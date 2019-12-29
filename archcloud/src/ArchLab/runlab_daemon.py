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
import traceback
from uuid import uuid4 as uuid
import pytz

from .BlobStore import BlobStore
from .DataStore import DataStore
from .PubSub import Publisher, Subscriber


from .Runner import build_submission, run_submission_locally, Submission, ArchlabError, UserError

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


    submission = Submission._fromdict(json.loads(job_submission_json))
    with tempfile.TemporaryDirectory(dir="/tmp/") as directory:
        submission.run_directory = directory
        result = run_submission_locally(submission,
                                        write_outputs=False,
                                        user_directory_override=submission.user_directory,
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
    job_id = None
    job_data = dict()
    while keep_running:
        result = None
        try:
            try:
                job_id = subscriber.pull()
                if job_id == "junk":
                    continue
                if len(job_id) == 0:
                    log.info('No jobs in queue')
                    time.sleep(1)
                    continue

                job_id = job_id[0]

                job_data = ds.pull(
                    job_id=job_id
                )
                if not job_data: # job missing?
                    continue
                if job_data['status'] != "SUBMITTED":  # Someone else grabbed it.
                    continue

                job_submission_json = blobstore.read_file(job_id)
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
                job_data = ds.pull(job_id=job_id)
                if job_data['status'] != "STARTED":
                    log.error(f"Found that job I was running completed without me")
                    continue

                blobstore.write_file(f"{job_id}-result",
                                     json.dumps(result._asdict(), sort_keys=True, indent=4))

                if job_data['username']:
                    username = f"{job_data['username'].split('@')[0]}-"
                else:
                    username = ""

                to_zone = pytz.timezone('America/Los_Angeles')
                local_time = job_data['submitted_utc'].astimezone(to_zone).strftime('%Y-%m-%d-%H-%M-%S')
                download_name=f"{username}submitted-at-{local_time}.zip"
                zip_name = f"{job_id}.zip"
                archive = blobstore.write_file(zip_name,
                                               result.build_file_zip_archive(),
                                               content_disposition=f"Attachment; filename={download_name}",
                                               owner=job_data['username'],
                                               content_type="application/zip")
                ds.update(
                    job_id,
                    status='COMPLETED',
                    submission_status=result.status,
                    submission_status_reasons=result.status_reasons,
                    completed_utc=datetime.datetime.now(pytz.utc),
                    zip_archive=archive
                )
            except (ArchlabError, UserError) as e:
                job_data = ds.pull(job_id=job_id)
                ds.update(
                    job_id,
                    status='ERROR',
                    status_reasons=job_data['status_reasons'] +
                    [f"{traceback.format_exc()}\n{repr(e)}"] +
                    [f"An error occurred.  This is probably {'not ' if isinstance(e, ArchlabError) else ''}a problem with your code or configuration."],
                    completed_utc=datetime.datetime.now(pytz.utc),
                )
                if args.debug:
                    raise
            except Exception as e:
                log.error(f"Something went wrong and {job_id} failed.  Job failed:{e}")
                job_id and ds.update(job_id,
                                     status='ERROR',
                                     status_reasons=job_data.get('status_reasons', []) +
                                     [f"{traceback.format_exc()}\n{repr(e)}"] +
                                     ["An unexected error occurred.  This is probably not a problem with your code."],
                                     completed_utc=datetime.datetime.now(pytz.utc),
                )
                if args.debug:
                    raise
            finally:
                set_status("IDLE")
                if args.just_once:
                    sys.exit(0)
        # This is to catch exceptions that arise during the processing
        # of other exceptions, so the daemon doesn't crash.  The
        # likely cause is some problem with the cloud services.  If
        # they aren't working, there's not much we can do, so we just
        # listen pause for a bit and look for a new request.
        except Exception as e: 
            log.error(f"Uncaught exception: {e}.")
            log.error("Sleeping for 10 second and trying again")
            if args.debug:
                raise
            time.sleep(10.0)
            

            
if __name__ == '__main__':
    main(sys.argv[1:])
