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

from .CloudServices import DS, PubSub
    
from .Runner import build_submission, run_submission_locally, Submission



from .GooglePubSub import get_publisher, ensure_topic, compute_topic_path
from .GooglePubSub import get_subscriber, ensure_subscription_exists, compute_subscription_path
import google.api_core

status = "IDLE"
keep_running = True
my_id=str(uuid())
    
class Heart(object):
    def __init__(self):
        self.topic = f"{os.environ['GOOGLE_RESOURCE_PREFIX']}-host-events"
        ensure_topic(self.topic)
        self.publisher = get_publisher()
        self.topic_path = compute_topic_path(self.topic)

    def send_beat(self):
        global status
        data = dict(id=my_id,
                    type="heartbeat",
                    node=platform.node(),
                    time=repr(datetime.datetime.utcnow()),
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
                log.debug(e)
            else:
                for r in r.received_messages:
                    log.info(f"Received command: {r.message.data.decode('utf8')}")
                    command = json.loads(r.message.data.decode('utf8'))
                    if command['command'] == "exit":
                        log.info("Got exit command")
                        global keep_running
                        keep_running = False
        
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
                                        docker_image=docker_image)
        
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

    heart = Heart()
    head = CommandListener()
    
    threading.Thread(target=Heart.beat,args=(heart,), daemon=True).start()
    threading.Thread(target=head.listen, daemon=True).start()

    while keep_running:
        time.sleep(1)
        try:
            job_id = pubsub.pull()

            if job_id is not None:
                #job_id = msg.message.attributes['job_id']

                job_data = ds.pull(
                    job_id=str(job_id)
                )
                if not job_data:
                    continue
                metadata = job_data['metadata']
                job_submission_json = job_data['job_submission_json']
                manifest = job_data['manifest']
                global status
                status = f"RUNNING {job_data['job_id'][:8]}"
                heart.send_beat()
                ds.update(
                    job_id,
                    status='STARTED',
                    started_utc=repr(datetime.datetime.utcnow()),
                    runner_host=platform.node()
                )


                output = run_job(
                    job_submission_json=job_submission_json,
                    in_docker=args.docker,
                    docker_image=args.docker_image
                )


                ds.update(
                    job_id,
                    status='COMPLETED',
                    output=output,
                    completed_utc=repr(datetime.datetime.utcnow())
                )
                status = "IDLE"
                heart.send_beat()
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
    status = "EXITED"
    heart.send_beat()
            
if __name__ == '__main__':
    main(sys.argv[1:])
