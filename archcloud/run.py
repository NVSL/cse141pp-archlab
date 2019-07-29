#!/usr/bin/env python3

from Runner import build_submission, run_submission_locally, run_submission_remotely, Submission
import logging as log
import json
import platform
import argparse
import sys
import os
import subprocess

def main(argv):
    """
    This is the command line driver for Runner.py.  It should demonstrate everything you'll need to do with the library.

    The assumption is that the local directory has a clone of a lab repo.  Lab repos have `lab.py` in them.  The possible fields in a `lab.py` are described in `Runner.LabSpec`

    Currently, only `github.com/NVSL/CSE141pp-lab-dot-product` is setup with a correct `lab.py`, so test with that.

    You can then do:
    1. `./run.py --local` To run the lab in the local directory.
    2. `./run.py --pristine` To run the lab in a fresh clone of the lab's repo with the local input files (specified in lab.py) copied in.
    3. `./run.py --local --docker` to run the lab in docker container.
    4. `./run.py --json` to dump the json version of the lab submission and response to stdout.
    5. `./run.py --json --nop` to dump the json version of the lab submission stdout, but not run anything.
    6. `./run.py --json --nop | ./run.py --run-json --pristine --docker` generate the submission, consume it, and run it in a pristine clone in a docker container.

    The key data structures: `LabSpec`, `Submission`, `SubmissionResult` should all be fully convertible to and from dicts with `_fromdict()` and `_todict()` methods.
    """
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
    parser.add_argument('--docker-image', default="cse141pp/submission-runner:0.10", help="Docker image to use")
    parser.add_argument('--options', default=[], nargs="*", help="Options to control compilation and execution (e.g., 'CC=gcc-8' or 'OPT=-O4'")
    parser.add_argument('--list-options', action='store_true', default=False, help="List Available Options")
    parser.add_argument('--clean', action='store_true', default=False, help="Cleanup before running.  Only has an effect with '--local' execution.")
    parser.add_argument('--no-validate', action='store_false', default=True, dest='validate', help="Don't check for erroneously edited files.")

    args = parser.parse_args(argv)
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)


    if args.run_json:
        submission = Submission._fromdict(json.loads(sys.stdin.read()))
    else:
        submission = build_submission(args.directory, args.options)

    if args.validate:
        c = ['git', 'diff', '--exit-code', '--stat', '--', '.'] + list(map(lambda x : f'!{x}', submission.lab_spec.input_files))
        p = subprocess.Popen(c, cwd=args.directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            log.error("You have modified files that won't be submitted.  This is unwise.  '--no-validate' to ignore.")
            log.error(stdout.decode("utf-8"))
            sys.exit(1)

    if args.clean:
        subprocess.run(submission.lab_spec.clean_cmd, cwd=args.directory)

    if args.json:
        sys.stdout.write(json.dumps(submission._asdict(), sort_keys=True, indent=4) + "\n")

    log.debug("Submission: {}".format(json.dumps(submission._asdict(),  sort_keys=True, indent=4)))

    if not args.nop:
        if args.local:
            result = run_submission_locally(submission, root=args.directory, in_docker=args.docker, run_pristine=args.pristine)
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
                    with open(os.path.join(args.directory, i), "w") as t:
                        t.write(result.files[i])

    log.info("Finished")


if __name__ == '__main__':
    main(sys.argv[1:])