import json
import time
import os
import argparse
from .Runner import run_submission_remotely, build_submission
import sys
import logging as log
import platform
import dateutil.parser
import datetime
import copy

def main(argv=sys.argv[1:]):
        parser = argparse.ArgumentParser(description='Run a lab.')
        parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")
        parser.add_argument('--root', default="/autograder", help="Autograder root")
        args = parser.parse_args(argv)

        log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if args.verbose else "%(levelname)-8s %(message)s",
                        level=log.DEBUG if args.verbose else log.INFO)
        
        metadata_fn = os.path.join(args.root, 'submission_metadata.json')
        results_fn = os.path.join(args.root, 'results/results.json')
        submission_dir = os.path.join(args.root, 'submission')
        
        with open(metadata_fn) as f:
                metadata_str = f.read()
                metadata = json.loads(metadata_str)

        manifest = 'one file from student repo'

        recent_submissions = 0
        latest_submission = None

#        for p in metadata['previous_submissions']:
#                t = dateutil.parser.parse(p['submission_time'])
#                if t > datetime.datetime.now() - datetime.timedelta(hours=1):
#                        recent_submissions += 1
#if latest_submission == None or t > dateutil.parser.parse(latest_submission['submission_time']):
#                        latest_submission = p
                        
        if recent_submissions > 1:
                log.info("Too many recent submissions.  Copying old results to current results.")
                output = latest_submission['results']
        else:
                start_time = time.time()
                submission = build_submission(submission_dir, ".", None, username=metadata['users'][0]["email"])
                result = run_submission_remotely(submission)

                files = []

                for filename in result.files:
                        log.debug(f"output file {filename}")
                        try:
                                contents = result.get_file(filename)
                        except UnicodeDecodeError:
                                contents = "<couldn't decode file.  Is it binary>"
                                
                        files.append(
                                {
                                        "score": 0.0, # optional, but required if not on top level submission
                                        "max_score": 0.0, # optional
                                        "name": filename, # optional
                                        "output": contents,
                                        "visibility": "visible", # Optional visibility setting
                                }
                        )
                end_time = time.time()

                default = {
                        "score": 0,
                        "visibility": "after_due_date", 
                        "stdout_visibility": "visible", 
                        "tests": []
                }

                # this script needs to write out the score/time etc...

                output = result.results.get('gradescope_test_output', default)
                output["execution_time"] = float(end_time - start_time)
                d = copy.deepcopy(result)
                d.files = None # this is rendudant and large
                d.submission.files = None #this too
                output['output'] = json.dumps(d._asdict(), indent=4, sort_keys=True)
                output['tests'] = files + output['tests'] # merge in tests

        with open(results_fn, 'w') as f:
                log.debug(f"Gradescope output (without files): {d}")
                f.write(json.dumps(output))

        
