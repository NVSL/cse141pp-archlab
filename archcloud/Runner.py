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


class RunnerException(Exception):
    pass
class BadOptionException(RunnerException):
    pass
class ConfigException(Exception):
    pass


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
                 output_files= None,
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
                
    def _asdict(self):
        return {f:getattr(self, f) for f in self._fields}

    # there no reason for these to be methods of this class
    
    def csv_extract_by_line(self, file_contents, field, line=0):
        reader = csv.DictReader(StringIO(file_contents))
        d = list(reader)
        if len(d) < line + 1:
            return None
        return float(d[line][field])

    def csv_extract_by_lookup(self, file_contents, field, column, value):
        reader = csv.DictReader(StringIO(file_contents))
        d = list(reader)
        r = None
        for l in d:
            if l[column] == value:
                if r == None:
                    r = float(l[field])
                else:
                    raise Exception(f"Multiple lines in output have {column}=={value}")
        return r
    
    def csv_column_values(self, file_contents, field):
        reader = csv.DictReader(StringIO(file_contents))
        return map(lambda x: x[field], reader)
    
    def post_run(self, result):
        return result

    def parse_one_option(self, option, value):
        if option == "cmd_line":
            value = value.strip()
            if re.match(r"[\w\.\s]*", value):
                return True, True, "simple text", dict(USER_CMD_LINE=value)
            else:
                return self.parse_one_dict_option(option, value)
        elif option == "MHz":
            return True, True, "integer multiples of 100", dict(MHZ=str(int(value)))
        elif option == "optimize":
            value = value.strip();
            if not re.match(r"[\s\w\-]*", value):
                return True, False, "Compiler optimization flags", {}
            else:
                return True, True, "Compiler optimization flags", dict(C_OPTS=value)
        elif option == "profiler":
            if value == 'gprof':
                return True, True, "gprof", dict(GPROF="yes")
            else:
                return True, False, "gprof", {}
        else:
            return self.parse_one_dict_option(option, value)

    def parse_one_dict_option(self, option, value):
        if option not in self.valid_options:
            return False, False, "", {}
        if value not in self.valid_options[option]:
            return True, False, ", ".join(self.valid_options[k].keys()), {}
        return True, True,  ", ".join(self.valid_options[option].keys()), self.valid_options[option][value]

    def parse_options(self, submission):
        log.debug(f"Parsing options {submission.options}")
        log.debug(f"Using option spec {self.valid_options}")
        valid_options = self.valid_options

        for k, v in list(submission.options.items()) + list(self.default_options.items()):
            valid_option_name, valid_value, valid_option_values, env = self.parse_one_option(k, v)
            if not valid_option_name:
                raise Exception(f"Illegal config file option '{k}'")
            if not valid_value:
                raise Exception(f"Illegal config file value '{v}' for option '{k}'")
            log.debug(f"Parsed option {k}={v} and added {env} into environment")
            submission.env.update(env)

        log.debug(f"New environment {submission.env}.")

        
    def safe_env_value(self, v):
        safe_env = r"[a-zA-Z0-9_\-\. \"\']"
        if not re.match(fr"^{safe_env}*$", v):
            return False
        else:
            return True
        
    def parse_config(self, f):
        r = dict()
        for l in f.readlines():
            l = re.sub(r"#.*", "", l)
            l = l.strip()
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
        t = cls(**j)
        return t

    @classmethod
    def load(cls, root):
        log.debug("Importing {}".format(os.path.join(root, "lab.py")))
        spec = importlib.util.spec_from_file_location("LabInfo", os.path.join(root, "lab.py"))
        lab_info = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lab_info)

        return lab_info.ThisLab()

