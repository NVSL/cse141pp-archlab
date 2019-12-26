import re
import sys
import collections
import subprocess
import tempfile
import os
from io import StringIO
import traceback
import importlib.util
import logging as log
import requests
import json
import copy
from contextlib import contextmanager
import csv
from pathlib import Path
import functools
import unittest
from pathlib import Path
import io
import platform
import pytest
import base64
from uuid import uuid4 as uuid
import time
from .BlobStore import BlobStore
from .DataStore import DataStore
from .PubSub import Publisher
from zipfile import ZipFile

from gradescope_utils.autograder_utils.json_test_runner import JSONTestRunner

from .Columnize import columnize
import datetime
import pytz

class UserError(Exception):
    pass
class ArchlabError(Exception):
    pass

class BadOptionException(UserError):
    pass
class ConfigException(UserError):
    pass

class MalformedObject(ArchlabError):
    pass


class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)
        
    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)
        
    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)
                
@contextmanager
def environment(**kwds):
    env = copy.deepcopy(os.environ)
    os.environ.update(**kwds)
    try:
        yield None
    finally:
        os.environ.clear()
        os.environ.update(env)

@contextmanager
def collect_fields_of(obj):
    before = list(obj.__dict__.keys())
    try:
        yield None
    finally:
        obj._fields =  list(set(obj.__dict__.keys()) - set(before))
    
