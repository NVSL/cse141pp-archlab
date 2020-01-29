from flask import Flask, escape, request
import json
import subprocess
import os
import tempfile
from .Runner import run_submission_remotely, build_submission, UserError, ArchlabError
import traceback
import sys
import logging as log
import platform
import re

app = Flask(__name__)

debug=False

def fail(**kwargs):
    t = json.dumps(kwargs, indent=4)
    sys.stderr.write(t)
    return t

log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if True else "%(levelname)-8s %(message)s",
                level=log.DEBUG)


@app.route('/jobs/submit',methods=["POST"])
def submit_job():
    log.warning(f"Got request: {request.form}")
    repo = request.form['repo']
    branch = request.form['branch']

    student_repo = re.search("/CSE141pp/wi20-CSE141L-(.*)-(\w+)", repo)
    master_repo = re.search("/NVSL/.*Lab-(.*)", repo)
    if student_repo:
        username=studet_repo.group(2)
    elif master_repo:
        username="staff"
    else:
        return fail(status="FAILURE",
                    reason=f"{repo} is not repo for this class.")
    
    os.makedirs("/jobs", exist_ok=True)
    with tempfile.TemporaryDirectory(dir="/jobs/") as work_dir:

        try:
            submission = build_submission(work_dir, username=username, repo=repo, branch=branch, pristine=True)

#            if submission.lab_spec.repo not in os.environ['VALID_LAB_STARTER_REPOS']:
#                raise UserError(f"Repo {submission.lab_spec.repo} is not one of the repos that is permitted for this lab.  You are probably submitting the wrong repo or to the wrong lab.")

            result = run_submission_remotely(submission)#, daemon=True)

        except UserError as e:
            if debug:
                raise
            return fail(status="FAILURE",
                        reason=f"{traceback.format_exc()}\nA user error occurred with your job.  There is probably something wrong with your submission: {repr(e)}")
        except ArchlabError as e:
            if debug:
                raise
            return fail(status="FAILURE",
                        reason=f"{traceback.format_exc()}\nSomething unexpected went wrong in autograder.  Probably not your fault.: {repr(e)}")
        except Exception as e:
            if debug:
                raise
            return fail(status="FAILURE",
                        reason=f"{traceback.format_exc()}\nAn exception occurred.  Probably not your fault: {repr(e)}.")
        finally:
            pass
        
        return json.dumps(dict(status="SUCCESS",
                               result=result._asdict()))
    