class Submission(object):

    def __init__(self, lab_spec, files, env, command):
        self.lab_spec = lab_spec
        self.files = files
        self.env = env
        self.command = command
        
    def _asdict(self):
        return dict(lab_spec=self.lab_spec._asdict(),
                    files=self.files,
                    env=self.env,
                    command=self.command)

    @classmethod
    def _fromdict(cls, j):
        t = cls(**j)
        t.lab_spec = LabSpec(**t.lab_spec)
        return t

    def apply_options(self):
        if subprocess.call(['which', 'cpupower']) != 0:
            log.warning("cpupower utility is not available.  Clock speed setting will not work.")
            return

        try:
            o = subprocess.check_output(["cpupower", "frequency-info", "-s"]).decode("utf-8").split("\n")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Calling 'cpupower' to extract frequency list failed: {e}")

        if "analyzing CPU" not in o[0]:
            raise Exception("Error running cpu power to extract available frequencies")

        fields = o[1].split(", ")
        frequencies = []
        for f in fields:
            m = re.search(r"(\d+):(\d+)", f)
            if not m:
                raise Exception(f"Failed to parse output from cpupower: {f}")
            f = int(int(m.group(1))/1000)
            if f % 10 == 0: # Sometimes the list includes things like 2001Mhz, but they don't seem to actually valid values, so trim them.
                frequencies.append(f)
            
        self.env["ARCHLAB_AVAILABLE_CPU_FREQUENCIES"] = " ".join(map(str, frequencies))

        if "MHz" in self.env:
            if int(self.env['MHz']) not in frequencies:
                raise Exception(f"Unsupported frequency in 'MHz': {self.env['MHz']}")
            target_MHz = self.env['MHz']
        else:
            target_MHz = max(frequencies)

        try:
            subprocess.check_output(["cpupower", "frequency-set", "--freq", f"{target_MHz}MHz"]).decode("utf-8").split("\n")
            o = subprocess.check_output(["/usr/bin/cpupower", "frequency-info", "-w"]).decode("utf-8").split("\n")
            if f"{target_MHz}000" not in o[1]:
                raise Exception(f"Calling 'cpupower' to set frequency to {target_MHz}MHz failed: {o[1]}.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Calling 'cpupower' to set frequency to {target_MHz}MHz failed: {e}")

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

    def __init__(self, submission, files, status, results=None):
        self.submission = submission
        self.files = files
        self.status = status
        if results is None:
            self.results = {}
        else:
            self.results = results
            
    def _asdict(self):
        return dict(submission=self.submission._asdict(),
                    files=self.files,
                    status=self.status,
                    results=self.results)

    @classmethod
    def _fromdict(cls, j):
        t = cls(**j)
        t.submission = Submission(**t.submission)
        return cls(**j)


def run_submission_locally(sub, root=".",
                           run_in_docker=False,
                           run_pristine=False,
                           nop=False,
                           timeout=None,
                           apply_options=False,
                           docker_image=None):
    out = StringIO()
    err = StringIO()
    result_files = {}

    def log_run(cmd, *args, timeout=None, **kwargs):
        log.debug("# executing {} in {}\n".format(repr(cmd), kwargs.get('cwd', ".")))

        r = SubmissionResult.SUCCESS

        p = subprocess.Popen(cmd, *args, stdin=None,
                             **kwargs)

        output, errout = b"", b""

        log.debug(f"Timeout is {timeout}")
        try:
            output, errout = p.communicate(timeout=timeout)
            log.info(f"Execution completed with result: {p.returncode}")
            if p.returncode != 0:
                r = SubmissionResult.ERROR
                
        except subprocess.TimeoutExpired:
            log.error(f"Execution timed out after {timeout} seconds.")

            # clean up: https://docs.python.org/3/library/subprocess.html
            p.kill()
            output, errout = p.communicate()
            
            r = SubmissionResult.TIMEOUT
            try:
                subprocess.run(['stty', 'sane']) # Timeouts can leave the terminal in a bad state.  Restore it.
            except:
                pass  # if it doesn't work, it's not a big deal

        if output:
            out.write(output.decode("utf-8"))
        if errout:
            err.write(errout.decode("utf-8"))

        return r

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

    status = SubmissionResult.ERROR
    
    if os.environ.get('IN_DOCKER') == 'yes' and run_in_docker and not run_pristine:
        # the problem here is that when we spawn the new docker image, it's a symbling to this image, and it needs to
        # be able to access the submission.  There's no really reliable way to export the current working directory to
        # the sybling container.  Intsead, we need to clone into /tmp and share /tmp across the syblings, hence, we have
        # to use pristine.
        raise Exception("If you are running in docker, you can only use '--docker' with '--pristine'.  '--local' won't work.")

    try:
        with directory_or_tmp(root if not run_pristine else None) as dirname:
            if run_pristine:
                log_run(cmd=['git', 'clone', ".", dirname])

            sub.lab_spec = LabSpec.load(dirname) # distrust submitters spec by loading the pristine one from the newly cloned repo.

            # If we run in a docker, just serialize the submission and pass it via the file system.
            if run_in_docker:
                log.debug(f"Executing submission in docker\n{sub._asdict()}")
                with open(os.path.join(dirname, "job.json"), "w") as job:
                    json.dump(sub._asdict(), job, sort_keys=True, indent=4)
                status = log_run(cmd=
                                 ["docker", "run",
                                  "--hostname", "runner",
                                  "--privileged",
                                  "-v", f"{dirname}:/runner"] +
                                 # Convenience avoid having to rebuild the docker container
                                 (["-v", f"{os.environ['ARCHLAB_ROOT']}:/cse141pp-archlab"] if os.environ.get("USE_LOCAL_ARCHLAB") is not None else [])+
                                 (["-v", f"{os.environ['CANELA_ROOT']}:/CSE141pp-SimpleCNN"] if os.environ.get("USE_LOCAL_ARCHLAB") is not None else [])+
                                 [docker_image] +
                                 ["run.py", "--run-json", "job.json"] +
                                 (['-v'] if (log.getLogger().getEffectiveLevel() < log.INFO) else []),
                                 timeout=sub.lab_spec.time_limit)
            else:
                if run_pristine:
                    for f in sub.files:
                        path = os.path.join(dirname, f)
                        with open(path, "wb") as of:
                            log.debug("Writing input file {}".format(path))
                            of.write(base64.b64decode(sub.files[f]))

                
                log.debug(f"Executing submission\n{sub._asdict()}")

                # filter the environment with the clean lab_spec
                log.debug(f"Incomming env: {sub.env}")
                sub.env = sub.lab_spec.filter_env(sub.env)
                good_command, error, sub.command = sub.lab_spec.filter_command(sub.command)
                if not good_command:
                    raise Exception(f"Disallowed command ({error}): {sub.command}")
                
                if run_pristine:
                    # we just dumped the files in '.' so, look for them there.
                    sub.env['LAB_SUBMISSION_DIR'] = "." 
                log.debug(f"Filtered env: {sub.env}")
                with environment(**sub.env):
                    log_run(sub.lab_spec.clean_cmd, cwd=dirname)
                    status = log_run(sub.command, cwd=dirname, timeout=sub.lab_spec.time_limit)
                
            for f in sub.lab_spec.output_files:
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

    result_files['STDOUT'] = out.getvalue()
    result_files['STDERR'] = err.getvalue()
    log.debug("STDOUT: {}".format(out.getvalue()))
    log.debug("STDERR: {}".format(err.getvalue()))
    result = SubmissionResult(sub, result_files, status)
    return sub.lab_spec.post_run(result)
    