class LabSpec(object):

    def __init__(self,
                 lab_name=None,
                 short_name=None,
                 output_files=None,
                 input_files=None,
                 repo=None,
                 reference_tag = None,
                 config_file=None,
                 default_cmd=None,
                 clean_cmd=None,
                 valid_options={},
                 time_limit = 30,
                 solution="."):

        with collect_fields_of(self):
            self.lab_name = lab_name
            self.short_name = short_name
            self.output_files = output_files
            self.input_files = input_files
            self.repo = repo
            self.reference_tag = reference_tag
            self.default_cmd = default_cmd
            self.clean_cmd = clean_cmd
            self.valid_options = valid_options
            self.time_limit = time_limit
            self.solution = solution
            self.config_file = config_file

            
        if self.default_cmd is None:
            self.default_cmd = ['make']
        if self.clean_cmd is None:
            self.clean_cmd = ['make', 'clean']
        
        assert self.lab_name is not None, "You must name your lab"

    class GradedRegressions(unittest.TestCase):
        pass
    
    class MetaRegressions(unittest.TestCase):
        pass

    def run_gradescope_tests(self, result, dirname):
        out =io.StringIO()
        Class = type(self).GradedRegressions
        log.debug(f"Running regressions for {Class}")
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Class)
        with cd (dirname):
            with environment(**result.submission.env):
                JSONTestRunner(visibility='visible', stream=out, buffer=True).run(suite)
        result.results['gradescope_test_output'] = json.loads(out.getvalue())

    def run_meta_regressions(self, *argc, **kwargs):
        Class = type(self).MetaRegressions
        if kwargs.get('test_name', None):
            suite = unittest.defaultTestLoader.loadTestsFromName(kwargs['test_name'])
        else:
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(Class)
        del kwargs['test_name']
            
        runner = unittest.TextTestRunner(*argc, **kwargs)
        return runner.run(suite)
        
    def get_help(self):
        rows = []
        rows.append(["INFO", ""])
        rows.append(["=======", ""])
        rows += [[k,getattr(self, k)] for k in ["lab_name", "short_name", "input_files", "output_files", "default_cmd", "clean_cmd", "time_limit"]]
        rows.append(["", ""])
        rows.append(["OPTIONS", ""])
        rows.append(["=======", ""])
        rows += map(list,self.valid_options.items())
        out = columnize(rows, headers=None, divider=" : " )
        return out
        
    
    def _asdict(self):
        return {f:getattr(self, f) for f in self._fields}

    # there no reason for these to be methods of this class

    def csv_extract_by_line(self, file_contents, field, line=0):
        reader = csv.DictReader(StringIO(file_contents))
        d = list(reader)
        if len(d) < line + 1:
            log.debug(f"Returning None, because there is no line {line}")
            return None
        try:
            return float(d[line][field])
        except:
            return d[line][field]
    

    def csv_extract_by_lookup(self, file_contents, field, column, value):
        reader = csv.DictReader(StringIO(file_contents))
        d = list(reader)
        r = None
        for l in d:
            if l[column] == value:
                if r == None:
                    try:
                        return float(l[field])
                    except:
                        return l[field]
                else:
                    raise Exception(f"Multiple lines in output have {column}=={value}")
        return r
    
    def csv_column_values(self, file_contents, field):
        reader = csv.DictReader(StringIO(file_contents))
        def parse(x):
            try:
                return float(x)
            except:
                return x
        return map(lambda x: parse(x[field]), reader)
    
    def safe_env_value(self, v):
        safe_env = r"[a-zA-Z0-9_\-\. =\"\'\/]"
        if not re.match(fr"^{safe_env}*$", v):
            return False
        else:
            return True
        
    def parse_config(self, f):
        r = dict()
        for l in f.readlines():
            orig=l
            l = re.sub(r"#.*", "", l)
            log.debug(f"stripped: {l}")
            l = re.sub(r'"|\'', "", l)
            log.debug(f"stripped: {l}")
            l = l.strip()
            log.debug(f"stripped: {l}")
            if not l:
                continue

            m = re.match(r"(\w+)=(.*)", l)
            if not m:
                raise ConfigException(f"Malformed config line':  {l}")
            else:
                if m.group(1) not in self.valid_options:
                    raise ConfigException(f"Setting {m.group(1)} is not permitted.  Possibilities are {','.join(self.valid_options.keys())}")
                if not self.safe_env_value(m.group(2)):
                    raise ConfigException(f"Unsafe value in this line.  Values cannot contain special characters.: {l}")

            log.debug(f"Parsed '{orig}' as '{m.group(1)}' = '{m.group(2)}'")
            r[m.group(1)] = m.group(2)
        return r
    
    def filter_env(self, env):
        out = {}
        for e in self.valid_options:
            if e in env:
                v = env[e]
                if not self.safe_env_value(v):
                    log.warn(f"Environment variable '{e}' has a potentially unsafe value: '{v}'.  Imported environment variables can only contain charecters from {safe_env}.")
                else:
                    out[e] = env[e]
        return out

    def filter_files(self, submission):
        """
        
        Check and potentially modify input files.
        
        `submission` is a `Submission` object and `submission.files` has input
        files.  You can check and/or modify them. 

        Returns a tuple `success, error`.  If `not success`, then the reason should be `error`

        """
        return True, ""

    def filter_command(self, command):
        if command == self.default_cmd:
            return True, "", self.default_cmd
        else:
            return False, f"This lab only runs the default command: {self.default_cmd}", command

    def make_target_filter(self, command):
        if command[0] != "make":
            return False, "You can only run make in this lab", command

        # just allow simple strings and filenames
        if any(map(lambda x: not re.match(r"^[a-zA-Z0-9_\-\.]+$", x), command)):
            return False, f"One of these doesn't look like a make target: {command[1:]}", command

        return True, "", command
        
    @classmethod
    def _fromdict(cls, j):
        try:
            t = cls(**j)
        except TypeError:
            raise MalformedObject()
        return t

    @classmethod
    def load(cls, root, public_only=False):
        sys.path.insert(0, os.path.abspath(root))
        def load_file(name, f):
            path =  os.path.join(root, f)
            spec = importlib.util.spec_from_file_location(name, path)
            info = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(info)
            log.debug(f"Imported {path}")
            log.debug(f"{dir(info)}")
            return info

        if public_only:
            log.debug(f"Ignoring private.py")
            LabType = load_file("lab", "lab.py").ThisLab
        else:
            try:
                log.debug(f"Checking for private.py")
                LabType = load_file("private", "private.py").ThisLab
            except FileNotFoundError:
                log.debug(f"Falling back to lab.py")
                LabType = load_file("lab", "lab.py").ThisLab
                
        return LabType()

class Submission(object):

    def __init__(self, lab_spec, files, env, command, run_directory, user_directory, solution, username=None):
        self.lab_spec = lab_spec
        with collect_fields_of(self):
            self.files = files
            self.env = env
            self.command = command
            self.username = username
            self.user_directory = user_directory
            self.run_directory = run_directory
            self.solution = solution
            
    def _asdict(self):
        t = {f:getattr(self, f) for f in self._fields}
        t['lab_spec'] = self.lab_spec._asdict()
        return t

    @classmethod
    def _fromdict(cls, j):
        try:
            t = cls(**j)
            t.lab_spec = LabSpec(**t.lab_spec)
        except TypeError:
            raise MalformedObject
        else:
            return t

