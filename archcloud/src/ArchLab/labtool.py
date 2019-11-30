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
from .Packet import PacketCmd

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

def cmd_hosts(args):
    log.debug(f"Running hosts with {args}")
    from google.cloud.pubsub_v1.types import Duration
    from google.cloud.pubsub_v1.types import ExpirationPolicy
    from .GooglePubSub import ensure_subscription_exists, get_subscriber, compute_subscription_path, delete_subscription
    from uuid import uuid4 as uuid
    import datetime
    import google.api_core

    class Host(object):
        def __init__(self, name, status):
            self.name = name
            self.last_heart_beat = datetime.datetime.utcnow()
            self.status = status
            self.last_status_change = datetime.datetime.utcnow()
            
        def touch(self, when):
            self.last_heart_beat = max(when, self.last_heart_beat)

        def update_status(self, status):
            if self.status != status:
                self.last_status_change = datetime.datetime.utcnow()
                self. status = status

    os.system("clear")
    
    try: 
        sub_name = f"top-listener-{uuid()}"
        ensure_subscription_exists(topic=f"{os.environ['GOOGLE_RESOURCE_PREFIX']}-host-events",
                                   subscription=sub_name,
                                   message_retention_duration=Duration(seconds=30*60),
                                   expiration_policy=ExpirationPolicy(ttl=Duration(seconds=24*3600)))

        subscriber = get_subscriber()
        sub_path = compute_subscription_path(sub_name)
        hosts = dict()
        while True:
            try:
                r = subscriber.pull(sub_path, max_messages=5, timeout=3)
            except google.api_core.exceptions.DeadlineExceeded as e: 
                log.debug(e)
                pass
            else:
                for r in r.received_messages:
                    log.debug(f"Got {r.message.data.decode('utf8')}")
                    d = json.loads(r.message.data.decode("utf8"))
                    try:
                        if d['id'] not in hosts:
                            hosts[d['id']] = Host(name=d['node'],
                                                  status=d['status'])
                        else:
                            host = hosts[d['id']]
                            stamp = eval(d['time'])
                            if stamp > host.last_heart_beat:
                                host.touch(stamp)
                                host.update_status(d['status'])

                    except KeyError:
                        log.warning("Got strange message: {d}")

            rows = [["host", "MIA", "status", "for"]]
            for n, h in hosts.items():
                rows.append([h.name, datetime.datetime.utcnow()-h.last_heart_beat, h.status, datetime.datetime.utcnow()-h.last_status_change])
            os.system("clear")
            sys.stdout.write(columnize(rows, divider=" "))
            sys.stdout.flush()
    except KeyboardInterrupt:
        return 0
    finally:
        try:
            delete_subscription(sub_name)
        except:
            pass
            
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
        if 'submitted_utc' not in i or i['submitted_utc'] in ["", None]:
            continue
        if utcnow() - eval(i['submitted_utc']) > datetime.timedelta(seconds=int(os.environ['UNIVERSAL_TIMEOUT_SEC'])):
            continue
        live_jobs.add(i['job_id'])
    for i in ds.query(status="RUNNING"):
        live_jobs.add(i['job_id'])
        
    try: 
        while True:
            rows =[["id", "status", "wtime", "rtime", "tot. time", "runner", "lab" ]]
            for j in copy.copy(live_jobs):
                job=ds.pull(j)
                now = utcnow()
                if job['status'] == "COMPLETED":
                    try:
                        since_complete = now - eval(job['completed_utc'])
                        if since_complete > datetime.timedelta(seconds=int(os.environ['UNIVERSAL_TIMEOUT_SEC'])):
                            live_jobs.remove(job['job_id'])
                    except:
                        live_jobs.remove(job['job_id'])

                try:
                    #log.debug(f"Parsing {job['submitted_utc']}")
                    if job['status'] == "SUBMITTED":
                        waiting = now - eval(job['submitted_utc'])
                    else:
                        waiting = eval(job['started_utc']) - eval(job['submitted_utc'])
                except KeyError:
                    waiting = "k"
                except SyntaxError:
                    waiting = "s"

                try:
                    #log.debug(f"Parsing {job['started_utc']}")
                    if job['status'] == "STARTED":
                        running = now - eval(job['started_utc'])
                    elif job['status'] == "COMPLETED":
                        running = eval(job['completed_utc']) - eval(job['started_utc'])
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
                    
                rows.append([job['job_id'], job.get('status','.'), str(waiting), str(running), str(total), str(job['runner_host']), job['lab_name']])
                
            os.system("clear")
            sys.stdout.write(columnize(rows, divider=" "))
            sys.stdout.flush()
            m = ps.pull(timeout=1)
            if m:
                live_jobs.add(m)
            
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

    top_parser = subparsers.add_parser('top', help="Track jobs")
    top_parser.set_defaults(func=cmd_top)
    
    hosts_parser = subparsers.add_parser('hosts', help="Track hosts")
    hosts_parser.set_defaults(func=cmd_hosts)

    PacketCmd(subparsers)
    
    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)
    
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)

    return args.func(args)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

