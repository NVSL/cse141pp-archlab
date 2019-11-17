from .Runner import LabSpec

class CSE141Lab(LabSpec):
    def __init__(self,
                 lab_name,
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
            'DEVEL_MODE':  ""
        })
        
        super(CSE141Lab, self).__init__(
            lab_name = lab_name,
            output_files = output_files,
            input_files = input_files,
            default_cmd = default_cmd,
            clean_cmd = clean_cmd,
            repo = repo,
            reference_tag = reference_tag,
            time_limit = timeout)

