#!/usr/bin/env python3

from .Runner import build_submission, run_submission_locally, run_submission_remotely, Submission, SubmissionResult, MalformedObject
import logging as log
import json
import platform
import argparse
import sys
import os
import subprocess
import base64
from  .DataStore import DataStore
from  .BlobStore import BlobStore
from  .PubSub import Subscriber
import math

import copy
from .Columnize import columnize, format_time_delta, format_time_short, format_time_excel
from .SubCommand import SubCommand
from .hosttool import send_command_to_hosts
import pytz

class Report(SubCommand):
    def __init__(self, parent):
        super(Report, self).__init__(parent,
                                   name="report",
                                   help="Generate reports")
        self.parser.add_argument("--count", default=None, help="How many to list")

    def subs_per_student_histo(self, jobs):
        
        counts = {}
        for j in jobs:
            counts[j['username']] = counts.setdefault(j['username'], 0) + 1
            #print(j['username'])

        self.print_histogram(counts,1)
              
    def subs_per_hour_histo(self, jobs, bucket_size=10):
        
        counts = {}
        for j in jobs:
            counts[j['submitted_utc'].hour] = counts.setdefault(j['username'], 0) + 1
            #print(j['username'])

        self.print_histogram(counts, bucket_size)
              
    def print_histogram(self, counts, bucket_size):
        min_count = int(math.floor(min(counts.values())/bucket_size)*bucket_size)
        max_count = int(math.ceil(max(counts.values())/bucket_size)*bucket_size)

        bucket_count = int((max_count - min_count)/bucket_size)

        buckets = [0]*bucket_count
        #print(counts)
        for lb in range(min_count, min_count + bucket_count *bucket_size, bucket_size):
            for k,v in counts.items():
                if v > lb and v <= lb + bucket_size:
                    buckets[int(lb/bucket_size)] += 1

        max_count = max(buckets)
        for lb in range(min_count, min_count + bucket_count *bucket_size, bucket_size):
            print(f"{lb:4} {'#' * int((buckets[int(lb/bucket_size)]/max_count)*70)}")
        
    def run(self, args):
        
        import csv
        import datetime
        
        ds = DataStore()
        jobs = ds.query(limit=None if not args.count else int(args.count))
        
        #self.subs_per_student_histo(jobs)
        self.subs_per_hour_histo(jobs)
        
        
class List(SubCommand):
    def __init__(self, parent):
        super(List, self).__init__(parent,
                                   name="ls",
                                   help="List all jobs")
        self.parser.add_argument("--count", default=None, help="How many to list")
        self.parser.add_argument("--csv", nargs="?", help="List as CSV")
        
    def run(self, args):
        
        import csv
        import datetime
        
        ds = DataStore()
        jobs = ds.query_iterator(limit=None if not args.count else str(args.count))
#<Entity('ArchLabJob', '00049b44-381b-4c33-89c4-fae781fad3fc') {'completed_utc': datetime.datetime(2020, 1, 24, 2, 34, 44, 411792, tzinfo=<UTC>), 'submission_status_reasons': [], 'started_utc': datetime.datetime(2020, 1, 24, 2, 34, 15, 976252, tzinfo=<UTC>), 'job_id': '00049b44-381b-4c33-89c4-fae781fad3fc', 'zip_archive': 'https://storage.cloud.google.com/cse141l-jobs/00049b44-381b-4c33-89c4-fae781fad3fc.zip', 'username': 'nonguyen@ucsd.edu', 'status': 'COMPLETED', 'status_reasons': [], 'runner_host': 'CSE141L-1', 'submitted_host': '8f6038c5b664', 'submission_status': 'success', 'submitted_utc': datetime.datetime(2020, 1, 24, 2, 34, 13, 188345, tzinfo=<UTC>)}>

        if args.csv:
            rows = []
            for i in jobs:
                for k,v in i.items():
                    if isinstance(v, datetime.datetime):
                        i[k] = format_time_excel(i[k])
                i.pop("submission_status_reasons", None)        
                i.pop("status_reasons", None)        
                rows.append(dict(i))

            with open(args.csv, "w") as out:
                writer = csv.DictWriter(out,fieldnames=rows[0].keys())
                writer.writeheader()
                for r in rows:
                    writer.writerow(r)
        else:
            for i in jobs:
                sys.stderr.write(f"{str(i)}\n")
        
    
