#!/usr/bin/env python3
"""
runlab daemon

This program pulls CSE141 jobs from the pubsub queue and runs them. Then posts results to Google Datastore.

Usage: runlab.d

"""
import time
import sys
import json
import os
import logging as log
import platform
import argparse
import tempfile
import datetime
import threading
from uuid import uuid4 as uuid
import pytz

from .BlobStore import BlobStore
from .DataStore import DataStore
from .PubSub import Publisher, Subscriber


from .Runner import build_submission, run_submission_locally, Submission

import google.api_core

status = "IDLE"
keep_running = True
my_id=str(uuid())
heart = None
valid_status = ["IDLE",
                "RUNNING",
                "RELOAD_DOCKER",
                "RELOAD_PYTHON",
                "SHUTDOWN"]

def set_status(new_status, message=None):
    global status
    message = message if message else ""
    
    if new_status not in valid_status:
        raise Exception("Illegal status: {new_status}.  should be in {valid_status}")
    status = new_status + (f": {message}" if message else "")
    log.info(f"Setting status to '{status}'")
    with open(f"{os.environ['RUNLAB_STATUS_DIRECTORY']}/status", "w") as f:
        log.info(f"Writing status: '{new_status}'")
        f.write(new_status)
    heart.send_beat()
    
class Heart(object):
    def __init__(self, rate):
        self.publisher = Publisher(topic=os.environ['HOST_EVENTS_TOPIC'])
        try:
            with open(f"{os.environ['RUNLAB_STATUS_DIRECTORY']}/archlab_version", "r") as f:
                self.git_hash = f.read()
        except:
            self.git_hash = "unknown"

        self.heart_rate = rate
        
    def send_beat(self):
        global status
        global my_id
        log.debug(f"now = {repr(datetime.datetime.utcnow())}")
        data = dict(id=my_id,
                    type="heartbeat",
                    node=platform.node(),
                    time=repr(datetime.datetime.utcnow()),
                    sw_git_hash=self.git_hash,
                    docker_image=os.environ.get("THIS_DOCKER_IMAGE", "unknown"),
                    status=status)
                
        self.publisher.publish(json.dumps(data))
        log.info(f"Heartbeat sent: {data}")

    @classmethod
    def beat(cls, heart):
        while True:
            heart.send_beat()
            time.sleep(heart.heart_rate)

class CommandListener(object):
    def listen(self):
        with Subscriber(topic=os.environ['HOST_COMMAND_TOPIC']) as subscriber:
            while True:
                try:
                    messages = subscriber.pull(max_messages=5, timeout=2)
                except DeadlineExceeded: 
                    pass
                else:
                    global keep_running
                    for r in messages: 
                        log.info(f"Received command: {r}")
                        command = json.loads(r)
                        if command['command'] == "exit":
                            keep_running = False
                        if command['command'] == "reload-python":
                            keep_running = False
                            set_status("RELOAD_PYTHON")
                        if command['command'] == "reload-docker":
                            keep_running = False
                            set_status("RELOAD_DOCKER")
                        if command['command'] == "shutdown":
                            keep_running = False
                            set_status("SHUTDOWN")
                        elif command['command'] == "send-heartbeat":
                            global heart
                            heart.send_beat()

    
def run_job(job_submission_json, in_docker, docker_image):

    log.info(f"Job json:{job_submission_json}")

    submission = Submission._fromdict(json.loads(job_submission_json))
    with tempfile.TemporaryDirectory(dir="/tmp/") as directory:
        submission.run_directory = directory
        result = run_submission_locally(submission,
                                        run_pristine=True,
                                        run_in_docker=in_docker,
                                        docker_image=docker_image,
                                        # this timeout is conservative.  The lab timeout is enforced on the docker process
                                        timeout=int(os.environ['UNIVERSAL_TIMEOUT_SEC']))

    return result

def main(argv=None):

    parser = argparse.ArgumentParser(description='Server to run a lab.')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")
    parser.add_argument('--docker', action='store_true', default=False, help="Run in a docker container.")
    parser.add_argument('--docker-image', default=os.environ['DOCKER_RUNNER_IMAGE'], help="Docker image to use")
    parser.add_argument('--just-once', action='store_true', help="Just check the queue 1 time, then exit.")
    parser.add_argument('--id', default=None,  help="Use this as the server identifier.")
    parser.add_argument('--debug', action='store_true', help="exit on errors")
    parser.add_argument('--heart-rate', default=30, help="seconds between heart beats")
    
        
    if argv == None:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)

    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)
    log.debug(f"args={args}")

    log.info(f"Running in {os.environ['CLOUD_MODE']}")
    log.info(f"Running in {os.environ['IN_DEPLOYMENT']}")
    log.info(f"Running in {os.environ['GOOGLE_RESOURCE_PREFIX']}")
    log.info(f"I am {platform.node()}")
    
    global my_id
    if args.id != None:
        my_id = args.id

    ds = DataStore()
    blobstore = BlobStore(os.environ['JOBS_BUCKET'])
    subscriber = Subscriber(name=os.environ['PUBSUB_SUBSCRIPTION'],
                            topic=os.environ['PUBSUB_TOPIC'])

    global heart
    global keep_running

    heart = Heart(float(args.heart_rate))
    head = CommandListener()
    set_status("IDLE")    
    threading.Thread(target=Heart.beat,args=(heart,), daemon=True).start()
    threading.Thread(target=head.listen, daemon=True).start()
    while keep_running:
        try:
            job_id = subscriber.pull()

            if len(job_id):
                job_id = job_id[0]

                job_data = ds.pull(
                    job_id=str(job_id)
                )
                if not job_data:
                    continue
                if job_data['status'] != "SUBMITTED":
                    continue
                
                job_submission_json = job_data['job_submission_json']
                set_status("RUNNING", job_data['job_id'][:8])

                ds.update(
                    job_id,
                    status='STARTED',
                    started_utc=datetime.datetime.now(pytz.utc),
                    runner_host=platform.node()
                )

                result = run_job(
                    job_submission_json=job_submission_json,
                    in_docker=args.docker,
                    docker_image=args.docker_image
                )

                # pull the job data again to make sure it wasn't
                # canceled or completed by someone else.  If it timed
                # out, we should leave it incomplete, since that's
                # what effectively happened.
                job_data = ds.pull(job_id=str(job_id))
                if job_data['status'] == "STARTED":
                    try:
                        blobstore.write_file(job_id, json.dumps(result._asdict(), sort_keys=True, indent=4))
                        ds.update(
                            job_id,
                            status='COMPLETED',
                            submission_status=result.status,
                            submission_status_reasons=result.status_reasons,
                            completed_utc=datetime.datetime.now(pytz.utc)
                        )
                    except Exception as e:
                        # if something goes wrong, we still need to notify
                        # the client, so try this simpler request.
                        #
                        # We probably don't adequately handle "ERROR" as a status.
                        log.error(f"Updating status of {job_id} failed.  Job failed:{e}")
                        ds.update(job_id,
                                  status='ERROR',
                                  status_reasons=["Couldn't update the status of the job. Something is wrong with the cloud.  This is not a problem with your code."])
                else:
                    log.error(f"Found that job I was running completed without me")
                        
                set_status("IDLE")

                if args.just_once:
                    sys.exit(0)
            else:
                log.info('No jobs in queue')
                time.sleep(1.0)
        except Exception as e:
            if args.debug:
                raise
            log.error(f"Uncaught exception: {e}.")
            log.error("Sleeping for 1 second and trying again")
            time.sleep(1.0)

            
if __name__ == '__main__':
    main(sys.argv[1:])
