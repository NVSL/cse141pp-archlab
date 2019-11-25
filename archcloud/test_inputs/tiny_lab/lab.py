from ArchLab.Runner import LabSpec

class ThisLab(LabSpec):
    def __init__(self):
        super(ThisLab, self).__init__(
            lab_name = "Tiny Lab For Testing",
            input_files = ['in'],
            output_files = ['out'],
            default_cmd = ['cp', 'in', 'out'],
            clean_cmd = ['rm', '-rf', 'out'],
            repo = "na",
            reference_tag = "na",
            time_limit = 2,
        )
