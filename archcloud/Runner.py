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
                       "env",
                       "lab_name",
                       "valid_options",
                       "default_options",
                       "time_limit",
                       "figures_of_merit"]
    
    def __init__(self,
                 output_files= None,
                 input_files=None,
                 run_cmd= None,
                 repo= None,
                 reference_tag = None,
                 valid_options={},
                 default_options = {},
                 time_limit = 30,
                 figures_of_merit = [],
                 clean_cmd=['true'],
                 env=[],
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
        t['figures_of_merit'] = {}
        return t;

    def csv_extract_by_line(self, file_contents, field, line=0):
        reader = csv.DictReader(StringIO(file_contents))
        d = list(reader)
        if len(d) < line + 1:
            return None
        return float(d[line][field])

    def csv_extract_by_lookup(self, file_contents, field, tag, value):
        reader = csv.DictReader(StringIO(file_contents))
        d = list(reader)
        r = None
        for l in d:
            if l[tag] == value:
                if r == None:
                    r = float(l[field])
                else:
                    raise Exception(f"Multiple lines in output have {tag}=={value}")
        return r
    
    def extract_figures_of_merit(self, result):
        return dict()

    def parse_options(self, submission):
        log.debug(f"Parsing options {submission.options}")
        log.debug(f"Using option spec {self.valid_options}")
        valid_options = self.valid_options

        for k, v in list(submission.options.items()) + list(self.default_options.items()):
            if k not in valid_options:
                raise BadOptionException(f"Illegal user option '{k}'. Valid options are {list(valid_options.keys())}")
            if callable(valid_options[k]):
                continue
            if v not in valid_options[k]:
                raise BadOptionException(f"Illegal value '{v}' for user options '{k}'. Valid values are {list(valid_options[k].keys())}")
            log.debug(f"Adding {valid_options[k][v]} to env")

        def update_env(k, v):
            if callable(valid_options[k]):
                submission.env.update(valid_options[k](v))
            else:
                submission.env.update(valid_options[k][v])

        for k, v in submission.options.items():
            update_env(k, v)

        for k, v in self.default_options.items():
            if k not in submission.options:
                update_env(k, v)

        log.debug(f"New environment {submission.env}.")

    @classmethod
    def _fromdict(cls, j):
        t = cls(**j)
        t._replace(figures_of_merit=[])
        t._replace(valid_options=dict())
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
        self.env = env
        self.options = options

    def _asdict(self):
        return dict(lab_spec=self.lab_spec._asdict(),
                    files=self.files,
                    env=self.env,
                    options=self.options)

    @classmethod
    def _fromdict(cls, j):
        return cls(files=j['files'],
                   lab_spec=LabSpec._fromdict(j['lab_spec']),
                   env=j['env'],
                   options=j['options'])


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
        self.figures_of_merit = submission.lab_spec.extract_figures_of_merit(self)

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


def run_submission_locally(sub, root=".", run_in_docker=False, run_pristine=False, nop=False, timeout=None, apply_options=False):
    out = StringIO()
    err = StringIO()
    result_files = {}

    def log_run(cmd, *args, timeout=None, **kwargs):
        log.debug("# executing {} in {}\n".format(repr(cmd), kwargs.get('cwd', ".")))

        r = SubmissionResult.SUCCESS

        p = subprocess.Popen(cmd, *args, stdin=None,
                             **kwargs)

        output, errout = b"", b""

        try:
            output, errout = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            log.error(f"Execution timed out.")
            p.kill()
            output, errout = p.communicate()
            r = SubmissionResult.TIMEOUT
            try:
                subprocess.run(['stty', 'sane']) # Timeouts often leaves the terminal in a bad state.  Restore it.
            except:
                pass  # if it doesn't work, it's not a big deal

        if output:
            out.write(output.decode("utf-8"))
        if errout:
            err.write(errout.decode("utf-8"))

        return r

    @contextmanager
    def directory(d=None):
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
        with directory(root if not run_pristine else None) as dirname:
            if run_pristine:
                log_run(cmd=['git', 'clone', sub.lab_spec.repo, dirname])

            spec = LabSpec.load(dirname) # distrust submitters spec by loading the pristine one from the newly cloned repo.
            sub.lab_spec = spec
            sub.lab_spec.parse_options(sub)

            if apply_options:
                sub.apply_options()

            log.debug(f"Executing submission {sub._asdict()}")
            if run_pristine:
                for f in spec.input_files:
                    path = os.path.join(dirname, f)
                    with open(path, "w") as of:
                        log.debug("Writing input file {}".format(path))
                        of.write(sub.files[f])

            if run_in_docker:
                image = "devonmerrill/cse141l-development-environment"
                status = log_run(cmd=["docker", "run",  "-it", "--privileged", "-v", f"{dirname}:/runner", image, "run.py", "--local", "--no-validate", "--apply-options"] + (['-v'] if (log.getLogger().getEffectiveLevel() <= log.INFO) else []), timeout=spec.time_limit)
            else:
                with environment(**sub.env):
                    status = log_run(spec.run_cmd, cwd=dirname, timeout=spec.time_limit)

            for i in spec.output_files:
                if i in ['STDERR', 'STDOUT']:
                    continue
                path = os.path.join(dirname, i)
                if os.path.exists(path) and os.path.isfile(path):
                    with open(path, "r") as r:
                        log.debug("Reading output file (storing as '{}') {}.".format(i, path))
                        result_files[i] = r.read()
                else:
                    result_files[i] = f"<This output file did not exist>"
                    if status == SubmissionResult.SUCCESS:
                        status = SubmissionResult.MISSING_OUTPUT
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


def build_submission(directory, options):
    spec = LabSpec.load(directory)
    files = {}
    for f in spec.input_files:
        full_path = os.path.join(directory, f)
        try:
            with open(full_path, "r") as o:
                log.debug(f"Reading input file '{full_path}'")
                files[f] = o.read()
        except Exception:
            log.error(f"Failed to open {full_path}")
            sys.exit(1)
    env = {}
    for e in spec.env:
        if e in os.environ:
            v = os.environ[e]
            safe_env = "[a-zA-Z0-9_\-\. ]"
            if not re.match(f"^{safe_env}*$", v):
                raise Exception(f"Environment variable '{e}' has a potentially unsafe value: '{v}'.  Imported environment variables can only contain charecters from {safe_env}.")
            env[e] = os.environ[e]

    options_dict = {}

    with open("config") as config:
        for l in config.readlines():
            l = re.sub("#.*", "", l)
            l = l.strip()
            if l:
                log.debug(f"parsing option {o} from config file")
                k,v = l.split("=", maxsplit=1)
                options_dict[k] = v
            
    for o in options:
        log.debug(f"parsing option {o} from command line")
        k,v = o.split("=", maxsplit=1)
        options_dict[k] = v

    s = Submission(spec, files, env, options_dict)
    return s
