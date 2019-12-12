from .Runner import LabSpec, build_submission, run_submission_locally
import unittest
import logging as log
import os
import sys
import subprocess

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
            "CMD_LINE_ARGS":"",
            "GPROF": "",
            "DEBUG": "",
            "OPTIMIZE": "",
            "COMPILER": "",
            'DEVEL_MODE':  "",
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
            if not root:
                root == os.environ['LAB_SUBMISSION_DIR']
                
            path = os.path.join(root, name)
            log.debug(f"Opening {path} for graded regressions")
            return open(path)

        def read_file(self, name, root=None):
            with self.open_file(name, root) as f:
                return f.read()

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
            
        def go_run_tests(self, label):
            self.regression_count += 1
            log.debug(f"Runing regression {label} {self.regression_count}")
            try:
                timedout = False
                cmd = ["./run_tests.exe", f"--gtest_filter=*{label}*"]
                try:
                    p = subprocess.run(cmd, timeout=30, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except subprocess.TimeoutExpired:
                    p.kill()
                    sys.stderr.write(f"===========Execution timed out after 30 seconds.================")
                    timedout= True
                else:
                    self.regressions_passed += 1
                    log.debug(f"Passed {self.regressions_passed}")
                finally:
                    sys.stdout.write(f"To reproduce: make run_test.exe; {' '.join(cmd)}\n")
                    sys.stdout.write(p.stdout.decode('utf8'))
                    sys.stderr.write(p.stderr.decode('utf8'))
                    if p.returncode != 0 or timedout:
                        self.assertTrue(False, f"Tests for {label} failed")
                    else:
                        self.assertTrue(True)
                            
            except Exception as e:
                log.exception(e)
                self.assertTrue(False, f"Got an exception: {repr(e)}")



    class MetaRegressions(unittest.TestCase, EasyFileAccess):

        def run_solution(self, solution):
            submission = build_submission(".",
                                          solution,
                                          None,
                                          username="metatest")
            result = run_submission_locally(submission,
                                            root=".",
                                            run_pristine=False)
            log.info(f"results={result.results}")
            return result
