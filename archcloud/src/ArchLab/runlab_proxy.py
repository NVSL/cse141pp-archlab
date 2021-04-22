import platform
import logging as log
log.basicConfig(format="{} %(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s".format(platform.node()) if True else "%(levelname)-8s %(message)s",
                level=log.DEBUG)

from flask import Flask, escape, request
import json
import subprocess
import os
import tempfile
from .Runner import run_submission_remotely, build_submission, UserError, ArchlabError, Submission
import traceback
import sys
import re
import time
import textwrap 
app = Flask(__name__)

debug=False

def fail(**kwargs):
    t = json.dumps(kwargs, indent=4)
    sys.stderr.write(t)
    return t

@app.route('/hello',methods=["GET"])
def submit_hello():
    return "Hello"

@app.route('/jobs/submit-full', methods=["POST"])
def submit_job():
    log.warning(f"Got request: {request.form}")
    os.makedirs("/status_files", exist_ok=True)
    _sub = request.form['submission']
    submission = Submission._fromdict(json.loads(_sub))
    submission.username += f"({request.remote_addr})"
    
    try:
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

@app.route('/jobs/submit',methods=["POST"])
def submit_gitjob():
    log.warning(f"Got request: {request.form}")
    os.makedirs("/status_files", exist_ok=True)
    r = request.form['request']
    data = json.loads(r)
    repo = data['repo']
    branch = data['branch']
    command = data['command']

    log.info(f"command = {command}")
    
    student_repo = re.search("/CSE142/(.*)-(\w+)", repo)
    master_repo = re.search("/NVSL/.*Lab-(.*)", repo)
    
    if student_repo:
        username=student_repo.group(2)
        lock_path =os.path.join("/status_files", username)
        if os.path.exists(lock_path):
            with open(lock_path) as f :
                last_timestamp=float(f.read())
            if time.time() < last_timestamp + 60:
                return fail(status="FAILURE",
                            reason="You can only submit one job per minute")
        with open(lock_path, "w") as f:
            f.write(str(time.time()))

    elif master_repo:
        username="staff"
        lock_path = None
    else:
        return fail(status="FAILURE",
                    reason=f"{repo} is not repo for this class.")


    os.makedirs("/jobs", exist_ok=True)
    with tempfile.TemporaryDirectory(dir="/jobs/") as work_dir:

        try:
            submission = build_submission(work_dir, username=username, repo=repo, branch=branch, pristine=True, command=command)

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

def main():
    app.run(debug=True, host='0.0.0.0')
    