class Download(SubCommand):
    def __init__(self, parent):
        super(Download, self).__init__(parent,
                                  name="fetch-data",
                                  help="Download information about a job")
        self.parser.add_argument("id", nargs='+', help="prefix of job id")

    def run(self, args):
        import json
        from .Runner import cd
        import re
        blobstore = BlobStore(os.environ['JOBS_BUCKET'])
        ds = DataStore()
        for id in args.id:
            names = blobstore.get_files_by_prefix(id)
            if len(names) == 0:
                sys.stderr.write(f"No such job: {id}")
                sys.exit(1)
            if len(names) > 3:
                sys.stderr.write(f"Not a unique prefix: {id}")
                sys.exit(1)

            m = re.search("^(\w+-\w+-\w+-\w+-\w+)", names[0])
            prefix = m.group(1)
            log.debug(f"Prefix = {prefix}\n")
            log.debug(f"Found these blobs: {names}")
            job_data = ds.get_job(prefix)

            
            os.makedirs(prefix, exist_ok=True)
            for i in names:
                d = blobstore.read_file(i)
                mode = "w" if isinstance(d, str) else "wb"
                    
                with open(os.path.join(prefix, i), mode) as f:
                    f.write(d)
                if "-result" in i:
                    files_path = os.path.join(prefix, "files")
                    os.makedirs(files_path, exist_ok=True)
                    result = SubmissionResult._fromdict(json.loads(d))
                    result.write_outputs(directory=files_path)
                    result.submission.write_inputs(directory=files_path)

                    result.files = "<hidden>"
                    result.submission.files = "<hidden>"
                    result.results ="<hidden>"
                    sys.stdout.write(json.dumps(result._asdict(), indent=4) + "\n")
                    
            with open(os.path.join(prefix, "job_data"), "w") as f:
                f.write(str(job_data))
                sys.stdout.write(str(job_data) + "\n")


            

            

class Cleanup(SubCommand):
    def __init__(self, parent):
        super(Cleanup, self).__init__(parent,
                                  name="cleanup",
                                  help="Cleanup stale jobs")
        self.parser.add_argument('-n', '--dry-run', action='store_true', default=False, help="Don't actually do anything")

    def run(self, args):
        import datetime
        ds = DataStore()
        for i in ds.query(status="SUBMITTED") + ds.query(status="STARTED"):
            now = datetime.datetime.now(pytz.utc)
            if now - i['submitted_utc'] > datetime.timedelta(seconds=int(os.environ['UNIVERSAL_TIMEOUT_SEC'])):
                log.info(f"Canceling {i['job_id']}")
                if not args.dry_run:
                    ds.update(i['job_id'],
                              status = "COMPLETED",
                              status_reasons=["Manually cleaned up"],
                              completed_utc=datetime.datetime.now(pytz.utc),
                              submission_status = SubmissionResult.TIMEOUT,
                    )
                    
