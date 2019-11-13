#!/usr/bin/env python3

from Runner import build_submission, run_submission_locally, Submission, RunnerException
import logging as log
import json
import platform
import argparse
import sys
import os
import subprocess

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

def main(argv):
    """
    This is the command line driver for Runner.py.  It should demonstrate everything you'll need to do with the library.

    The assumption is that the local directory has a clone of a lab repo.  Lab repos have `lab.py` in them.  The possible fields in a `lab.py` are described in `Runner.LabSpec`

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
    parser.add_argument('--pristine', action='store_true', default=False, help="Clone a new repo")
    parser.add_argument('--docker', action='store_true', default=False, help="Run in a docker container.")
    parser.add_argument('--docker-image', default="stevenjswanson/cse141pp:latest", help="Docker image to use")
    parser.add_argument('--local', action='store_true', default=True, help="Run locally in this directory.")
    parser.add_argument('--nop', action='store_true', default=False, help="Don't actually running anything.")
    parser.add_argument('--json', default=False, action='store_true', help="Dump json version of submission and response.")
    parser.add_argument('--directory', default=".", help="Lab root")
    parser.add_argument('--run-json', nargs="*", default=None, help="Read json submission spec from file.   With no arguments, read from stdin")
    parser.add_argument('--no-validate', action='store_false', default=True, dest='validate', help="Don't check for erroneously edited files.")
    parser.add_argument('--devel', action='store_true', default=False, dest='devel', help="Don't check for edited files and set DEVEL_MODE=yes in environment.")
    parser.add_argument('--local-clone', default=False, action='store_true', help="Clone the local repo instead of the origin")
    parser.add_argument('--solution', default=None, help="Subdirectory to fetch inputs from")

    args = parser.parse_args(argv)

    
    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)

    if args.run_json is not None:
        args.pristine = True
        log.info("Enabling pristine moder for json run")

    if args.devel:
        log.debug("Entering devel mode")
        args.validate = False
        os.environ['DEVEL_MODE'] = 'yes'

    # We default to 'solution' so the autograder will run the solution when we
    # test it with maste repo. Since we delete 'solution' in the starter repo,
    # it will use '.' for the students.
    if args.solution is None:
        solution = "solution" if os.path.isdir("solution") else "."
    else:
        solution = args.solution

    # Make sure it's relative.
    input_dir=os.path.join(".", solution)
    log.debug(f"Fetching inputs from '{input_dir}'")
    os.environ['LAB_SUBMISSION_DIR'] = input_dir
    
    try:
        if args.run_json is not None:
            if args.run_json == []:
                submission = Submission._fromdict(json.loads(sys.stdin.read()))
            else:
                submission = Submission._fromdict(json.loads(open(args.run_json[0]).read()))
            log.debug(f"loaded this submission from json:\n" + str(submission._asdict()))
        else:
            submission = build_submission(args.directory,
                                          input_dir,
                                          None)
            
            if args.validate:
                c = ['git', 'diff', '--exit-code', '--stat', '--', '.'] + list(map(lambda x : f'!{x}', submission.files.keys()))
                p = subprocess.Popen(c, cwd=args.directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=None)
                stdout, stderr = p.communicate()
                if p.returncode != 0:
                    log.error("You have modified files that won't be submitted.  This is unwise.  '--no-validate' to ignore.")
                    log.error(stdout.decode("utf-8"))
                    sys.exit(1)
   
        if args.json:
            sys.stdout.write(json.dumps(submission._asdict(), sort_keys=True, indent=4) + "\n")

            #log.debug("Submission: {}".format(json.dumps(submission._asdict(),  sort_keys=True, indent=4)))
        log.debug("Submission: {}".format(submission._asdict()))


        result = None
        if not args.nop:
            
            result = run_submission_locally(submission,
                                            root=args.directory,
                                            run_in_docker=args.docker,
                                            run_pristine=args.pristine,
                                            docker_image=args.docker_image)
            
            for i in result.files:
                log.debug("========================= {} ===========================".format(i))
                log.debug(result.files[i][:1000])
                if len(result.files[i]) > 1000:
                    log.debug("< more output >")
                    
                if i == "STDERR":
                    sys.stdout.write(result.files[i])
                elif i == "STDOUT":
                    sys.stdout.write(result.files[i])
                    
                with open(os.path.join(args.directory, i), "w") as t:
                    t.write(result.files[i])
            
    except RunnerException as e: 
        log.error(e)
        status = "Unknown failure: {e}"
    else:
        status = result.status if result else "success"
        
    log.info(f"Finished.  Final status: {status}")


if __name__ == '__main__':
    main(sys.argv[1:])

