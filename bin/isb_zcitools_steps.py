#!/usr/bin/python3

import os.path
import json
from isabella.environment_desc import get_program_desc
from isabella.utils import standard_arguments
from isabella.processing import check_is_directory_processing, write_processing_status


def process(step_names=None, **arguments):
    check_is_directory_processing()

    jobs = []
    for step_name in (step_names or os.listdir('.')):
        if not os.path.isdir(step_name):
            continue

        # Is there specification how to run the job
        cr = os.path.join(step_name, 'cluster_run.json')
        if not os.path.isfile(cr):
            continue
        data = json.load(open(cr, 'r'))
        if not data:
            print(f"Warning: step {step_name}: cluster run info is empty?!")
            continue

        program = data.get('program')
        if not program:
            print(f"Warning: step {step_name}: cluster run info doesn't have specified program to run!")
            continue

        program_desc = get_program_desc(program)
        if not program_desc:
            continue
        method = method.create_scripts_method()
        if not method:
            continue

        dir_parts = os.path.abspath(step_name).split(os.path.sep)
        for job in data['jobs']:
            _dir = job.get('directory')
            if _dir:
                cwd = join(step_name, _dir)
                name = f"{dir_parts[-1]}-{_dir}"
            else:
                cwd = step_name
                name = '-'.join(dir_parts[-2:])
            jobs.append(cwd)
            method(program, cwd, job, name=name, **arguments)

    write_processing_status(jobs, arguments.get('email'))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="""
Run jobs with given zcitools project steps.
Check zcitools repository (https://github.com/CroP-BioDiv/zcitools).
""")
    parser.add_argument('step_names', nargs='*',
                        help="Project step directories to run. If not set, than all subdirectories are checked.")
    standard_arguments(parser)

    process(**vars(parser.parse_args()))
