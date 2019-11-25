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
    
def main(argv=None):
    """
    This is backend lab management tool.
    """
    parser = argparse.ArgumentParser(description='Run a lab.')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")

    subparsers = parser.add_subparsers(help='sub-command help')
    ls_parser = subparsers.add_parser('ls', help="List lab jobs")
    ls_parser.set_defaults(func=cmd_ls)
    
    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)
    
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)

    return args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
