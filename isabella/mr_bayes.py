from .environment_desc import ProgramDescription


class MrBayes(ProgramDescription):
    @staticmethod
    def create_scripts_method():
        from .utils import simple_run_script
        return simple_run_script

    @staticmethod
    def get_job_additional_params(job_data):
        return dict(result_prefix=job_data['result_prefix'])

    @staticmethod
    def files_to_zip(job_data):
        rp = job_data['result_prefix']
        return [(rp + e) for e in ('.ckp', '.con.tre', '.parts', '.run1.p', '.run1.t',
                                   '.run2.p', '.run2.t', '.tstat', '.vstat')]

    # @staticmethod
    # def status_string(job_directory):
    #     num_iterations = 1000  # ToDo: find data somewhere

    #     r_o = os.path.join(job_directory, 'RAxML_info.raxml_output')
    #     if os.path.isfile(r_o):
    #         with open(r_o, 'r') as _in:
    #             last_lines = deque(_in, 5)
    #         # Check lines from the end
    #         lines = reversed(last_lines)
    #         for line in lines:
    #             m = _bootstrap_iteration.search(line)
    #             if m:
    #                 num_iter = m.group(1)
    #                 return f"on iteration {num_iter}/{num_iterations}"
    #             m = _overall_time.search(line)
    #             if m:
    #                 seconds = lasted_seconds(int(m.group(1)))
    #                 return f"bootstrap time {seconds}"
    #     return ''
