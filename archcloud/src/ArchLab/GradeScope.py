"""
This program should send the submission metadata (in /autograder/submission_metadata.json) to the job queue.
Then it should wait for a response and write the response to /autograder/results/results.json


Output format:
{ "score": 44.0, // optional, but required if not on each test case below. Overrides total of tests if specified.
  "execution_time": 136, // optional, seconds
  "output": "Text relevant to the entire submission", // optional
  "visibility": "after_due_date", // Optional visibility setting
  "stdout_visibility": "visible", // Optional stdout visibility setting
  "extra_data": {}, // Optional extra data to be stored
  "tests": // Optional, but required if no top-level score
    [
        {
            "score": 2.0, // optional, but required if not on top level submission
            "max_score": 2.0, // optional
            "name": "Your name here", // optional
            "number": "1.1", // optional (will just be numbered in order of array if no number given)
            "output": "Giant multiline string that will be placed in a <pre> tag and collapsed by default", // optional
            "tags": ["tag1", "tag2", "tag3"], // optional
            "visibility": "visible", // Optional visibility setting
            "extra_data": {} // Optional extra data to be stored
        },
        // and more test cases...
    ],
  "leaderboard": // Optional, will set up leaderboards for these values
    [
      {"name": "Accuracy", "value": .926},
      {"name": "Time", "value": 15.1, "order": "asc"},
      {"name": "Stars", "value": "*****"}
    ]
}


metadata format:

{
  "created_at": "2018-07-01T14:22:32.365935-07:00", // Submission time
  "assignment": { // Assignment details
    "due_date": "2018-07-31T23:00:00.000000-07:00",
    "group_size": 4, // Maximum group size, or null if not set
    "group_submission": true, // Whether group submission is allowed
    "id": 25828, // Gradescope assignment ID
    "late_due_date": null, // Late due date, if set
    "release_date": "2018-07-02T00:00:00.000000-07:00",
    "title": "Programming Assignment 1",
    "total_points": "20.0" // Total point value, including any manual grading portion
  },
  "users": [
    {
      "email": "student@example.com",
      "id": 1234,
      "name": "Student User"
    }, ... // Multiple users will be listed in the case of group submissions
  ],
  "previous_submissions": [
    {
       "submission_time": "2017-04-06T14:24:48.087023-07:00",// previous submission time
      "score": 0.0, // Previous submission score
      "results": { ... } // Previous submission results object
    }, ...
  ]
}
"""

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
                submission = build_submission(submission_dir, ".", None, metadata=metadata, username=metadata['users'][0]["email"])
                result = run_submission_remotely(submission)

                files = []

                for filename in result.files:
                        files.append(
                                {
                                        "score": 0.0, # optional, but required if not on top level submission
                                        "max_score": 0.0, # optional
                                        "name": filename, # optional
                                        "output": result.get_file(filename), # "Giant multiline string that will be placed in a <pre> tag and collapsed by default", # optional
                                        "visibility": "visible", # Optional visibility setting
                                        "extra_data": {} # Optional extra data to be stored
                                }
                        )

                # this script needs to write out the score/time etc...
                end_time = time.time()

                output = { 
                        "score": (60.0*5.0) - float(end_time - start_time), # optional, but required if not on each test case below. Overrides total of tests if specified.
                        "execution_time": float(end_time - start_time), # optional, seconds
                        "output": str(result._asdict),
                        "visibility": "after_due_date", # Optional visibility setting
                        "stdout_visibility": "visible", # Optional stdout visibility setting
                        "extra_data": {}, # Optional extra data to be stored
                        "tests": files, # Optional, but required if no top-level score
                        # [
                        #     {
                        #         "score": 2.0, # optional, but required if not on top level submission
                        #         "max_score": 2.0, # optional
                        #         "name": "Your name here", # optional
                        #         "number": "1.1", # optional (will just be numbered in order of array if no number given)
                        #         "output": "Giant multiline string that will be placed in a <pre> tag and collapsed by default", # optional
                        #         "tags": ["tag1", "tag2", "tag3"], # optional
                        #         "visibility": "visible", # Optional visibility setting
                        #         "extra_data": {} # Optional extra data to be stored
                        #     },
                        #     # and more test cases...
                        # ],
                        "leaderboard": result.results['figures_of_merit'] # Optional, will set up leaderboards for these values
                }

        with open(results_fn, 'w') as f:
                f.write(json.dumps(output))

        
