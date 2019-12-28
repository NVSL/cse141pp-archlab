from .Runner import LabSpec, build_submission, run_submission_locally, run_submission_remotely, environment
import unittest
import logging as log
import os
import sys
import subprocess
import time
import inspect
import subprocess
from uuid import uuid4 as uuid

# this is for parameterizing tests
def crossproduct(a,b):
    r = []
    
    for i in a:
#        print(i)
        for j in b:
 #           print(j)
            r.append(list(i) + list(j))
    return r


# These are the flag settings we check
# You can add columns, but don't org them.
# lab.py's refer to these by index

class TestFlags(object):
    def __init__(self, pristine, devel, gprof, remote, public_lab):
        self.pristine = pristine
        self.devel = devel
        self.gprof = gprof
        self.remote = remote
        self.public_lab = public_lab

    def grades_valid(self):
        return self.remote or (not self.public_lab and os.path.exists("private.py"))

_test_flags = crossproduct(
#     pristine devel  gprof  remote
    [(False,  False, False, False ), # everything off
     (True,   False, False, False ),
     (False,  True,  False, False ),
     (False,  False, True,  False ),
     (False,  False, False, True  ), 
     (False,  True,  True,  False ), # Local perf tuning
     (True ,  False, True,  True  ), # typical autograder run
     (True ,  True, True,   True  ), # everything on
    ],
    # public_only
    [[True], [False]])

test_flags = list(map(lambda x: TestFlags(*x), _test_flags))

def test_configs(*solutions):
    t = crossproduct(list(map(lambda x:[x], solutions)), list(map(lambda x: [x], test_flags)))
    return t


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
            'IN_TRAVIS_CI': "yes|undef"
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

    @classmethod
    def does_papi_work(cls):
        try:
            subprocess.check_call(['archlab_check', '--engine', 'papi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except:
            return False
        
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
            if not os.path.exists("./run_tests.exe"):
                self.skipTest("Regression not run, since run_tests.exe was not built.  This is probably because either compilation or running your job failed.")
                
            try:
                timedout = False
                log.debug(f"PWD={os.getcwd()}")
                cmd = ["./run_tests.exe", f"--gtest_filter=*{label}*"]
                try:
                    p = subprocess.run(cmd, timeout=30, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except OSError as e:
                    self.assertTrue(False, f"Something went wrong running the regressions.  If run_tests.exe runs for you locally, this is probably a bug in the autograder: {repr(e)}.")
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

        def runtimes_valid(self):
            return not ('IN_TRAVIS_CI' in os.environ)
        
        def compute_scores(self, js):
            # breakdown score into approximate and precise components
            # for more accurate regression testing.
            precise = 0
            approximate = 0
            for t in js['gradescope_test_output']['tests']:
                if 'tags' in t and 'approximate' in t['tags']:
                    approximate += float(t['score'])
                else:
                    precise += float(t['score'])
            return precise, approximate
        
        
        def run_solution(self, solution, flags):
            tag = f"{solution}-{'p' if flags.pristine else ''}-{'d' if flags.devel else ''}-{'g' if flags.gprof else ''}-{'r' if flags.remote else ''}-{'s' if flags.public_lab else ''}"
            log.info(f"=========================== Starting {tag} in {self.id()} ==========================================")

            if not CSE141Lab.does_papi_work() and not flags.devel:
                log.warn("Skipping since PAPI doesn't work on this machine and this is not a devel mode test.")
                self.skipTest("Skipping since PAPI doesn't work on this machine and this is not a devel mode test.")

            if not os.path.exists(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]) and flags.remote:
                log.warn("Skipping since this docker container can't submit jobs")
                self.skipTest("Skipping since this docker container can't submit jobs")

            if not os.path.exists(solution):
                log.warn(f"Skipping since {solution} doesn't exist.")
                self.skipTest(f"Skipping since {solution} doesn't exist.")
                
            env = {}
            if flags.devel:
                env['DEVEL_MODE'] = 'yes'
            else:
                env['DEVEL_MODE'] = ''

            if flags.gprof:
                env['GPROF'] = 'yes'
            else:
                env['GPROF'] = 'no'
                
            with environment(**env):
                submission = build_submission(".",
                                              solution,
                                              None,
                                              public_only=flags.public_lab,
                                              username="swanson@eng.ucsd.edu",
                                              pristine=flags.pristine)
                if flags.remote:
                    result = run_submission_remotely(submission, daemon=not 'SUPRESS_LOCAL_DAEMON' in os.environ)
                else:
                    result = run_submission_locally(submission,
                                                    run_in_docker=False,
                                                    docker_image=os.environ['DOCKER_RUNNER_IMAGE'],
                                                    run_pristine=flags.pristine)
                    
                log.debug(f"results={result.results}")
            log.info(f"=========================== Finished {tag} in {self.id()} ==========================================")
            return result, tag 
