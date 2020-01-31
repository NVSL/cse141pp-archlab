#!/usr/bin/env python3

from .Runner import build_submission, run_submission_locally, run_submission_remotely, run_submission_by_proxy, Submission, ArchlabError, UserError, SubmissionResult, LabSpec, ArchlabTransientError
import logging as log
import json
import platform
import argparse
import sys
import os
import subprocess
import base64
import textwrap
import tempfile
from  .CSE141Lab import CSE141Lab
import traceback

dev_null=open("/dev/null", "w")

def show_info(directory, fields=None):
    try:
        spec=LabSpec.load(directory)
        if fields == []:
            return spec.get_help()
        else:
            return f"{getattr(spec, fields)}\n"
    except FileNotFoundError:
        return "Not a lab directory\n"
    except AttributeError:
        return f"Unknown field: {fields}\n"

def set_upstream():
    if os.path.exists(".starter_repo"):
        with open(".starter_repo") as f:
            upstream = f.read().strip()
    else:
        log.warning("Can't find '.starter_repo', so I can't check for updates")
        return False
        
    current_remotes = subprocess.check_output(['git', 'remote']).decode("utf8")
    if "upstream" in current_remotes:
        log.debug("Remote upstream is set")
        return True
    try:
        subprocess.check_call(f"git remote add upstream {upstream}".split(), stdout=dev_null)
        return True
    except:
        log.error("Failed to set upstream remote")
        return False

def check_for_updates():

    try:
        subprocess.check_call("git fetch upstream".split(), stdout=dev_null)
        common_ancestor = subprocess.check_output("git merge-base HEAD remotes/upstream/master".split()).decode("utf8").strip()
        log.debug(f"Common ancestor for merge: {common_ancestor}")
    except:
        log.error("Failed to check for updates.")
        return
    
    if subprocess.run(f"git diff --exit-code {common_ancestor} remotes/upstream/master -- ".split(), stdout=dev_null).returncode != 0:

        sys.stdout.write("""
===================================================================
# The lab starter repo has been changed.  The diff follows.
# Do `runlab --merge-updates` to merge the changes into your repo.\n""")
        subprocess.run(f"git diff {common_ancestor} remotes/upstream/master -- ".split())
        sys.stdout.write("""
===================================================================\n""")
    else:
        sys.stdout.write("No updates available for this lab.\n")


def merge_updates():
    try:
        subprocess.check_call("git fetch upstream".split(), stdout=dev_null)
    except:
        log.error("Failed to check for updates.")
        return

    try:
        subprocess.call(["git", "merge", "-m", "merge in updates from the starter repo", "remotes/upstream/master"])
    except:
        log.error("Failed to merge updates")
        raise
    
    
