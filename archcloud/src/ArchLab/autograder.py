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
import random
from uuid import uuid4 as uuid
import time
import os
from .Runner import run_submission_remotely
import sys

def main():
        
        RUNNER_PATH = '/cse141pp-archlab/archcloud'
        sys.path.insert(1, '/cse141pp-archlab/archcloud')
        from Runner import build_submission

        metadata_fn = '/autograder/submission_metadata.json'
        results_fn = '/autograder/results/results.json'

        with open(metadata_fn) as f:
                metadata_str = f.read()
                print(metadata_str)
                metadata = json.loads(metadata_str)

        metadata = json.dumps(metadata)
        manifest = 'one file from student repo'

        cdir = os.getcwd()
        os.chdir('/autograder/submission/')
        submission = build_submission('/autograder/submission', [])
        os.chdir(cdir)

        result = run_submission_remotely(submission, metadata, manifest)

        files = []

        for key, value in result.files.items():
                files.append(
                        {
                                "score": 0.0, # optional, but required if not on top level submission
                                "max_score": 0.0, # optional
                                "name": key, # optional
                                # "number": "1.1", # optional (will just be numbered in order of array if no number given)
                                "output": value, # "Giant multiline string that will be placed in a <pre> tag and collapsed by default", # optional
                                # "tags": ["tag1", "tag2", "tag3"], # optional
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
                "leaderboard": json.loads(job_data['output'])['figures_of_merit'] # Optional, will set up leaderboards for these values
        }

        with open(results_fn, 'w') as f:
                f.write(json.dumps(output))

        
