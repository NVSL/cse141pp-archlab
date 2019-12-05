#!/usr/bin/env python3

from .Runner import build_submission, run_submission_locally, run_submission_remotely, Submission, RunnerException, SubmissionResult, LabSpec
import logging as log
import json
import platform
import argparse
import sys
import os
import subprocess
import base64
import textwrap

def show_info():
    try:
        spec=LabSpec.load(".")
        return spec.get_help()
    except :
        return "Not a lab directory"

def main(argv=None):
    """
    This is the command line driver for Runner.py.  It should demonstrate everything you'll need to do with the library.

    The assumption is that the local directory has a clone of a lab repo.  Lab repos have `lab.py` in them.  The possible fields in a `lab.py` are described in `Runner.LabSpec`

    You can then do:
    1. `./runlab` To run the lab in the loecal directory.
    2. `./runlab --pristine` To run the lab in a fresh clone of the lab's repo with the local input files (specified in lab.py) copied in.
    3. `./runlab --pristine --docker` to run the lab in docker container.
    4. `./runlab --json` to dump the json version of the lab submission and response to stdout.
    5. `./runlab --json --nop` to dump the json version of the lab submission stdout, but not run anything.
    6. `./runlab --json --nop | ./runlab --run-json --pristine --docker` generate the submission, consume it, and run it in a pristine clone in a docker container.

    """

    student_mode = "STUDENT_MODE" in os.environ # Don't get any clever
                                                # ideas, this just
                                                # hides the options to
                                                # the make help more
                                                # useful.  Access
                                                # control checks
                                                # happen
                                                # elsewhere. ;-)
    
    parser = argparse.ArgumentParser(description=textwrap.dedent("""Run a Lab

    Running the lab with this command ensure that your compilation and
    execution enviroment matches the autograder's as closely as possible.
    
    Useful options include:
    
    * '--no-validate' to run your code without committing it.
    * '--info' to see the parameters for the current lab.
    * '--pristine' to (as near as possible) exactly mimic how the autograder runs code.
    
    """),
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Be verbose")
    parser.add_argument('--pristine', action='store_true', default=False, help="Clone a new repo")
    parser.add_argument('--info', action="store_true", help="Print information about this lab an exit")
    parser.add_argument('--no-validate', action='store_false', default=True, dest='validate', help="Don't check for erroneously edited files.")
    parser.add_argument('command', nargs=argparse.REMAINDER, help="Command to run (optional).  By default, it'll run the command in lab.py.")

    def sm(s):
        if 'STUDENT_MODE' in os.environ:
            return argparse.SUPPRESS
        else:
            return s
        
    parser.add_argument('--devel', action='store_true', default=student_mode, dest='devel', help=sm("Don't check for edited files and set DEVEL_MODE=yes in environment."))
    parser.add_argument('--nop', action='store_true', default=False, help=sm("Don't actually run anything."))
    parser.add_argument('--native', action='store_false', dest='devel', help=sm("Don't check for edited files and set DEVEL_MODE=yes in environment."))
    parser.add_argument('--docker', action='store_true', default=False, help=sm("Run in a docker container."))
    parser.add_argument('--docker-image', default=os.environ['DOCKER_RUNNER_IMAGE'], help=sm("Docker image to use"))
    parser.add_argument('--json', default=False, action='store_true', help=sm("Dump json version of submission and response."))
    parser.add_argument('--directory', default=".", help=sm("Lab root"))
    parser.add_argument('--run-json', nargs="*", default=None, help=sm("Read json submission spec from file.   With no arguments, read from stdin"))
    parser.add_argument('--remote', action='store_true', default=False, help=sm("Run remotely"))
    parser.add_argument('--solution', default=None, help=sm("Subdirectory to fetch inputs from"))
    parser.add_argument('--lab-override', nargs='+', default=[], help=sm("Override lab.py parameters."))
    parser.add_argument('--debug', action="store_true", help=sm("Be more verbose about errors."))
    parser.add_argument('--verify-repo', action="store_true", help=sm("Check that repo in lab.py is on the whitelist"))


    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)

    log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if True else "%(levelname)-8s %(message)s",
                    level=log.DEBUG if True else log.INFO)

    log.debug(f"Command line args: {args}")

    if args.info:
        sys.stdout.write(show_info())
        return 

    if args.run_json is not None:
        args.pristine = True
        log.info("Enabling pristine modern for json run")

    if args.devel:
        log.debug("Entering devel mode")
        args.validate = False
        os.environ['DEVEL_MODE'] = 'yes'

    if args.command and len(args.command) > 0:
        log.debug(f"Got command arguments: {args.command}")
        assert args.command[0] == "--", f"Unknown arguments: {args.command}"
        args.command = args.command[1:]
        log.debug(f"Using command: {args.command}")
    else:
        args.command = None
        
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
                                          args.command,
                                          username=os.environ.get("USER"))
            

            for i in args.lab_override:
                k, v = i.split("=")
                log.debug(f"Overriding lab spec: {k} = {v}")
                setattr(submission.lab_spec, k, v)
                log.debug(f"{submission.lab_spec._asdict()}")
            
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

        log.debug("Submission: {}".format(submission._asdict()))

        result = None
        if not args.nop:

            if not args.remote:
                result = run_submission_locally(submission,
                                                root=args.directory,
                                                run_in_docker=args.docker,
                                                run_pristine=args.pristine,
                                                docker_image=args.docker_image,
                                                verify_repo=args.verify_repo)
            else:
                result = run_submission_remotely(submission)
                
            log.debug(f"Got response: {result}")
            log.debug(f"Got response: {result._asdict()}")
            for i in result.files:
                log.debug("========================= {} ===========================".format(i))
                log.debug(result.files[i][:1000])
                if len(result.files[i]) > 1000:
                    log.debug("< more output >")
                    
                if i == "STDERR":
                    sys.stdout.write(result.files[i])
                elif i == "STDOUT":
                    sys.stdout.write(result.files[i])
                    
                with open(os.path.join(args.directory, i), "wb") as t:
                    log.debug(f"Writing data to {i}: {result.files[i][0:100]}")
                    t.write(base64.b64decode(result.files[i]))

            with open(os.path.join(args.directory, "results.json"), "w") as t:
                t.write(json.dumps(result.results, sort_keys=True, indent=4))
                sys.stdout.write("Extracted results:\n" + json.dumps(result.results, sort_keys=True, indent=4) + "\n")
                
    except RunnerException as e: 
        log.error(e)
        status_str = "Unknown failure: {e}"
        exit_code = 1
    except Exception as e:
        if args.debug:
            raise
        else:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)
    else:
        if result:
            status_str =  result.status
            if result.status == SubmissionResult.SUCCESS:
                exit_code = 0
            else:
                exit_code = 1
        else:
            status_str =  "success"
            exit_code = 0
        
    log.info(f"Finished.  Final status: {status_str}")
    log.debug(f"Exit code: {exit_code}")
    sys.exit(exit_code)


if __name__ == '__main__':
    main(sys.argv[1:])

