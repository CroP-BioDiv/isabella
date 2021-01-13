import re
import os.path
from collections import deque
from .environment_desc import ProgramDescription, lasted_seconds

# Regex for these lines
# Bootstrap[995]: Time 125.459517 seconds, bootstrap likelihood -1151493.001498, best rearrangement setting 9
# Overall Time for 1000 Rapid Bootstraps 119924.468086 seconds
_bootstrap_iteration = re.compile(r'^Bootstrap\[(\d+)\]')
_overall_time = re.compile(r'Rapid Bootstraps (\d+)')  # Take only seconds


class RAxML:
    @staticmethod
    def create_scripts_method():
        from .utils import simple_run_script
        return simple_run_script

    @staticmethod
    def files_to_zip(job_data):
        return ('RAxML_bestTree.raxml_output', 'RAxML_bipartitionsBranchLabels.raxml_output',
                'RAxML_bipartitions.raxml_output', 'RAxML_bootstrap.raxml_output', 'RAxML_info.raxml_output'),

    @staticmethod
    def status_string(job_directory):
        num_iterations = 1000  # ToDo: find data somewhere

        r_o = os.path.join(job_directory, 'RAxML_info.raxml_output')
        if os.path.isfile(r_o):
            with open(r_o, 'r') as _in:
                last_lines = deque(_in, 5)
            # Check lines from the end
            lines = reversed(last_lines)
            for line in lines:
                m = _bootstrap_iteration.search(line)
                if m:
                    num_iter = m.group(1)
                    return f"on iteration {num_iter}/{num_iterations}"
                m = _overall_time.search(line)
                if m:
                    seconds = lasted_seconds(int(m.group(1)))
                    return f"bootstrap time {seconds}"
        return ''
