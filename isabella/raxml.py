import re
import os.path
from collections import deque
from .environment_desc import ProgramDescription

_bootstrap_iteration = re.compile(r'^Bootstrap\[(\d+)\]')


class RAxML:
    @staticmethod
    def create_scripts_method():
        from .utils import simple_run_script
        return simple_run_script

    @staticmethod
    def files_to_zip():
        return ('RAxML_bestTree.raxml_output', 'RAxML_bipartitionsBranchLabels.raxml_output',
                'RAxML_bipartitions.raxml_output', 'RAxML_bootstrap.raxml_output', 'RAxML_info.raxml_output'),

    @staticmethod
    def status_string(job_directory):
        num_iterations = 1000  # ToDo: find data somewhere

        r_o = os.path.join(job_directory, 'RAxML_info.raxml_output')
        if os.path.isfile(r_o):
            with open(r_o, 'r') as _in:
                last_lines = deque(_in, 3)
            while last_lines:
                r_o = os.path.join(job_directory, 'RAxML_info.raxml_output')
                m = _bootstrap_iteration.search(last_lines.pop())
                if m:
                    num_iter = m.group(1)
                    return f"iteration {num_iter}/{num_iterations}"
        return ''
