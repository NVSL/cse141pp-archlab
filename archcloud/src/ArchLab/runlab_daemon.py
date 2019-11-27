#!/usr/bin/env python3
"""
packet_server.

This program pulls CSE141 jobs from the pubsub queue and runs them. Then posts results to Google Datastore.

Usage: packet_server 

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

from .CloudServices import DS, PubSub
    
from .Runner import build_submission, run_submission_locally, Submission

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
    log.debug(f"argv={argv}")
    log.debug(f"args={args}")
    ds = DS()
    pubsub = PubSub()

    while True:
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