def extract_from_first_csv_line_by_field(file_contents, field):
    reader = csv.DictReader(StringIO(file_contents))
    d = list(reader)
    if len(d) == 0:
        return None
    return float(d[0][field])

class SubmissionResult(object):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    MISSING_OUTPUT= "missing_output"
    ERROR = "error"

    def __init__(self, submission, files, status, status_reasons, results=None):
        self.submission = submission
        #log.debug(f"{submission}")# {submission.__type__}  {submission.__type__.__name__}")
        assert isinstance(submission, Submission)
        self.files = files
        self.status = status
        self.status_reasons = status_reasons
        
        if results is None:
            self.results = {}
        else:
            self.results = results

    def get_file(self, name):
        try: # this seems horribly wrong. We return either bytes or a string...
            return base64.b64decode(self.files[name]).decode("utf8")
        except UnicodeDecodeError:
            return base64.b64decode(self.files[name])
    
    def put_file(self, name, contents):
        self.files[name] = base64.b64encode(contents).decode('utf8')
            
    def _asdict(self):
        return dict(submission=self.submission._asdict(),
                    files=self.files,
                    status=self.status,
                    results=self.results,
                    status_reasons=self.status_reasons)
    
    def write_outputs(self):
        for i in self.files:
            p = os.path.abspath(os.path.join(self.submission.user_directory, i))
            with open(p, "wb") as t:
                log.debug(f"Writing data to {p}: {self.files[i][0:100]}")
                t.write(base64.b64decode(self.files[i]))
                
        with open(os.path.join(self.submission.user_directory, "results.json"), "w") as t:
            log.debug(f"wrote {json.dumps(self.results, sort_keys=True, indent=4)}")
            t.write(json.dumps(self.results, sort_keys=True, indent=4))

    def build_file_zip_archive(self):
        out = io.BytesIO()
        zip_file = ZipFile(out,mode="w")
        
        for fn in self.files:
            zip_file.writestr(fn, self.get_file(fn))

        for fn in self.submission.files:
            zip_file.writestr(fn, base64.b64decode(self.submission.files[fn]).decode('utf8'))
        zip_file.close()

        return out.getvalue()

    @classmethod
    def _fromdict(cls, j):
        try:
            if j['submission']:
                j['submission'] = Submission._fromdict(j['submission'])
            return cls(**j)
        except TypeError:
            raise MalformedObject



def run_submission_remotely(submission, daemon=False):
    the_daemon = None
    log.info(f"Submitting remotely  {os.environ['IN_DEPLOYMENT']}")
    log.info(f"Submitting remotely  {os.environ['CLOUD_MODE']}")
    log.info(f"Submitting remotely  {os.environ['GOOGLE_RESOURCE_PREFIX']}")
    try:
        if daemon:
            log.debug("Starting local daemon")
            # This should ensure that the daemon processes our
            # requests.  This prevents interference between testing
            # instances.
            #os.environ['PRIVATE_PUBSUB_NAMESPACE'] = str(uuid())[-8:]
            the_daemon = subprocess.Popen(['runlab.d', '-v', '--debug', '--docker'])
        else:
            the_daemon = None

        with environment(**submission.env):
            # cleanup local outputs.  This is mostly so can reliably
            # test for the absence of particular outputs.
            subprocess.check_call(submission.lab_spec.clean_cmd, cwd=submission.user_directory)
            
        ds = DataStore()
        publisher = Publisher(topic=os.environ['PUBSUB_TOPIC'])

        job_submission_json = json.dumps(submission._asdict(), sort_keys=True, indent=4)

        job_id = str(uuid())

        output = ''

        blobstore = BlobStore(os.environ['JOBS_BUCKET'])
        blobstore.write_file(job_id, job_submission_json)
        ds.push(
            job_id,
            output='',
            status='SUBMITTED',
            username=submission.username
        )

        publisher.publish(job_id)

        c = 0
        while True:
            log.info("Waiting for job to appear...")
            job_data = ds.pull(
                job_id=job_id
            )
            if job_data:
                break
            c +=1
            if c > 20:
                raise ArchlabError("I was not able to submit your job.  This is a problem with the autograder.  Try again.")
            time.sleep(0.5)

        start_time = time.time()
        status = 'SUBMITTED'
        running_time = time.time() - start_time

        log.info(f"Started job {job_id}.")
        while True:

            job_data = ds.pull(
                job_id=job_id
            )

            running_time = time.time() - start_time

            if running_time > int(os.environ['UNIVERSAL_TIMEOUT_SEC']):
                status = SubmissionResult.TIMEOUT
                log.error(f'Job timed out after {running_time}s')
                ds.update(job_id,
                          status="COMPLETED",
                          completed_utc=datetime.datetime.now(pytz.utc),
                          submission_status=SubmissionResult.TIMEOUT)
                raise UserError(f"Your job ran for more than {os.environ['UNIVERSAL_TIMEOUT_SEC']} seconds, and was canceled")

            if job_data is None:
                log.error("Can't find job!")
                raise ArchlabError(f"Couldn't find job: {job_id}")
            else:
                log.debug(f"Job progress: {job_id[:8]} is {job_data['status']} on host {job_data['runner_host'] or '<na>'}")

                if job_data['status'] == 'COMPLETED':
                    log.info(f"Job finished after {running_time} seconds: {job_id}")
                    status = 'COMPLETED'
                    r = SubmissionResult._fromdict(json.loads(blobstore.read_file(f"{job_id}-result")))
                    r.write_outputs()
                    r.zip_archive = job_data['zip_archive']
                    return r
                elif job_data['status'] == 'ERROR':
                    raise ArchlabError(f"Job failed after {running_time} seconds: {job_id}:\nstatus={job_data['status']}\n{'; '.join(job_data['status_reasons'])}")
                elif job_data['status'] == 'STARTED':
                    pass  # keep running...
                elif job_data['status'] == 'SUBMITTED':
                    pass  # keep running...
                else:
                    raise ArchlabError(f"Job {job_id} in unknown state: '{job_data['status']}'")

            time.sleep(1)
    finally:
        if the_daemon:
            log.debug("Killing local daemon")
            the_daemon.terminate()
            the_daemon.wait()
            log.debug("Local daemon is dead.")
            try:
                del os.environ['PRIVATE_PUBSUB_NAMESPACE']
            except:
                pass
                  

