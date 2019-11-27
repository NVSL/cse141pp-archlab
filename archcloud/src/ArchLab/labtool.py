#!/usr/bin/env python3

from .Runner import build_submission, run_submission_locally, run_submission_remotely, Submission, RunnerException, SubmissionResult
import logging as log
import json
import platform
import argparse
import sys
import os
import subprocess
import base64
from  .CloudServices import DS, PubSub
import copy

def columnize(data, divider="|", headers=1):
    r = ""
    column_count = max(map(len, data))
    rows = [x + ([""] * (column_count - len(x))) for x in data]
    widths = [max(list(map(lambda x:len(str(x)), col))) for col in zip(*rows)]
    div = "{}".format(divider)
    for i, row in enumerate(rows):
        if headers is not None and headers == i:
            r += divider.join(map(lambda x: "-" * (x), widths )) + "\n"
        r += div.join((str(val).ljust(width) for val, width in zip(row, widths))) + "\n"
    return r

def cmd_ls(args):
    log.debug(f"Running ls with {args}")
    ds = DS()
    jobs = ds.query()
    sys.stdout.write(f"{len(jobs)} jobs:\n")
    for j in jobs:
        sys.stdout.write(f"{j['job_id']}: {j['metadata']} \n")

def cmd_top(args):
    from google.cloud.pubsub_v1.types import Duration
    from google.cloud.pubsub_v1.types import ExpirationPolicy
    import datetime

    utcnow = datetime.datetime.utcnow
    
    log.debug(f"Running top with {args}")

    ds = DS()

    ps = PubSub(private_subscription=True,
                subscription_base="top",
                retain_acked_messages=True,
                message_retention_duration=Duration(seconds=30*60),
                expiration_policy=ExpirationPolicy(ttl=Duration(seconds=24*3600)))

    live_jobs=set()
    for i in ds.query(status="SUBMITTED"):
        live_jobs.add(i['job_id'])
    for i in ds.query(status="RUNNING"):
        live_jobs.add(i['job_id'])
        
    while True:
        os.system("clear")
        for j in copy.copy(live_jobs):
            job=ds.pull(j)
            if job['status'] == "COMPLETED":
                live_jobs.remove(job['job_id'])
            sys.stdout.write(f"{job['job_id']}\t{job['status']}\n")
            sys.stdout.flush()
        m = ps.pull(timeout=1)
        if not m:
            continue
        sys.stdout.write(f"Got message {m}")
        sys.stdout.flush()
        live_jobs.add(m)
        
def main(argv=None):
    """
    This is backend lab management tool.
    """
    parser = argparse.ArgumentParser(description='Run a lab.')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")

    subparsers = parser.add_subparsers(help='sub-command help')

    ls_parser = subparsers.add_parser('ls', help="List lab jobs")
    ls_parser.set_defaults(func=cmd_ls)

    top_parser = subparsers.add_parser('top', help="Track jobs")
    top_parser.set_defaults(func=cmd_top)
    
    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)
    
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)

    return args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])

