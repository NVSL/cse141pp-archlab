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

from .CloudServices import DS, PubSub, BlobStore
    
from .Runner import build_submission, run_submission_locally, Submission
 

from .GooglePubSub import get_publisher, ensure_topic, compute_topic_path
from .GooglePubSub import get_subscriber, ensure_subscription_exists, compute_subscription_path
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
    def __init__(self):
        self.topic = f"{os.environ['GOOGLE_RESOURCE_PREFIX']}-host-events"
        ensure_topic(self.topic)
        self.publisher = get_publisher()
        self.topic_path = compute_topic_path(self.topic)
        try:
            with open(f"{os.environ['RUNLAB_STATUS_DIRECTORY']}/archlab_version", "r") as f:
                self.git_hash = f.read()
        except:
            self.git_hash = "unknown"
        
    def send_beat(self):
        global status
        data = dict(id=my_id,
                    type="heartbeat",
                    node=platform.node(),
                    time=repr(datetime.datetime.now(pytz.utc)),
                    sw_git_hash=self.git_hash,
                    status=status)
        
        self.publisher.publish(self.topic_path,
                          json.dumps(data).encode('utf8'))
        log.info(f"Heartbeat sent: {data}")

    @classmethod
    def beat(cls, heart):
        while True:
            heart.send_beat()
            time.sleep(30)

class CommandListener(object):
    def __init__(self):
        topic = f"{os.environ['GOOGLE_RESOURCE_PREFIX']}-host-commands"        
        ensure_topic(topic)
        self.subscriber = get_subscriber()
        self.subscription_name = f"host-command-listener-{my_id}"
        self.subscription_path = compute_subscription_path(self.subscription_name)
        ensure_subscription_exists(topic, self.subscription_name)

    def listen(self):
        log.info(f"Heading listening on {self.subscription_path}")
        while True:
            try:
                r = self.subscriber.pull(self.subscription_path, max_messages=5, timeout=10)
            except google.api_core.exceptions.DeadlineExceeded as e: 
                pass
            else:
                global keep_running
                for r in r.received_messages:
                    log.info(f"Received command: {r.message.data.decode('utf8')}")
                    command = json.loads(r.message.data.decode('utf8'))
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
                    self.subscriber.acknowledge(self.subscription_path, [r.ack_id])
                        
    def teardown(self):
        try:
            delete_subscription(self.subscription_path)
        except:
            pass

    
def run_job(job_submission_json, in_docker, docker_image):

    log.info(f"Job json:{job_submission_json}")

    submission = Submission._fromdict(json.loads(job_submission_json))
    with tempfile.TemporaryDirectory(dir="/tmp/") as directory:
        result = run_submission_locally(submission,
                                        root=directory,
                                        run_pristine=True,
                                        run_in_docker=in_docker,
                                        docker_image=docker_image,
                                        # this timeout is conservative.  The lab timeout is enforced on the docker process
                                        timeout=int(os.environ['UNIVERSAL_TIMEOUT_SEC']))
        
    output = json.dumps(result._asdict(), sort_keys=True, indent=4) + "\n"

    return output

def main(argv=None):
    parser = argparse.ArgumentParser(description='Server to run a lab.')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")
    parser.add_argument('--docker', action='store_true', default=False, help="Run in a docker container.")
    parser.add_argument('--docker-image', default=os.environ['DOCKER_RUNNER_IMAGE'], help="Docker image to use")
    parser.add_argument('--just-once', action='store_true', help="Just check the queue 1 time, then exit.")
    parser.add_argument('--debug', action='store_true', help="exit on errors")
    if argv == None:
        argv = sys.argv[1:]
    args = parser.parse_args(argv)

    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)
    log.debug(f"args={args}")

    ds = DS()
    pubsub = PubSub()
    blobstore = BlobStore("jobs")
    
    global heart
    heart = Heart()
    head = CommandListener()
    set_status("IDLE")    
    threading.Thread(target=Heart.beat,args=(heart,), daemon=True).start()
    threading.Thread(target=head.listen, daemon=True).start()
    global keep_running
    while keep_running:
        time.sleep(1)
        try:
            job_id = pubsub.pull()[0]

            if job_id is not None:
                #job_id = msg.message.attributes['job_id']

                job_data = ds.pull(
                    job_id=str(job_id)
                )
                if not job_data:
                    continue
                if job_data['status'] != "SUBMITTED":
                    continue
                
                metadata = job_data['metadata']
                job_submission_json = job_data['job_submission_json']
                manifest = job_data['manifest']
                set_status("RUNNING", job_data['job_id'][:8])

                ds.update(
                    job_id,
                    status='STARTED',
                    started_utc=datetime.datetime.now(pytz.utc),
                    runner_host=platform.node()
                )


                output = run_job(
                    job_submission_json=job_submission_json,
                    in_docker=args.docker,
                    docker_image=args.docker_image
                )

                try:
                    blobstore.write_file(job_id, output)
                    ds.update(
                        job_id,
                        status='COMPLETED',
                        completed_utc=datetime.datetime.now(pytz.utc)
                    )
                except Exception as e:
                    # if something goes wrong, we still need to notify
                    # the client, so try this simpler request.  The
                    # main culprit seems to be values being too large.
                    log.error(f"Updating status of {job_id} failed.  Job failed:{e}")
                    ds.update(job_id,
                              status='ERROR')
                    
                set_status("IDLE")

                if args.just_once:
                    sys.exit(0)
            else:
                log.info('No jobs in queue')
                time.sleep(1.0)
        except Exception as e:
            if args.debug:
                raise
            log.error(f"Uncaught exception: {e}.\nSleeping for 1 second and trying again")
            time.sleep(1.0)

            
if __name__ == '__main__':
    main(sys.argv[1:])
