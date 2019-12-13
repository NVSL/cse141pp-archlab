from .Runner import LabSpec, build_submission, run_submission_locally, run_submission_remotely, environment
import unittest
import logging as log
import os
import sys
import subprocess
import time
import inspect

# this is for parameterizing tests
def crossproduct(a,b):
    r = []
    for i in a:
        for j in b:
            r.append(list(i) + list(j))
    return r


# These are the flag settings we check
#              pristine devel gprof remote
test_flags = [(False, False, False, False),
              (True,  False, False, False),
              (False, True,  False, False),
              (False, False, True,  False),
              (False, False, False, True ), 
              (False, True,  True,  False), # Local perf tuning
              (True , False, True,  True ), # typical autograder run
              (True , True,  True,  True )]

class CSE141Lab(LabSpec):
    def __init__(self,
                 lab_name,
                 short_name,
                 output_files,
                 input_files,
                 repo,
                 reference_tag,
                 default_cmd=None,
                 clean_cmd=None,
                 valid_options=None,
                 timeout=20
    ):
        if default_cmd == None:
            default_cmd = ['make']
        if clean_cmd == None:
            clean_cmd = ['make', 'clean']
        if valid_options == None:
            valid_options = {}

        valid_options.update({
            "CMD_LINE_ARGS":"<cmdline args for the code under test>",
            "GPROF": "yes|no",
            "DEBUG": "yes|no",
            "OPTIMIZE": "<gcc optimization flags>",
            "COMPILER": "gcc-9",
            'DEVEL_MODE':  "yes|no",
        })
        
        super(CSE141Lab, self).__init__(
            lab_name = lab_name,
            short_name = short_name,
            output_files = output_files,
            input_files = input_files,
            default_cmd = default_cmd,
            valid_options= valid_options,
            clean_cmd = clean_cmd,
            config_file="config.env",
            repo = repo,
            reference_tag = reference_tag,
            time_limit = timeout)

    class EasyFileAccess(object):
        
        def open_file(self, name, root=None):
            if root == None:
                root = os.environ['LAB_SUBMISSION_DIR']
            else:
                root = "."
                
            path = os.path.join(root, name)
            log.debug(f"Opening {os.path.abspath(path)} for graded regressions")
            return open(path)

        def read_file(self, name, root=None):
            with self.open_file(name, root) as f:
                return f.read()
        def assertFileExists(self, f, tag=""):
            self.assertTrue(os.path.exists(f), f"Failed on {tag}: looking for '{f}'")
        def assertNotFileExists(self, f, tag):
            self.assertFalse(os.path.exists(f), f"Failed on {tag}: looking for the absence of '{f}'")
        

    class GradedRegressions(unittest.TestCase, EasyFileAccess):

        def __init__(self, *argc, **kwargs):
            unittest.TestCase.__init__(self, *argc, **kwargs)
            self.regressions_passed = 0
            self.regression_count = 0

        # this is some magic to let us introspect on what's passed: https://stackoverflow.com/questions/28500267/python-unittest-count-tests
        currentResult = None
        def run(self, result=None):
            self.currentResult = result # remember result for use in tearDown
            unittest.TestCase.run(self, result) # call superclass run method
            
        def go_run_tests(self, label, cwd=None):
            self.regression_count += 1
            log.debug(f"Runing regression {label} {self.regression_count}")
            try:
                timedout = False
                log.debug(f"PWD={os.getcwd()}")
                cmd = ["./run_tests.exe", f"--gtest_filter=*{label}*"]
                try:
                    p = subprocess.run(cmd, timeout=30, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except OSError as e:
                    self.assertTrue(False, "Something went wrong running the regressions.  If run_tests.exe runs for you locally, this is probably a bug in the autograder: {repr(e)}.")
                    p = None
                except subprocess.TimeoutExpired:
                    p.kill()
                    sys.stderr.write(f"===========Execution timed out after 30 seconds.================")
                    timedout= True
                    self.assertTrue(False, f"Tests for {label} failed due to timeout")
                else:
                    self.regressions_passed += 1
                    log.debug(f"Passed {self.regressions_passed}")
        
                sys.stdout.write(f"To reproduce: make run_test.exe; {' '.join(cmd)}\n")
                sys.stdout.write(p.stdout.decode('utf8'))
                sys.stderr.write(p.stderr.decode('utf8'))
                if p.returncode != 0:
                    self.assertTrue(False, f"Tests for {label} did not pass.")
                else:
                    self.assertTrue(True)
                                    
            except Exception as e:
                log.exception(e)
                self.assertTrue(False, f"Got an exception: {repr(e)}")

    class MetaRegressions(unittest.TestCase, EasyFileAccess):

        def run_solution(self, solution, pristine=False, devel=False, gprof=False, remote=False):
            tag = f"{solution}-{'p' if pristine else ''}-{'d' if devel else ''}-{'g' if gprof else ''}-{'r' if remote else ''}"
            log.info(f"=========================== Starting {tag} in {self.id()} ==========================================")
            env = {}
            if devel:
                env['DEVEL_MODE'] = 'yes'
            else:
                env['DEVEL_MODE'] = ''
            if gprof:
                env['GPROF'] = 'yes'
            else:
                env['GPROF'] = 'no'
                
            with environment(**env):
                submission = build_submission(".",
                                              solution,
                                              None,
                                              username="metatest",
                                              pristine=pristine)
                if remote:
                    result = run_submission_remotely(submission, daemon=True)
                else:
                    result = run_submission_locally(submission,
                                                    root=".",
                                                    run_in_docker=False,
                                                    docker_image=os.environ['DOCKER_RUNNER_IMAGE'],
                                                    run_pristine=pristine)
                    
                log.info(f"results={result.results}")
            log.info(f"=========================== Finished {tag} in {self.id()} ==========================================")
            return result, tag 