def remove_outputs(dirname, submission):
    for i in submission.lab_spec.output_files:
        if os.path.exists(path) and os.path.isfile(path):
            os.remove(path)
    
def build_submission(directory, input_dir, command, config_file=None):
    spec = LabSpec.load(directory)
    files = {}
    if config_file is None:
        config_file = spec.config_file

    if not command:
        command = spec.default_cmd
    # check if the command is ok.  We don't recorded the filtered version
    # because the filtered result might not, itself, pass through the filter.
    good_command, error, _ = spec.filter_command(command)
    if not good_command:
        raise Exception(f"This command is not allowed ({error}): {command}")
        
    for f in spec.input_files:
        full_path = os.path.join(directory, input_dir)
        for filename in Path(full_path).glob(f):
            log.debug(f"Found file '{filename}' matching '{f}'.")
            try:
                with open(filename, "rb") as o:
                    log.debug(f"Reading input file '{filename}'")
                    key = filename.relative_to(full_path)
                    log.debug(f"Storing as '{str(key)}'")
                    files[str(key)] = base64.b64encode(o.read()).decode('utf8')
                    log.info(f"Found input file '{filename}'")
            except Exception:
                raise Exception(f"Couldn't open input file '{filename}'.")

    from_env = spec.filter_env(os.environ)
    for i in from_env:
        log.info(f"Copying environment variable '{i}' with value '{from_env[i]}'")
        
    if config_file:
        path = os.path.join(directory,
                            input_dir,
                            config_file)
        with open(path) as config:
            from_config = spec.parse_config(config)
            for i in from_config:
                log.info(f"From '{Path(path).relative_to('.')}', loading environment variable '{i}={from_config[i]}'")
    else:
        from_config = {}
        
    from_env.update(from_config)

    s = Submission(spec, files, from_env, command)
    return s


def test_run():
    sub = build_submission("test_inputs", ".", config_file = "config-good", command=["true"])

    result = run_submission_locally(sub,
                                    "test_inputs",
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

    result2 = run_submission_locally(n,
                                     "test_inputs",
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
                USER_CMD_LINE=hello
                USER_CMD_LINE2=hello
                USER_CMD_LINE=--stat foo bar "baoeu aoue"
                GPROF=yes
                DEBUG=no
                DEBUG2=
                """
        ]:
            s = io.StringIO(f)
            env = spec.parse_config(s)
            assert dict(USER_CMD_LINE2="hello",
                        USER_CMD_LINE='--stat foo bar "baoeu aoue"',
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
        
    
