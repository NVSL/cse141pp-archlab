# Students should not edit this file, since changes here will _only_
# affect how your code runs locally.  It will not change how your code
# executes in the cloud.
from Runner import LabSpec
import functools

class ThisLab(LabSpec):
    def __init__(self):
        super(ThisLab, self).__init__(
            lab_name = "Characterizing a Perceptron",
            input_files = ['*.inp', 'foo.in', 'bar/bang.*', 'bar/boom'],
            output_files = ['an_output', 'out?'],
            default_cmd = ['touch', 'out1', 'out2', 'an_output'],
            repo = "https://github.com/NVSL/CSE141pp-Lab-Characterizing-A-Perceptron.git",
            reference_tag = "314bfbd09ab3a28b446742234851eeef2c29dcba",
            time_limit = 50000,
            valid_options = {
                "USER_CMD_LINE":"",
                "USER_CMD_LINE2":"",
                "GPROF": "",
                "DEBUG": "",
                "DEBUG2": "",
                "C_OPTS": "",
                "COMPILER": ""
            }
        )
