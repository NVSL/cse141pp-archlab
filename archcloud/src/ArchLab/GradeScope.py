import json
import time
import os
import argparse
from .Runner import run_submission_remotely, build_submission, UserError, ArchlabError

import sys
import logging as log
import platform
import dateutil.parser
import datetime
import copy
import traceback

def main(argv=sys.argv[1:]):
        parser = argparse.ArgumentParser(description='Run a lab.')
        parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")
        parser.add_argument('--root', default="/autograder", help="Autograder root")
        parser.add_argument('--debug', action='store_true', help="exit on errors")
        parser.add_argument('--daemon', action='store_true', default=False, help="Start a local server to run my job")
        args = parser.parse_args(argv)

        log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                        level=log.DEBUG if args.verbose else log.INFO)

        log.info(f"Running in {os.environ['CLOUD_MODE']}")
        log.info(f"Running in {os.environ['IN_DEPLOYMENT']}")
        log.info(f"Running in {os.environ['GOOGLE_RESOURCE_PREFIX']}")
        log.info(f"Allowed repos: {os.environ['VALID_LAB_STARTER_REPOS']}")

        def default_file_output():
                return {
                        "score": 0.0, # optional, but required if not on top level submission
                        "max_score": 0.0, # optional
                        "name": "",
                        "output": "",
                        "visibility": "visible", # Optional visibility setting
                }

        output={
                        "score": 0,
                        "visibility": "visible", 
                        "stdout_visibility": "visible", 
                        "tests": []
                }


        files = []
        tail =[]
        result = None
        try:
                metadata_fn = os.path.join(args.root, 'submission_metadata.json')
                results_fn = os.path.join(args.root, 'results/results.json')
                submission_dir = os.path.join(args.root, 'submission')

                with open(metadata_fn) as f:
                        metadata_str = f.read()
                        metadata = json.loads(metadata_str)

                recent_submissions = 0
                latest_submission = None

                log.debug(f"{output}")
                start_time = time.time()

                try:
                        # Sometimes we don't get a
                        # user from gradescope.  Resubmitting
                        # seems to fix it.
                        username= metadata['users'][0]["email"]
                except IndexError as e:
                        raise ArchlabError("Malformed job metadata.  Probably gradescope's fault.  Resubmit.")

                submission = build_submission(submission_dir, username=username)

                if submission.lab_spec.repo not in os.environ['VALID_LAB_STARTER_REPOS']:
                        raise UserError(f"Repo {submission.lab_spec.repo} is not one of the repos that is permitted for this lab.  You are probably submitting the wrong repo or to the wrong lab.")

                result = run_submission_remotely(submission, daemon=args.daemon)
        except UserError as e:
                t = default_file_output()
                t['name'] = "User Error"
                t['output'] = f"{traceback.format_exc()}\nA user error occurred with your job.  There is probably something wrong with your submission: {repr(e)}"
                files.append(t)
                if args.debug:
                        raise
        except ArchlabError as e:
                t = default_file_output()
                t['name'] = "Internal Error"
                t['output'] = f"{traceback.format_exc()}\nSomething unexpected went wrong in autograder.  Probably not your fault.: {repr(e)}"
                files.append(t)
                if args.debug:
                        raise
        except Exception as e:
                t = default_file_output()
                t['name'] = "Unexpected Internal Error"
                t['output'] = f"{traceback.format_exc()}\nAn exception occurred.  Probably not your fault: {repr(e)}"
                files.append(t)
                if args.debug:
                        raise
        else:
                files.append(
                        {
                                "score": 0.0, # optional, but required if not on top level submission
                                "max_score": 0.0, # optional
                                "name": "zip_output_url",
                                "output": f"Your lab inputs and oututs are available in this zip file:\n{result.zip_archive}\nWhen prompted, log in as '{metadata['users'][0]['email']}' to access it.\nIf you have trouble, either log out of google or open it in your browser's 'private' or 'incognito' mode.",
                                "visibility": "visible", # Optional visibility setting
                        }
                )

                d = copy.deepcopy(result)
                d.files = None # this is rendudant and large
                d.submission.files = None #this too
                d.results = None
                tail.append(
                        {
                                "score": 0.0, # optional, but required if not on top level submission
                                "max_score": 0.0, # optional
                                "name": "full_json_result",
                                "output": json.dumps(d._asdict(), indent=4, sort_keys=True),
                                "visibility": "visible", # Optional visibility setting
                        }
                )

        finally:
                end_time = time.time()
                if result:
                        output = result.results.get('gradescope_test_output', output)
                        output['output'] = f"""
================== STDOUT =======================
{result.get_file('STDOUT.txt')}
================== STDERR =======================
{result.get_file('STDERR.txt')}
=================================================
If you see any of the following in the output above, do not be alarmed.  They are not errors:

* WARNING You have uncommitted changes and/or there is changes in github that you don't have locally. This means local behavior won't match what the autograder will do.

* If you have not been specifically asked to management the live deployment of these tools, you should not be here. To leave: type 'notdeployed'

If something seems to have not worked poperly, check the field right below this one ("submission status")

"""

                status = {
                        "score": 0.0, # optional, but required if not on top level submission
                        "max_score": 0.0, # optional
                        "name": "submission status",
                        "visibility": "visible", # Optional visibility setting
                }
                if result:
                        status["output"] = f"Job outcome: {result.status}" + ("" if result.status == "success" else f"ERROR:\n{result.status_reasons}")
                else:
                        status["output"] = f"Job outcome: Pre-execution failure in GradeScope.py"
                files.insert(0, status)
                        
                output["execution_time"] = float(end_time - start_time)
                output['tests'] = files + output['tests'] + tail 

                

        log.debug(f"Writing to {os.path.abspath(results_fn)}")
        with open(os.path.abspath(results_fn), 'w') as f:
                t = json.dumps(output)
                log.debug(t)
                f.write(t)
