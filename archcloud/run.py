#!/usr/bin/env python3

from Runner import build_submission, run_submission_locally, run_submission_remotely, Submission
import logging as log
import json
import platform
import argparse
import sys

def main(argv):
    parser = argparse.ArgumentParser(description='Run a lab.')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")
    parser.add_argument('--pristine', action='store_true', default=False, help="Run job locally")
    parser.add_argument('--remote', default="http://localhost:5000", help="Run remotely on this host")
    parser.add_argument('--docker', action='store_true', default=False, help="Run in a docker container.")
    parser.add_argument('--local', action='store_true', default=True, help="Run locally in this directory.")
    parser.add_argument('--nop', action='store_true', default=False, help="Don't actually running anything.")
    parser.add_argument('--json', action='store_true', default=False, help="Dump json version of submission and response.")
    parser.add_argument('--directory', default=".", help="Directory to submit")
    parser.add_argument('--run-json', action='store_true', default=False, help="Read json submission spec from stdin")
#    parser.add_argument('--repo', help="git repo")
    args = parser.parse_args(argv)
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)

    if args.run_json:
        submission = Submission._fromdict(json.loads(sys.stdin.read()))
    else:
        submission = build_submission(args.directory)

    if args.json:
        sys.stdout.write(json.dumps(submission._asdict(), sort_keys=True, indent=4) + "\n")

    log.debug("Submission: {}".format(json.dumps(submission._asdict(),  sort_keys=True, indent=4)))

    if not args.nop:
        if args.local:
            result = run_submission_locally(submission, in_docker=args.docker, run_pristine=args.pristine)
        else:
            result = run_submission_remotely(submission, args.remote, "5000")

        if args.json:
            sys.stdout.write(json.dumps(result._asdict(), sort_keys=True, indent=4) + "\n")

        for i in submission.lab_spec.output_files:
            if i in result.files:
                log.debug("========================= {} ===========================".format(i))
                log.debug(result.files[i])
                if i == "STDERR":
                    sys.stderr.write(result.files[i])
                elif i == "STDOUT":
                    sys.stdout.write(result.files[i])
                else:
                    with open(i, "w") as t:
                        t.write(result.files[i])

    log.info("Finished")


if __name__ == '__main__':
    main(sys.argv[1:])