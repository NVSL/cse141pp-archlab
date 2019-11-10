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

class RunnerException(Exception):
    pass
class BadOptionException(RunnerException):
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

class LabSpec(object):

    required_fields = ["output_files",
                       "input_files",
                       "run_cmd",
                       "repo",
                       "reference_tag"]

    optional_fields = ["clean_cmd",
                       "allowed_env",
                       "lab_name",
                       "test_cmd",
                       "solution",
                       "valid_options",
                       "default_options",
                       "time_limit",
                       "lab_env",
                       #"turnin_files"
    ]
    
    def __init__(self,
                 output_files= None,
                 input_files=None,
                 run_cmd= None,
                 test_cmd= None,
                 repo= None,
                 reference_tag = None,
                 valid_options={},
                 default_options = {},
                 time_limit = 30,
                 solution=".",
                 figures_of_merit = [],
                 clean_cmd=['true'],
                 allowed_env=[],
                 lab_env={},
                 lab_name="<unnamed>"):
    
        for i in LabSpec.required_fields:
            if locals()[i] is None:
                raise Exception(f"lab.py must set ThisLab.{i}")
            else:
                setattr(self, i, locals()[i])
                
        for i in LabSpec.optional_fields:
            setattr(self, i, locals()[i])
                
    def _asdict(self):
        t = {f:getattr(self, f) for f in LabSpec.required_fields + LabSpec.optional_fields}
        t['valid_options'] = {}
        return t;

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
    
    def extract_figures_of_merit(self, result):
        return dict()

    def parse_one_option(self, option, value):
        if option == "cmd_line":
            value = value.strip()
            if re.match("[\w\.\s]*", value):
                return True, True, "simple text", dict(USER_CMD_LINE=value)
            else:
                return self.parse_one_dict_option(option, value)
        elif option == "MHz":
            return True, True, "integer multiples of 100", dict(MHZ=str(int(value)))
        elif option == "optimize":
            value = value.strip();
            if not re.match("[\s\w\-]*", value):
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

    @classmethod
    def _fromdict(cls, j):
        t = cls(**j)
        t.figures_of_merit=[]
        t.valid_options=dict()
        return t

    @classmethod
    def load(cls, root):
        log.debug("Importing {}".format(os.path.join(root, "lab.py")))
        spec = importlib.util.spec_from_file_location("LabInfo", os.path.join(root, "lab.py"))
        lab_info = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lab_info)

        return lab_info.ThisLab()

class Submission(object):

    def __init__(self, lab_spec, files, env, options):
        self.lab_spec = lab_spec
        self.files = files
        self.local_env = env
        self.options = options
        self.env = {}
        
    def _asdict(self):
        return dict(lab_spec=self.lab_spec._asdict(),
                    files=self.files,
                    env=self.env,
                    local_env=self.local_env,
                    options=self.options)

    @classmethod
    def _fromdict(cls, j):
        t = cls(files=j['files'],
                lab_spec=LabSpec._fromdict(j['lab_spec']),
                env=j['env'],
                options=j['options'])
        t.local_env = j['local_env']
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
            m = re.search("(\d+):(\d+)", f)
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

    def __init__(self, submission, files, status):
        self.submission = submission
        self.files = files
        self.status = status
        r = []
        if status == SubmissionResult.SUCCESS:
            try:
                self.figures_of_merit = submission.lab_spec.extract_figures_of_merit(self)
            except KeyError as e:
                self.figures_of_merit={}
                log.warn(f"Couldn't extract figures of merit: {e}")
                
        else:
            self.figures_of_merit ={}

    def _asdict(self):
        return dict(submission=self.submission._asdict(),
                    files=self.files,
                    status=self.status,
                    figures_of_merit=self.figures_of_merit)

    @classmethod
    def _fromdict(cls, j):
        return cls(submission=Submission._fromdict(j['submission']),
                   files=j['files'],
                   status=j['status'],
                   figures_of_merit=j['figures_of_merit'])


