#!/usr/bin/env python3

import argparse
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
import docker
client = docker.from_env()
import docker.types

@contextmanager
def environment(**kwds):
    env = copy.deepcopy(os.environ)
    os.environ.update(**kwds)
    try:
        yield None
    finally:
        os.environ.clear()
        os.environ.update(env)

class LabSpec(collections.namedtuple("LabSpecBase", "repo output_files input_files cmd env")):

    @classmethod
    def _fromdict(cls, j):
        return cls(**j)


class Submission(object):
    def __init__(self, lab_spec, files, env):
        self.lab_spec = lab_spec
        self.files = files
        self.env = env

    def _asdict(self):
        return dict(lab_spec=self.lab_spec._asdict(),
                    files=self.files,
                    env=self.env)

    @classmethod
    def _fromdict(cls, j):
        return cls(files=j['files'],
                   lab_spec=LabSpec._fromdict(j['lab_spec']),
                   env=j['env'])

class SubmissionResult(object):
    def __init__(self, submission, files):
        self.submission = submission
        self.files = files

    def _asdict(self):
        return dict(submission=self.submission._asdict(),
                    files=self.files)

    @classmethod
    def _fromdict(cls, j):
        return cls(submission=Submission._fromdict(j['submission']),
                   files=j['files'])


def load_lab_spec(root):
    log.debug("Importing {}".format(os.path.join(root, "lab.py")))
    spec = importlib.util.spec_from_file_location("LabInfo", os.path.join(root, "lab.py"))
    lab_info = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lab_info)
    return LabSpec(
                   output_files=lab_info.output_files + ['STDOUT', 'STDERR'],
                   input_files=lab_info.input_files,
                   cmd=lab_info.cmd,
                   env=lab_info.env,
                   repo=lab_info.base_repo)


def run_submission_remotely(sub, host, port):
    log.debug("Running remotely on {}".format(host))
    r = requests.post("{}/run-job".format(host), data=dict(payload=json.dumps(sub._asdict())))
    log.debug(r.raw.read())
    log.debug(r.json())
    return SubmissionResult._fromdict(r.json())

def run_submission_in_docker(sub):
    pass
#    docker
#    run - it - p
#    5000: 5000 - v $ARCHLAB_ROOT: / runner
#    cse141pp / submission - runner: 0.10
#    bash - c
#    '. env.sh; cd archcloud/test_lab; ../run.py --local'    pass


def run_submission_locally(sub, in_docker=False, run_pristine=False):
    out = StringIO()
    err = StringIO()
    result_files = {}

    def log_run(cmd, *args, **kwargs):
        m = "# executing {} in {}\n".format(repr(cmd), kwargs.get('cwd', "."))
        #out.write(m)
        #err.write(m)
        log.debug(m)

        #subprocess.call(cmd, *args, stdout=None, stderr=err, **kwargs)
        p = subprocess.Popen(cmd, *args, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        output, errout = p.communicate()
        out.write(output.decode("utf-8"))
        err.write(errout.decode("utf-8"))
        #   rc = p.returncode

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
        with directory("." if not run_pristine else None) as dirname:
            if run_pristine:
                log_run(cmd=['git', 'clone', sub.lab_spec.repo, dirname])

            spec = load_lab_spec(dirname) # distrust submitters spec by loading the pristine one from the newly cloned repo.
            sub.lab_spec = spec

            if run_pristine:
                for f in spec.input_files:
                    path = os.path.join(dirname, f)
                    with open(path, "w") as of:
                        log.debug("Writing input file {}".format(path))
                        of.write(sub.files[f])

            if in_docker:
                image = "cse141pp/submission-runner:0.10"
                log_run(cmd=["docker", "run",  "-v", f"{dirname}:/runner", image, "run.py", "--local"])
            else:
                with environment(**sub.env):
                    log_run(spec.cmd, cwd=dirname)

            for i in spec.output_files:
                if i in ['STDERR', 'STDOUT']:
                    continue
                path = os.path.join(dirname, i)
                if os.path.exists(path) and os.path.isfile(path):
                    with open(path, "r") as r:
                        log.debug("Reading output file (storing as '{}') {}.".format(i, path))
                        result_files[i] = r.read()

    except Exception as e:
        traceback.print_exc(file=err)
        traceback.print_exc()
        err.write("# Execution failed\n")
        out.write("# Execution failed\n")
    finally:
        result_files['STDOUT'] = out.getvalue()
        result_files['STDERR'] = err.getvalue()
        log.debug("STDOUT: {}".format(out.getvalue()))
        log.debug("STDERR: {}".format(err.getvalue()))
        return SubmissionResult(sub, result_files)

def main(argv):
    parser = argparse.ArgumentParser(description='Run a lab.')
    parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")
    parser.add_argument('--pristine', action='store_true', default=False, help="Run job locally")
    parser.add_argument('--remote', default="http://localhost:5000", help="Run remotely on this host")
    parser.add_argument('--docker', action='store_true', default=False, help="Run in a docker container.")
    parser.add_argument('--local', action='store_true', default=True, help="Run locally in this directory.")
#    parser.add_argument('--repo', help="git repo")
    args = parser.parse_args(argv)
    log.basicConfig(format="%(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s" if args.verbose else "%(message)s",
                    level=log.DEBUG if args.verbose else log.INFO)

    spec = load_lab_spec(".")

    files = {}
    for f in spec.input_files:
        try:
            with open(f, "r") as o:
                log.debug("Reading input file '{}'".format(f))
                files[f] = o.read()
        except Exception as e:
            log.error("Failed to open {}".format(f))
            sys.exit(1)

    env = {}
    for e in spec.env:
        if e in os.environ:
            env[e] = os.environ[e]

    s = Submission(spec, files, env)

    log.debug("Submission: {}".format(s._asdict()))
    log.debug("Submission: {}".format(json.dumps(s._asdict())))

    if args.local:
        result = run_submission_locally(s, in_docker=args.docker, run_pristine=args.pristine)
    else:
        result = run_submission_remotely(s, args.remote, "5000")

    for i in spec.output_files:
        if i in result.files:
            log.debug("========================= {} ===========================".format(i))
            log.debug(result.files[i])
            if i == "STDERR":
                sys.stderr.write(result.files[i])
            elif i == "STDOUT":
                sys.stdout.write(result.files[i])
            else:
                with open(i, "w") as t:
                    t.write(result.files[i])

    log.info("Finished")
if __name__ == '__main__':
    main(sys.argv[1:])