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
from .Columnize import columnize
from .SubCommand import SubCommand
from .hosttool import send_command_to_hosts
import pytz

def cmd_ls(args):
    log.debug(f"Running ls with {args}")
    ds = DS()
    jobs = ds.query()
    sys.stdout.write(f"{len(jobs)} jobs:\n")
    for j in jobs:
        sys.stdout.write(f"{j['job_id']}: {j['metadata']} \n")

class Top(SubCommand):
    def __init__(self, parent):
        super(Top, self).__init__(parent,
                                  name="top",
                                  help="Track lab submission status")
        self.parser.add_argument('--once', action='store_true', default=False, help="Just collect stats once and exit")

    def run(self, args):
        from google.cloud.pubsub_v1.types import Duration
        from google.cloud.pubsub_v1.types import ExpirationPolicy
        import datetime

        log.debug(f"Running top with {args}")

        ds = DS()

        ps = PubSub(private_subscription=True,
                    subscription_base="top",
                    retain_acked_messages=True,
                    message_retention_duration=Duration(seconds=30*60),
                    expiration_policy=ExpirationPolicy(ttl=Duration(seconds=24*3600)))

        live_jobs=set()
        for i in ds.query(status="SUBMITTED"):
            if 'submitted_utc' not in i or i['submitted_utc'] in ["", None]:
                continue
            if datetime.datetime.now(pytz.utc) - i['submitted_utc'] > datetime.timedelta(seconds=int(os.environ['UNIVERSAL_TIMEOUT_SEC'])):
                continue
            live_jobs.add(i['job_id'])
        for i in ds.query(status="RUNNING"):
            live_jobs.add(i['job_id'])

        try: 
            while True:
                rows =[["id", "status", "wtime", "rtime", "tot. time", "runner", "lab" ]]
                for j in copy.copy(live_jobs):
                    job = ds.pull(j)
                    now = datetime.datetime.now(pytz.utc)
                    if job['status'] == "COMPLETED":
                        try:
                            since_complete = now - job['completed_utc']
                            if since_complete > datetime.timedelta(seconds=int(os.environ['UNIVERSAL_TIMEOUT_SEC'])):
                                live_jobs.remove(job['job_id'])
                        except:
                            live_jobs.remove(job['job_id'])

                    try:
                        #log.debug(f"Parsing {job['submitted_utc']}")
                        if job['status'] == "SUBMITTED":
                            waiting = now - job['submitted_utc']
                        else:
                            waiting = job['started_utc'] - job['submitted_utc']
                    except KeyError:
                        waiting = "k"
                    except SyntaxError:
                        waiting = "s"

                    try:
                        #log.debug(f"Parsing {job['started_utc']}")
                        if job['status'] == "STARTED":
                            running = now - job['started_utc']
                        elif job['status'] == "COMPLETED":
                            running = job['completed_utc'] - job['started_utc']
                        else:
                            running = "."
                    except KeyError as e:
                        log.error(e)
                        running = "k"
                    except SyntaxError as e:
                        log.error(e)
                        running = "s"

                    try:
                        total = running + waiting
                    except:
                        total = "?"

                    submission = Submission._fromdict(json.loads(job['job_submission_json']))
                    rows.append([job['job_id'][:8], job.get('status','.'), str(waiting), str(running), str(total), str(job['runner_host']), submission.lab_spec.short_name])

                os.system("clear")
                sys.stdout.write(columnize(rows, divider=" "))
                sys.stdout.flush()
                m = ps.pull(timeout=1)
                if m:
                    live_jobs.add(m)
                if args.once:
                    break
        except KeyboardInterrupt:
            return 0
        finally:
            ps.tear_down()

def main(argv=None):
    """
    This is backend lab management tool.
    """
    parser = argparse.ArgumentParser(description='Run a lab.')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")

    subparsers = parser.add_subparsers(help='sub-command help')

    ls_parser = subparsers.add_parser('ls', help="List jobs")
    ls_parser.set_defaults(func=cmd_ls)

    Top(subparsers)

    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)

    if not "func" in args:
        parser.print_help()
        sys.exit(1)
        
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)

    return args.func(args)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

