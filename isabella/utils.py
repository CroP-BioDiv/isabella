import os
import shutil
import subprocess
from .environment_desc import get_program_and_queue
from .processing import Processing

_ISABELLA_MODULE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_ISABELLA_BIN_DIR = os.path.join(_ISABELLA_MODULE_DIR, 'bin')


def write_str_in_file(filename, s):
    with open(filename, 'w') as r:
        r.write(s)


def standard_arguments(parser):
    parser.add_argument('-t', '--num-threads', default=1,
                        help="Number of threads. Can be specified as ingteger (8), or a range (4-8)")
    parser.add_argument('-S', '--simulate', action='store_true', help="Simulate run, without actual running")
    parser.add_argument('-m', '--email', help="Email address for start/end notices")


def parse_num_threads(num_threads):
    try:
        return int(num_threads)
    except ValueError:
        pass

    parts = num_threads.split('-')
    return (int(parts[0]), int(parts[1]))


def simple_run_script(program_type, cwd, job_desc,
                      name=None, project=None, email=None,
                      num_threads=1, job_additional_params=None, simulate=False):
    # Check available command lines
    single_cmd = job_desc.get('single')
    threads_cmd = job_desc.get('threads')
    if not threads_cmd and not single_cmd:
        print("Don't know job's command line!!!")
        return

    # Make run script for programs that depend only on num_threads
    nt = parse_num_threads(num_threads)
    max_num_threads = nt if isinstance(nt, int) else nt[1]
    program, queue = get_program_and_queue(program_type, max_num_threads, single_cmd, threads_cmd)
    if not program:
        return

    if program.parallel == 'threads':
        # Run threaded version
        cmd = threads_cmd.format(num_threads=("$NSLOTS" if max_num_threads > 1 else 1), exe=program.program)
    else:
        cmd = single_cmd.format(exe=program.program)
    assert cmd

    #
    script = make_script(program_type, program.program + ' ' + cmd, queue.queue,
                         name=name, project=project, email=email,
                         num_threads=(num_threads if max_num_threads > 1 else None),
                         load_modules=program.modules,
                         job_additional_params=job_additional_params,
                         env_path=program.directory)

    write_str_in_file(os.path.join(cwd, 'job_script'), script)

    if simulate:
        print(cwd)
        print(script)
    else:
        if shutil.which('qsub'):
            subprocess.run(['qsub', 'job_script'], cwd=cwd)
        else:
            print(f'cd {cwd}; qsub job_script')


def make_script(program_type, cmd, queue, name=None, project=None, email=None, num_threads=None,
                load_modules=None, job_additional_params=None, env_path=None):
    # https://wiki.srce.hr/display/RKI/Pokretanje+i+upravljanje+poslovima#Pokretanjeiupravljanjeposlovima-Resursi
    script = '#!/bin/bash\n\n'
    for val, flag in ((name, 'N'), (project, 'P'), (num_threads, 'pe *mpisingle'), (queue, 'q')):
        if val:
            script += f'#$ -{flag} {val}\n'
    script += """#$ -cwd
#$ -o stdout.out
#$ -e stderr.out
"""

    if email:
        script += f"""#$ -M {email}
#$ -m e
"""
    script += f"""
# Set environment
export PYTHONPATH={_ISABELLA_MODULE_DIR}:$PYTHONPATH
export PATH={_ISABELLA_BIN_DIR}:$PATH
"""

    if env_path:
        if isinstance(env_path, str):
            script += f"export PATH={os.path.abspath(env_path)}:$PATH\n"
        elif isinstance(env_path, (list, tuple)):
            script += f"export PATH={';'.join(os.path.abspath(p) for p in env_path)}:$PATH\n"

    if load_modules:
        for m in load_modules:
            script += f"module load {m}\n"

    if job_additional_params:
        jap = f' "{":".join(f"{k}={v}" for k, v in job_additional_params.items())}"'
    else:
        jap = ''

    script += f"""
# Run script
job_pre_run.py {program_type}{jap}
{cmd}
job_post_run.py
"""

    return script


#
def on_finish_job():
    processing = Processing()
    if processing.is_finished():
        processing.send_post_email()
        processing.collect_output()


def send_pre_email():
    Processing().send_pre_email()
