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

if "RUN_LOCAL_DS" in os.environ:
    from .LocalDataStore import LocalDataStore as DS
else:
    from .GoogleDataStore import GoogleDataStore as DS

if "RUN_LOCAL_PUBSUB" in os.environ:
    from .LocalPubSub import LocalPubSub as PubSub
else:
    from .GooglePubSub import GooglePubSub as PubSub

from .Runner import build_submission, run_submission_locally, Submission

def run_job(job_submission_json, submission_dir, pristine, in_docker, docker_image):

    log.info(f"Job json:{job_submission_json}")

    submission = Submission._fromdict(json.loads(job_submission_json))
    result = run_submission_locally(submission, root=submission_dir, run_pristine=pristine, run_in_docker=in_docker, docker_image=docker_image)
    output = json.dumps(result._asdict(), sort_keys=True, indent=4) + "\n"

    return output

def main(argv=None):
    parser = argparse.ArgumentParser(description='Server to run a lab.')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")
    parser.add_argument('--pristine', action='store_true', default=False, help="Clone a new repo")
    parser.add_argument('--docker', action='store_true', default=False, help="Run in a docker container.")
    parser.add_argument('--docker-image', default="stevenjswanson/cse141pp:latest", help="Docker image to use")
    parser.add_argument('--just-once', action='store_true', help="Just check the queue 1 time, then exit.")
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
        job_id = pubsub.pull()
        if job_id is not None:
            #job_id = msg.message.attributes['job_id']

            job_data = ds.pull(
                job_id=str(job_id)
            )

            metadata = job_data['metadata']
            job_submission_json = job_data['job_submission_json']
            manifest = job_data['manifest']

            output = ''

            ds.push(
                job_id=job_id,
                metadata=metadata, 
                job_submission_json=job_submission_json, 
                manifest=manifest,
                output=output,
                status='STARTED'
            )

            SUBMISSION_DIR = os.environ['SUBMISSION_DIR']
            output = run_job(
                job_submission_json=job_submission_json,
                submission_dir=SUBMISSION_DIR,
                in_docker=args.docker,
                docker_image=args.docker_image,
                pristine=args.pristine
            )


            ds.push(
                job_id=job_id,
                metadata=metadata, 
                job_submission_json=job_submission_json, 
                manifest=manifest,
                output=output,
                status='COMPLETED'
            )
            if args.just_once:
                sys.exit(0)
        else:
            log.info('No jobs in queue')
            time.sleep(1.0)

if __name__ == '__main__':
    main(sys.argv[1:])

import pytest

def test_server():
    pass