def run_submission_locally(sub,
                           run_in_docker=False,
                           run_pristine=False,
                           nop=False,
                           timeout=None,
                           write_outputs=True, # write outputs in addition to capturing them
                           docker_image=None,
                           verify_repo=True,
                           user_directory_override=None):
    out = StringIO()
    err = StringIO()
    result_files = {}
    root = sub.run_directory
    reasons = []
    status = SubmissionResult.ERROR

    def log_run(cmd, *args, timeout=None, **kwargs):
        log.debug("# executing {} in {}\n".format(repr(cmd), kwargs.get('cwd', ".")))

        r = SubmissionResult.SUCCESS
        reasons = []
        try:
            p = subprocess.Popen(cmd, *args, stdin=None,
                                 **kwargs)
            
            output, errout = b"", b""
            
            log.debug(f"Timeout is {timeout}")
            output, errout = p.communicate(timeout=timeout)
            log.info(f"Execution completed with result: {p.returncode}")
            if p.returncode != 0:
                r = SubmissionResult.ERROR
                reasons.append(f"""Execution of {cmd} completed with result {p.returncode}, which usually indicates failure.  Look at STDERR and STDOUT for more information.""")
        except subprocess.TimeoutExpired:
            log.error(f"Execution timed out after {timeout} seconds.")

            # clean up: https://docs.python.org/3/library/subprocess.html
            p.kill()
            output2, errout2 = p.communicate()

            output += output2
            errout += errout2
            
            r = SubmissionResult.TIMEOUT
            reasons.append("Execution of {args} timedout after {timeout} seconds.")
            try:
                subprocess.run(['stty', 'sane']) # Timeouts can leave the terminal in a bad state.  Restore it.
            except:
                pass  # if it doesn't work, it's not a big deal
        except OSError as e:
            r = SubmissionResult.ERROR
            reasons.append(f"An error occcurred while running your program: {repr(e)}.")
            
        if output:
            out.write(output.decode("utf-8"))
        if errout:
            err.write(errout.decode("utf-8"))

        return r, reasons

    @contextmanager
    def directory_or_tmp(d=None):
        if d is not None:
            try:
                yield os.path.abspath(d)
            finally:
                pass
        else:
            r = tempfile.TemporaryDirectory(dir="/tmp/")
            try:
                yield r.name
            finally:
                r.cleanup()

    
    if os.environ.get('IN_DOCKER') == 'yes' and run_in_docker and not run_pristine:
        # the problem here is that when we spawn the new docker image, it's a symbling to this image, and it needs to
        # be able to access the submission.  There's no really reliable way to export the current working directory to
        # the sybling container.  Intsead, we need to clone into /tmp and share /tmp across the syblings, hence, we have
        # to use pristine.
        raise Exception("If you are running in docker, you can only use '--docker' with '--pristine'.  '--local' won't work.")

    # use the existing directory, if we aren't doing a pristine checkout.
    with directory_or_tmp(root if not run_pristine else None) as dirname:
        try:
            if run_pristine:
                repo = sub.lab_spec.repo
                log.debug("Valid repos = {os.environ['VALID_LAB_STARTER_REPOS']}")
                if verify_repo and repo not in os.environ['VALID_LAB_STARTER_REPOS']:
                    raise UserError(f"Repo {repo} is not one of the repos that is permitted for this lab.  You are probably submitting the wrong repo or to the wrong lab.")
                if "GITHUB_OAUTH_TOKEN" in os.environ and "http" in repo:
                    repo = repo.replace("//", f"//{os.environ['GITHUB_OAUTH_TOKEN']}@", 1)
                log.info("Cloning lab reference files...")
                r, reasons = log_run(cmd=['git', 'clone', '-b', sub.lab_spec.reference_tag, repo , dirname])
                if r != SubmissionResult.SUCCESS:
                    raise  ArchlabError(f"Clone for pristine execution failed: {reasons}")

            sub.lab_spec = LabSpec.load(dirname) # distrust submitters spec by loading the pristine one from the newly cloned repo.

            # If we run in a docker, just serialize the submission and pass it via the file system.
            if run_in_docker:
                
                with open(os.path.join(dirname, "job.json"), "w") as job:
                    d = sub._asdict()
                    # we can't be sure where the submission's run
                    # directory is, but that's ok.  The submision has
                    # all the files in it.  What we know for sure is
                    # that dirname is where copy of the lab we should
                    # be using resides, so we can safely use that.
                    d['run_directory'] = dirname 
                    json.dump(d, job, sort_keys=True, indent=4)
                log.info("Docker starts...")
                status, reasons = log_run(cmd=
                                          ["docker", "run",
                                           "--hostname", "runner",
                                           "--volume", f"{dirname}:{dirname}"] + 
                                          (["--volume", "/home/swanson/cse141pp-archlab/archcloud/src:/course/cse141pp-archlab/archcloud/src"] if "USE_LOCAL_ARCHCLOUD" in os.environ else [])+
                                          ["-w", dirname,
                                           "--privileged",
                                           docker_image,
                                           "runlab", "--run-json", "job.json", '--debug', '--json-status', 'status.json', '--directory', dirname] +
                                          (['-v'] if (log.getLogger().getEffectiveLevel() < log.INFO) else []),
                                          timeout=sub.lab_spec.time_limit)
                log.info("Docker finished")

                status_path = os.path.join(dirname, "status.json")
                if os.path.exists(status_path):
                    with open(status_path, "r") as s:
                        json_status = json.loads(s.read())
                        if json_status['exit_code'] != 0:
                            reasons.append(f"From runlab in docker: {json_status['status_str']}")
            else:

                # filter the environment with the clean lab_spec
                log.debug(f"Incoming env: {sub.env}")
                sub.env = sub.lab_spec.filter_env(sub.env)
                good_command, error, sub.command = sub.lab_spec.filter_command(sub.command)
                if not good_command:
                    raise UserError(f"Disallowed command ({error}): {sub.command}")
                log.debug(f"Filtered env: {sub.env}")

                if run_pristine:
                    # we just dumped the files in '.' so, look for them there.
                    sub.env['LAB_SUBMISSION_DIR'] = dirname
                else:
                    with environment(**sub.env):
                        log_run(sub.lab_spec.clean_cmd, cwd=dirname)
                    os.makedirs(os.path.join(dirname, ".tmp"),exist_ok=True)
                    sub.env['LAB_SUBMISSION_DIR'] = ".tmp"

                for f in sub.files:
                    path = os.path.join(dirname, sub.env['LAB_SUBMISSION_DIR'], f)
                    os.makedirs(os.path.dirname(path),exist_ok=True)
                    with open(path, "wb") as of:
                        log.debug("Writing input file {}".format(path))
                        of.write(base64.b64decode(sub.files[f]))

                # Run the job!
                with environment(**sub.env):
                    status, reasons = log_run(sub.command, cwd=dirname, timeout=sub.lab_spec.time_limit)
                
            for f in sub.lab_spec.output_files:
                log.debug(f"Searching for output files matching '{f}'")
                for filename in Path(dirname).glob(f):
                    if os.path.isfile(filename):
                        with open(filename, "rb") as r:
                            key = filename.relative_to(dirname)
                            log.debug(f"Reading output file (storing as '{key}') {filename}.")
                            t = str(key)
                            result_files[t] = base64.b64encode(r.read()).decode('utf8')

        except TypeError:
            raise
        except Exception as e:
            traceback.print_exc(file=err)
            traceback.print_exc()
            err.write("# Execution failed\n")
            out.write("# Execution failed\n")
            status=SubmissionResult.ERROR
            reasons.append(f"Autograder caught an exception during execution.:{repr(e)}.  THis probably a bug or error in the autograder.")
            
        try:
            result_files['STDOUT'] = base64.b64encode(out.getvalue().encode('utf8')).decode('utf8')
            result_files['STDERR'] = base64.b64encode(err.getvalue().encode('utf8')).decode('utf8')
            log.debug("STDOUT: \n{}".format(out.getvalue()))
            log.debug("STDOUT_ENDS")
            log.debug("STDERR: \n{}".format(err.getvalue()))
            log.debug("STDERR_ENDS")
            log.debug(result_files['STDOUT'])
            result = SubmissionResult(sub, result_files, status, reasons)
            sub.lab_spec.run_gradescope_tests(result, dirname)
            if write_outputs:
                result.write_outputs()
        except Exception as e:
            exc_type, exc_value, exc_tb = sys.exc_info()
            log.error("\n".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
            log.error(repr(e))
            result_files['exception'] = base64.b64encode(repr(e).encode('utf8')).decode('utf8')
            result = SubmissionResult(sub,
                                      result_files,
                                      SubmissionResult.ERROR,
                                      [f'Something went wrong while preparing the submission response.  This a bug or error in the autograder: {repr(e)}'])
            
    return result
    

def remove_outputs(dirname, submission):
    for i in submission.lab_spec.output_files:
        if os.path.exists(path) and os.path.isfile(path):
            os.remove(path)
    
def build_submission(user_directory, solution, command, config_file=None, username=None,pristine=False, public_only=False):

    # We default to 'solution' so the autograder will run the solution when we
    # test it with maste repo. Since we delete 'solution' in the starter repo,
    # it will use '.' for the students.
    if solution is None:
        input_dir = "solution" if os.path.isdir("solution") else "."
    else:
        input_dir = os.path.join(".", solution) # this will fail in the path isn't relative.
    os.environ['LAB_SUBMISSION_DIR'] = input_dir

    if pristine:
        run_directory = tempfile.TemporaryDirectory(dir="/tmp/").name
        try:
            log.info("Cloning user files to get the version in github...")
            subprocess.check_call(["git", "clone", user_directory, run_directory])
        except Exception as e:
            log.error(f"Tried to clone `{user_directory}` into '{run_directory}' for pristine execution, but failed: {repr(e)}")
            sys.exit(1)
    else:
        run_directory = user_directory

    spec = LabSpec.load(run_directory, public_only=public_only)
    files = {}
    if config_file is None:
        config_file = spec.config_file

    if not command:
        command = spec.default_cmd
    # check if the command is ok.  We don't recorded the filtered version
    # because the filtered result might not, itself, pass through the filter.
    good_command, error, _ = spec.filter_command(command)
    if not good_command:
        raise UserError(f"This command is not allowed ({error}): {command}")
        
    for f in spec.input_files:
        full_path = os.path.join(run_directory, input_dir)
        log.debug(f"Looking for files matching '{f}' in '{full_path}'.")
        for filename in Path(full_path).glob(f):
            if not  os.path.isfile(filename):
                log.debug(f"Skipping '{filename}' since it's a directory")
                continue
            log.debug(f"Found file '{filename}' matching '{f}'.")
            try:
                with open(filename, "rb") as o:
                    log.debug(f"Reading input file '{filename}'")
                    key = filename.relative_to(full_path)
                    log.debug(f"Storing as '{str(key)}'")
                    files[str(key)] = base64.b64encode(o.read()).decode('utf8')
                    log.info(f"Found input file '{filename}'")
            except Exception:
                raise UserError(f"Couldn't open input file '{filename}'.")

    if config_file:
        path = os.path.join(run_directory,
                            input_dir,
                            config_file)
        with open(path) as config:
            log.debug(f"Parsing config file: '{path}'")
            from_config = spec.parse_config(config)
            for i in from_config:
                log.info(f"From '{path}', loading environment variable '{i}={from_config[i]}'")
    else:
        log.debug("No config file")
        from_config = {}

    from_env = spec.filter_env(os.environ)
    
    for i in from_env:
        from_env[i] = re.sub(r'"|\'', "", from_env[i])
        log.info(f"Copying environment variable '{i}' with value '{from_env[i]}'")
        
    from_config.update(from_env)

    s = Submission(spec, files, from_config, command, run_directory, user_directory, input_dir, username=username)

    return s

    


def test_run():
    sub = build_submission("test_inputs", ".", config_file = "config-good", command=["true"])

    result = run_submission_locally(sub,
                                    run_in_docker = False,
                                    run_pristine = False,
                                    docker_image = None)

    assert set(result.files.keys()) == set(['an_output',
                                            'out1',
                                            'out2',
                                            'STDOUT',
                                            'STDERR'])
    assert result.status == SubmissionResult.SUCCESS

    d = result._asdict()
    j = json.loads(json.dumps(d))
    n = SubmissionResult._fromdict(j)

    result2 = run_submission_locally(sub,
                                     run_in_docker = False,
                                     run_pristine = False,
                                     docker_image = None)

    assert result.files == n.files
    assert result.status == n.status
    assert result.results == n.results

    
def test_lab_spec():
    spec = LabSpec.load("test_inputs")
    d = spec._asdict()
    j = json.loads(json.dumps(d))
    n = LabSpec._fromdict(j)
    for f in spec._fields:
        assert getattr(n, f) == getattr(spec, f), f"Field '{f}' doesn't match";

def test_build_result():
    with environment(FOO="BAR", C_OPTS="yes"):
        sub = build_submission("test_inputs", ".", config_file = "config-good", command=["true"])
        r = SubmissionResult(sub, dict(t="stuff"), SubmissionResult.SUCCESS, [])
        d = r._asdict()
        j = json.loads(json.dumps(d))
        n = SubmissionResult._fromdict(j)

        assert r.status == n.status
        assert r.files == n.files
        
        
def test_build_submission():
    with environment(FOO="BAR", C_OPTS="yes"):
        sub = build_submission("test_inputs", ".", config_file = "config-good", command=["true"])

        assert set(['foo.in',
                    '1.inp',
                    '2.inp',
                    'bar/bang.1',
                    'bar/bang.2'])  == set(map(str,sub.files.keys())), "Didn't find the expected input files"

        assert "JUNK" not in sub.env
        log.debug(f"{os.environ}")
        assert sub.env["C_OPTS"] == "yes"

        d = sub._asdict()
        j = json.loads(json.dumps(d))
        n = Submission._fromdict(j)

        assert sub.env == n.env
        assert sub.files == n.files

        # 'solution' should be a symlink to test_inputs, so the result should
        # be the same even though the file prefix is different.
        sub2 = build_submission("test_inputs", "solution", config_file = "config-good", command=["true"])
        assert set(['foo.in',
                    '1.inp',
                    '2.inp',
                    'bar/bang.1',
                    'bar/bang.2'])  == set(map(str,sub2.files.keys())), "Didn't find the expected input files"
    
    with pytest.raises(ConfigException):
        sub = build_submission("test_inputs", ".", config_file="config-bad", command=["true"])

def test_configs_validation():
        
    def test_good():
        spec = LabSpec.load("test_inputs")
        for f in [
                """
                USER_CMD_LINE2=hello
                GPROF=yes
                DEBUG=no
                DEBUG2=
                """
        ]:
            s = io.StringIO(f)
            env = spec.parse_config(s)
            assert dict(USER_CMD_LINE2="hello",
                        GPROF="yes",
                        DEBUG="no",
                        DEBUG2=""
                        ) == env

    def test_err():
        spec = LabSpec.load("test_inputs")
        for f in ["USER_CMD_LINE=hello;goodbye",
                  "foo=bar",
                  "DEBUG=@",
                  "foo=bar=baz"]:
            s = io.StringIO(f)
            log.debug(f"checking '{f}'")
            with pytest.raises(ConfigException):
                spec.parse_config(s)

    test_good()
    test_err()
        
    
