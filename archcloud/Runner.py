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

@contextmanager
def environment(**kwds):
    env = copy.deepcopy(os.environ)
    os.environ.update(**kwds)
    try:
        yield None
    finally:
        os.environ.clear()
        os.environ.update(env)

class LabSpec(collections.namedtuple("LabSpecBase", "repo output_files input_files run_cmd clean_cmd env lab_name valid_options default_options reference_tag time_limit")):

    Field = collections.namedtuple("Field", "required default")
    fields = dict(
        output_files=Field(True, None),
        input_files=Field(True, None),
        run_cmd=Field(True, None),
        clean_cmd=Field(False, ['true']),
        env=Field(False, []),
        repo=Field(True, None),
        lab_name=Field(False, "<unnamed>"),
        valid_options=Field(False, {}),
        default_options = Field(False, {}),
        reference_tag = Field(True, None),
        time_limit = Field(False, 30)
    )

    def _asdict(self):
        t = super(LabSpec, self)._asdict()
        t['valid_options'] = {}
        return super(LabSpec, LabSpec(**t))._asdict()

    @classmethod
    def _fromdict(cls, j):
        return cls(**j)

    @classmethod
    def load(cls, root):
        log.debug("Importing {}".format(os.path.join(root, "lab.py")))
        spec = importlib.util.spec_from_file_location("LabInfo", os.path.join(root, "lab.py"))
        lab_info = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lab_info)

        args = dict()
        for i in LabSpec.fields:
            try:
                args[i] = getattr(lab_info, i)
            except AttributeError as e:
                if LabSpec.fields[i].required:
                    raise Exception(f"Your lab spec is missing '{i}'")
                else:
                    args[i] = copy.deepcopy(LabSpec.fields[i].default)

        return cls(**args)



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

    def parse_options(self):
        log.debug(f"Parsing options {self.options}")
        log.debug(f"Using option spec {self.lab_spec.valid_options}")
        valid_options = self.lab_spec.valid_options

        for k, v in list(self.options.items()) + list(self.lab_spec.default_options.items()):
            if k not in valid_options:
                raise Exception(f"Illegal user option '{k}'. Valid options are {list(valid_options.keys())}")
            if callable(valid_options[k]):
                continue
            if v not in valid_options[k]:
                raise Exception(f"Illegal value '{v}' for user options '{k}'. Valid values are {list(valid_options[k].keys())}")
            log.debug(f"Adding {valid_options[k][v]} to env")

        def update_env(k, v):
            if callable(valid_options[k]):
                self.env.update(valid_options[k](v))
            else:
                self.env.update(valid_options[k][v])

        for k, v in self.options.items():
            update_env(k, v)

        for k, v in self.lab_spec.default_options.items():
            if k not in self.options:
                update_env(k, v)

        log.debug(f"New environment {self.env}.")

    def apply_options(self):
        if subprocess.call(['which', 'cpupower']) != 0:
            log.warning("cpupower utility is not available.  Clock speed setting will not work.")
            return

        try:
            o = subprocess.check_output(["cpupower", "frequency-info", "-s"]).split("\n")
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
            frequencies.append(int(m.group(1))/1000)

        self.env['AVAILABLE_FREQUENCIES'] = " ".join(map(str, frequencies))

        if "MHz" in self.env:
            if int(self.env['MHz']) not in frequencies:
                raise Exception(f"Unsupported frequency in 'MHz': {self.env['MHz']}")
            target_MHz = self.env['MHz']
        else:
            target_MHz = max(frequencies)

        try:
            subprocess.check_output(["cpupower", "frequency-set", "--freq", f"{target_MHz}MHz"]).split("\n")
            o = subprocess.check_output(["/usr/bin/cpupower", "frequency-info", "-w"]).split("\n")
            if f"{target_MHz}000" not in o[1]:
                raise Exception(f"Calling 'cpupower' to set frequency to {target_MHz}MHz failed.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Calling 'cpupower' to set frequency to {target_MHz}MHz failed: {e}")


class SubmissionResult(object):
    SUCCESS = "success"
    TIMEOUT = "timeout"

    def __init__(self, submission, files, status):
        self.submission = submission
        self.files = files
        self.status = status

    def _asdict(self):
        return dict(submission=self.submission._asdict(),
                    files=self.files,
                    status=self.status)

    @classmethod
    def _fromdict(cls, j):
        return cls(submission=Submission._fromdict(j['submission']),
                   files=j['files'],
                   status=j['status'])


def run_submission_remotely(sub, host, port):
    log.debug("Running remotely on {}".format(host))
    r = requests.post("{}/run-job".format(host), data=dict(payload=json.dumps(sub._asdict())))
    log.debug(r.raw.read())
    log.debug(r.json())
    return SubmissionResult._fromdict(r.json())


def run_submission_locally(sub, root=".", in_docker=False, run_pristine=False, nop=False, timeout=None, apply_options=False):
    out = StringIO()
    err = StringIO()
    result_files = {}

    def log_run(cmd, *args, timeout=None, **kwargs):
        m = "# executing {} in {}\n".format(repr(cmd), kwargs.get('cwd', "."))
        #out.write(m)
        #err.write(m)
        log.debug(m)

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



    try:
        with directory(root if not run_pristine else None) as dirname:
            if run_pristine:
                log_run(cmd=['git', 'clone', sub.lab_spec.repo, dirname])

            spec = LabSpec.load(dirname) # distrust submitters spec by loading the pristine one from the newly cloned repo.
            sub.lab_spec = spec
            sub.parse_options()
            if apply_options:
                sub.apply_options()

            log.debug(f"Executing submission {sub._asdict()}")
            if run_pristine:
                for f in spec.input_files:
                    path = os.path.join(dirname, f)
                    with open(path, "w") as of:
                        log.debug("Writing input file {}".format(path))
                        of.write(sub.files[f])

            if in_docker:
                image = "cse141pp/submission-runner:0.10"
                status = log_run(cmd=["docker", "run",  "-it", "--privileged", "-v", f"{dirname}:/runner", image, "run.py", "--local", "--no-validate", "--apply-options"], timeout=spec.time_limit)
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

    except Exception:
        traceback.print_exc(file=err)
        traceback.print_exc()
        err.write("# Execution failed\n")
        out.write("# Execution failed\n")
    finally:
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
    for o in options:
        log.debug(f"parsing option {o}")
        k,v = o.split("=", maxsplit=1)
        options_dict[k] = v

    s = Submission(spec, files, env, options_dict)
    return s