def run_submission_remotely(sub, host, port):
    log.debug("Running remotely on {}".format(host))
    r = requests.post("{}/run-job".format(host), data=dict(payload=json.dumps(sub._asdict())))
    log.debug(r.raw.read())
    log.debug(r.json())
    return SubmissionResult._fromdict(r.json())


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

    figures_of_merit = []

    try:
        with directory_or_tmp(root if not run_pristine else None) as dirname:
            if run_pristine:
                log_run(cmd=['git', 'clone', ".", dirname])

            sub.lab_spec = LabSpec.load(dirname) # distrust submitters spec by loading the pristine one from the newly cloned repo.

            # If we run in a docker, just serialize the submission and pass it via the file system.
            if run_in_docker:
                log.debug(f"Executing submission in docker\n{json.dumps(sub._asdict(), sort_keys=True, indent=4)}")
                with open(os.path.join(dirname, "job.json"), "w") as job:
                    json.dump(sub._asdict(), job, sort_keys=True, indent=4)
                status = log_run(cmd=
                                 ["docker", "run",
                                  "--hostname", "runner",
                                  "--privileged",
                                  "-v", f"{dirname}:/runner"] +
                                 # Convenience avoid having to rebuild the docker container
                                 (["-v", f"{os.environ['ARCHLAB_ROOT']}:/cse141pp-archlab"] if os.environ.get("USE_LOCAL_ARCHLAB") is not None else [])+
                                 [docker_image] +
                                 ["run.py", "--run-json", "job.json", "--apply-options"] +
                                 (['-v'] if (log.getLogger().getEffectiveLevel() < log.INFO) else []),
                                 timeout=sub.lab_spec.time_limit)
            else:
                
                if run_pristine:
                    for f in sub.lab_spec.input_files:
                        path = os.path.join(dirname, f)
                        with open(path, "w") as of:
                            log.debug("Writing input file {}".format(path))
                            of.write(sub.files[f])

                log.debug(f"Executing submission\n{json.dumps(sub._asdict(), sort_keys=True, indent=4)}")
                sub.env = {}                         # distrust incoming environment, and recompue
                sub.env.update(sub.lab_spec.lab_env) # lab spec environment
                sub.lab_spec.parse_options(sub)      # config file
                # In theory this was already filtered, but don't trust it.  Filter again.
                sub.env.update(filter_env(sub.lab_spec, sub.local_env))        

                if apply_options:
                    sub.apply_options()

                with environment(**sub.env):
                    status = log_run(sub.lab_spec.run_cmd, cwd=dirname, timeout=sub.lab_spec.time_limit)

            for i in sub.lab_spec.output_files:
                if i in ['STDERR', 'STDOUT']:
                    continue
                path = os.path.join(dirname, i)
                if os.path.exists(path) and os.path.isfile(path):
                    with open(path, "r") as r:
                        log.debug("Reading output file (storing as '{}') {}.".format(i, path))
                        result_files[i] = r.read()
                # else:
                #     result_files[i] = f"<This output file did not exist>"
                #     if status == SubmissionResult.SUCCESS:
                #         status = SubmissionResult.MISSING_OUTPUT
    except BadOptionException as e:
        # if the get this, just fail, rather than exiting cleanly.
        raise
    except Exception:
        traceback.print_exc(file=err)
        traceback.print_exc()
        err.write("# Execution failed\n")
        out.write("# Execution failed\n")
        status=SubmissionResult.ERROR

    result_files['STDOUT'] = out.getvalue()
    result_files['STDERR'] = err.getvalue()
    log.debug("STDOUT: {}".format(out.getvalue()))
    log.debug("STDERR: {}".format(err.getvalue()))
    return SubmissionResult(sub, result_files, status)


def remove_outputs(dirname, submission):
    for i in submission.lab_spec.output_files:
        if os.path.exists(path) and os.path.isfile(path):
            os.remove(path)

def filter_env(spec, env):
    out = {}
    for e in spec.allowed_env:
        if e in env:
            v = env[e]
            safe_env = "[a-zA-Z0-9_\-\. ]"
            if not re.match(f"^{safe_env}*$", v):
                raise Exception(f"Environment variable '{e}' has a potentially unsafe value: '{v}'.  Imported environment variables can only contain charecters from {safe_env}.")
            out[e] = env[e]
    return out

def build_submission(directory, input_dir, options, config_file):
    spec = LabSpec.load(directory)
    files = {}

    for f in spec.input_files:
        full_path = os.path.join(directory, input_dir, f)
        try:
            with open(full_path, "r") as o:
                log.debug(f"Reading input file '{full_path}'")
                files[f] = o.read()
        except Exception:
            log.error(f"Failed to open {full_path}")
            sys.exit(1)

    env = filter_env(spec, os.environ)

    options_dict = {}
    
    with open(os.path.join(directory,
                           input_dir,
                           config_file)) as config:
        for l in config.readlines():
            l = re.sub("#.*", "", l)
            l = l.strip()
            if l:
                log.debug(f"parsing option {l} from config file")
                k,v = l.split("=", maxsplit=1)
                options_dict[k.strip()] = v.strip()

    if options: # THis is a hack to force make to rerun rules that depend on changes to the config file.
        Path(config_file).touch()

    log.debug(f"--config options are: {options}")
    for o in options:
        log.debug(f"parsing option {o} from command line")
        k,v = o.split("=", maxsplit=1)
        options_dict[k.strip()] = v.strip()

    s = Submission(spec, files, env, options_dict)
    return s