class Top(SubCommand):
    def __init__(self, parent):
        super(Top, self).__init__(parent,
                                  name="top",
                                  help="Track lab submission status")
        self.parser.add_argument('--once', action='store_true', default=False, help="Just collect stats once and exit")
        self.parser.add_argument('--max-rows', default="50", help="How many to display")
        self.parser.add_argument('--window', default=30, help="Time window to compute stats (in minutes) (default = 30)")

    def run(self, args):
        from google.cloud.pubsub_v1.types import Duration
        from google.cloud.pubsub_v1.types import ExpirationPolicy
        import datetime

        log.debug(f"Running top with {args}")

        args.window = int(args.window)*60
        
        ds = DataStore()

        with Subscriber(topic=os.environ['PUBSUB_TOPIC']) as subscriber:


            live_jobs=set()

            for i in ds.query(status="SUBMITTED"):
                log.debug(f"Found submitted job: {i['job_id']}")
                live_jobs.add(i['job_id'])
            for i in ds.query(status="RUNNING"):
                log.debug(f"Found running job: {i['job_id']}")
                live_jobs.add(i['job_id'])
            for i in ds.get_recently_completed_jobs(args.window):
                log.debug(f"Found completed job: {i['job_id']}")
                live_jobs.add(i['job_id'])

            try: 
                while True:
                    rows =[]
                    header =[["id", "jstat", "sstat", "wtime","rtime", "tot. time", "finished", "runner",  "user" ]]
                    users = set()
        
                    for j in copy.copy(live_jobs):
                        job = ds.pull(j)
                        if not job:
                            continue
                        now = datetime.datetime.now(pytz.utc)
                        if job['status'] == "COMPLETED":
                            try:
                                since_complete = now - job['completed_utc']
                                if since_complete > datetime.timedelta(seconds=args.window):
                                    live_jobs.remove(job['job_id'])
                            except Exception as e:
                                log.error("Error checking status of job {j}: {e}")
                                live_jobs.remove(job['job_id'])

                        try:

                            if job['status'] == "SUBMITTED" or not job['started_utc']:
                                waiting = now - job['submitted_utc']
                            else:
                                waiting = job['started_utc'] - job['submitted_utc']
                        except KeyError:
                            waiting = "k"
                        except SyntaxError:
                            waiting = "s"

                        try:

                            if job['status'] == "STARTED":
                                running = now - job['started_utc']
                            elif job['status'] == "COMPLETED" and job['started_utc']:
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
                            total = waiting

                            
                        #try:
                        #    submission = Submission._fromdict(json.loads(job['job_submission_json']))
                        #except MalformedObject:
                        #continue
                        users.add(job.get('username',""))
                        
                        rows.append([job['job_id'][:8],
                                     job.get('status','.'),
                                     job.get('submission_status', "."),
                                     format_time_delta(waiting),
                                     format_time_delta(running),
                                     format_time_delta(total),
                                     format_time_short(job['started_utc']),
                                     str(job['runner_host']),
                                     job.get('username', "")])

                    
                    recent_jobs = ds.get_recently_completed_jobs(seconds_ago=args.window)
                    latency_sum = datetime.timedelta()
                    exec_time_sum = datetime.timedelta()
                    timeout = datetime.timedelta(seconds = int(os.environ['UNIVERSAL_TIMEOUT_SEC']))
                    overdue = 0

                    for j in recent_jobs:
                        try:
                            d = j['completed_utc'] - j['submitted_utc']
                        except TypeError as e:
                            log.error(f"j['completed_utc'] = {j['completed_utc']}")
                            log.error(f"j['submitted_utc'] = {j['submitted_utc']}")
                            raise e
                        if d > timeout:
                            overdue += 1
                        latency_sum += d

                        try:
                            exec_time_sum += j['completed_utc'] - j['started_utc']
                        except TypeError:
                            pass
                            
                    if not args.verbose:
                        os.system("clear")
                    sys.stdout.write(f"Namespace: {os.environ['GOOGLE_RESOURCE_PREFIX']}; {os.environ['IN_DEPLOYMENT']} in {os.environ['CLOUD_MODE']}; DOCKER: {os.environ.get('THIS_DOCKER_IMAGE', 'unknown')}\n")
                    sys.stdout.write(f"In the last {args.window}s: {len(recent_jobs)} job; {len(users)} students\n")
                    sys.stdout.write(f"Average latency: Total: {len(recent_jobs) and latency_sum/len(recent_jobs)}; Execute {len(recent_jobs) and exec_time_sum/len(recent_jobs)}.\n")
                    if len(recent_jobs):
                        arrival_period = float(args.window)/float(len(recent_jobs))
                        log.debug(f"arrival_period={arrival_period}")
                        completion_period = float(exec_time_sum.seconds)/float(len(recent_jobs))
                        log.debug(f"completion_period={completion_period}")
                        servers_needed = math.ceil(completion_period/arrival_period)
                    else:
                        servers_needed = 1
                        
                    sys.stdout.write(f"We should have this many servers running: {servers_needed}\n")  
                    sys.stdout.write(f"Gradescope timeout %: {len(recent_jobs) and float(overdue)/len(recent_jobs)*100}\n")
                    sys.stdout.write(f"Current Time: {format_time_short(datetime.datetime.utcnow())}\n")
                    rows.sort(key=lambda x: (x[1], x[6]), reverse=True)
                    sys.stdout.write(columnize((header + rows)[:int(args.max_rows)], divider=" "))
                    sys.stdout.flush()

                    for m in subscriber.pull(timeout=5,max_messages=100):
                        live_jobs.add(m)

                    if args.once:
                        break
            except KeyboardInterrupt:
                return 0


def main(argv=None):
    """
    This is backend lab management tool.
    """
    parser = argparse.ArgumentParser(description='Run a lab.')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")

    subparsers = parser.add_subparsers(help='sub-command help')

    Top(subparsers)
    Cleanup(subparsers)
    Download(subparsers)
    List(subparsers)
    Report(subparsers)

    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)

    if not "func" in args:
        parser.print_help()
        sys.exit(1)
        
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.WARN)

    return args.func(args)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