def main(argv=None):
    """
    This is the command line driver for Runner.py.  It should demonstrate everything you'll need to do with the library.

    The assumption is that the local directory has a clone of a lab repo.  Lab repos have `lab.py` in them.  The possible fields in a `lab.py` are described in `Runner.LabSpec`

    You can then do:
    1. `./runlab` To run the lab in the local directory.
    2. `./runlab --pristine` To run the lab in a fresh clone of the lab's repo with the local input files (specified in lab.py) copied in.
    3. `./runlab --pristine --docker` to run the lab in docker container.
    4. `./runlab --json` to dump the json version of the lab submission and response to stdout.
    5. `./runlab --json --nop` to dump the json version of the lab submission stdout, but not run anything.
    6. `./runlab --json --nop | ./runlab --run-json --pristine --docker` generate the submission, consume it, and run it in a pristine clone in a docker container.

    """

    student_mode = os.environ.get("STUDENT_MODE", "no").upper() == "YES"
    # Don't get any clever
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

    def sm(s): return s
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help="Be verbose")
    parser.add_argument('--pristine', action='store_true', default=False, help="Clone a new copy of the reference repo.")
    parser.add_argument('--info', nargs="?", default=None, const=[],  help="Print information about this lab an exit.  With an argument print that field of lab structure.")
    parser.add_argument('--no-validate', action='store_false', default=True, dest='validate', help="Don't check for erroneously edited files.")
    parser.add_argument('command', nargs=argparse.REMAINDER, help="Command to run (optional).  By default, it'll run the command in lab.py.")
    parser.add_argument('--branch',  help="When running a git repo, use this branch instead of the current branch")
    parser.add_argument('--run-git-remotely', action='store_true', default=False, help="Run the contents of this repo remotely")

    def sm(s):
        if student_mode:
            return argparse.SUPPRESS
        else:
            return s

    parser.add_argument('--repo', help=sm("Run this repo"))
    parser.add_argument('--proxy', default=os.environ.get('RUNLAB_PROXY', "http://127.0.0.1:5000"), help=sm("Proxy host"))
    parser.add_argument('--devel', action='store_true', default=student_mode, dest='devel', help=sm("Don't check for edited files and set DEVEL_MODE=yes in environment."))
    parser.add_argument('--nop', action='store_true', default=False, help=sm("Don't actually run anything."))
    parser.add_argument('--native', action='store_false', dest='devel', help=sm("Don't check for edited files and set DEVEL_MODE=yes in environment."))
    parser.add_argument('--docker', action='store_true', default=False, help=sm("Run in a docker container."))
    parser.add_argument('--docker-image', default=os.environ['DOCKER_RUNNER_IMAGE'], help=sm("Docker image to use"))
    parser.add_argument('--json', default=None, help=sm("Dump json version of submission and response."))
    parser.add_argument('--directory', default=".", help=sm("Lab root"))
    parser.add_argument('--run-json', nargs="*", default=None, help=sm("Read json submission spec from file.   With no arguments, read from stdin"))
    parser.add_argument('--json-status', help=sm("Write exit status to file"))
    parser.add_argument('--remote', action='store_true', default=False, help=sm("Run remotely"))
    parser.add_argument('--daemon', action='store_true', default=False, help=sm("Start a local server to run my job"))
    parser.add_argument('--solution', default=None, help=sm("Subdirectory to fetch inputs from"))
        
    parser.add_argument('--lab-override', nargs='+', default=[], help=sm("Override lab.py parameters."))
    parser.add_argument('--debug', action="store_true", help=sm("Be more verbose about errors."))
    parser.add_argument('--zip',action='store_true', help=sm("Generate a zip file of inputs and outputs"))
    parser.add_argument('--verify-repo', action="store_true", help=sm("Check that repo in lab.py is on the whitelist"))
    parser.add_argument('--public-only', action="store_true", help=sm("Only load the public lab configuration"))
    parser.add_argument('--quieter', action="store_true", help=sm("Be quieter"))
    parser.add_argument('--check-for-updates', action='store_true', help=sm("Check for upstream updates"))
    parser.add_argument('--merge-updates', action='store_true', help="Merge in updates from starter repo.")
    
    if argv == None:
        argv = sys.argv[1:]
        
    args = parser.parse_args(argv)

    if not args.verbose and student_mode:
        log.basicConfig(format="%(levelname)-8s %(message)s", level=log.WARN)
    else:
        log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                        level=log.DEBUG if args.verbose else log.WARN)

    log.debug(f"Command line args: {args}")


    if student_mode:
        args.check_for_updates = True

    if args.merge_updates:
        try:
            merge_updates()
        except:
            if debug:
                raise
            return 1
        else:
            return 0

    if args.check_for_updates:
        if set_upstream():
            check_for_updates()

    if args.info != None:
        sys.stdout.write(show_info(args.directory, args.info))
        return 

            
    if args.run_git_remotely:
        if not args.repo:
            args.repo = subprocess.check_output("git config --get remote.origin.url".split()).strip()
        if not args.branch:
            args.branch = subprocess.check_output("git rev-parse --abbrev-ref HEAD".split()).strip()
        args.pristine=True
        
    if args.repo or args.branch:
        if not args.pristine:
            args.pristine = True
            
    if not CSE141Lab.does_papi_work():
        log.warn("Forcing '--devel' because PAPI doesn't work on this machine")
        args.devel = True

    if args.devel:
        log.debug("Entering devel mode")
        os.environ['DEVEL_MODE'] = 'yes'

    if args.command and len(args.command) > 0:
        log.debug(f"Got command arguments: {args.command}")
        assert args.command[0] == "--", f"Unknown arguments: {args.command}"
        args.command = args.command[1:]
        log.debug(f"Using command: {args.command}")
    else:
        args.command = None

    try:
        if args.run_json is not None:
            if args.run_json == []:
                submission = Submission._fromdict(json.loads(sys.stdin.read()))
            else:
                submission = Submission._fromdict(json.loads(open(args.run_json[0]).read()))
            log.debug(f"loaded this submission from json:\n" + str(submission._asdict()))
        elif args.run_git_remotely:
            pass
        else:
            submission = build_submission(args.directory,
                                          args.solution,
                                          args.command,
                                          public_only=args.public_only,
                                          username=os.environ.get("USER_EMAIL"),
                                          pristine=args.pristine,
                                          repo=args.repo,
                                          branch=args.branch)

            for i in args.lab_override:
                k, v = i.split("=")
                log.debug(f"Overriding lab spec: {k} = {v}")
                setattr(submission.lab_spec, k, v)
                log.debug(f"{submission.lab_spec._asdict()}")
            

            if not args.repo:
                diff = ['git', 'diff', '--exit-code', '--stat', '--', '.'] + list(map(lambda x : f'!{x}', submission.files.keys()))
                update = ['git', 'remote', 'update']
                unpushed = ['git' , 'status', '-uno']
                reporter = log.error if args.validate else log.warn

                try:
                    subprocess.check_call(diff, stdout=dev_null)
                    subprocess.check_call(update, stdout=dev_null)
                    if not "Your branch is up-to-date with" in subprocess.check_output(unpushed).decode('utf8'):
                        raise Exception()
                except:
                    reporter("You have uncommitted changes and/or there is changes in github that you don't have locally.  This means local behavior won't match what the autograder will do.")
                    if args.validate:
                        log.error("To run anyway, pass '--no-validate'.  Alternately, to mimic the autograder as closely as possible (and require committing your files), do '--pristine'")
                        if args.debug:
                            raise
                        else:
                            sys.exit(1)

                    
        if args.json:
            with open(args.json, "w") as f:
                f.write(json.dumps(submission._asdict(), sort_keys=True, indent=4) + "\n")

        result = None
        if not args.nop:

            if args.remote:
                result = run_submission_remotely(submission, daemon=args.daemon)
            elif args.run_git_remotely:
                result = run_submission_by_proxy(proxy=args.proxy,
                                                 repo=args.repo,
                                                 branch=args.branch)
             
            else:
                result = run_submission_locally(submission,
                                                run_in_docker=args.docker,
                                                run_pristine=args.pristine,
                                                docker_image=args.docker_image,
                                                verify_repo=args.verify_repo)

                
            log.debug(f"Got response: {result}")
            for i in result.files:
                log.debug("========================= {} ===========================".format(i))
                d = result.get_file(i)
                log.debug(d[:1000])
                if len(d) > 1000:
                    log.debug("< more output >")
                    
                if i == "STDERR.txt":
                    sys.stdout.write(result.get_file(i))
                elif i == "STDOUT.txt":
                    sys.stdout.write(result.get_file(i))
                    
                log.debug("Extracted results:\n" + json.dumps(result._asdict(), sort_keys=True, indent=4) + "\n")

            if args.zip:
                with open("files.zip", "wb") as f:
                    f.write(result.build_file_zip_archive())

            log.info(f"Grading results:\n{result.results}")
    except UserError as e: 
        log.error(f"User error (probably your fault): {repr(e)}")
        status_str = f"{repr(e)}"
        exit_code = 1
        if args.debug:
            raise
    except ArchlabError as e:
        log.error(f"System error (probably not your fault): {repr(e)}")
        status_str = f"{traceback.format_exc()}\n{repr(e)}"
        exit_code = 1
        if args.debug:
            raise
    except ArchlabTransientError as e:
        log.error(f"System error (probably not your fault): {repr(e)}")
        status_str = f"{repr(e)}"
        exit_code = 1
        if args.debug:
            raise
    except Exception as e:
        log.error(f"Unknown error (probably not your fault): {repr(e)}")
        status_str = f"{traceback.format_exc()}\n{repr(e)}"
        exit_code = 1
        if args.debug:
            raise
    else:
        if result:
            status_str = f"{result.status}\n" + '\n'.join(result.status_reasons)
            if result.status == SubmissionResult.SUCCESS:
                exit_code = 0
            else:
                exit_code = 1
        else:
            status_str =  "success"
            exit_code = 0
        
    log.info(f"Finished.  Final status: {status_str}")
    if exit_code != 0:
        log.info(f"Rerun with '--debug -v' for more details")
    log.debug(f"Exit code: {exit_code}")
    if args.json_status:
        with open(args.json_status, "w") as f:
            f.write(json.dumps(dict(exit_code=exit_code,
                                    status_str=status_str)))
    sys.exit(exit_code)

if __name__ == '__main__':
    main(sys.argv[1:])

