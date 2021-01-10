import os
import shutil
import subprocess
from .environment_desc import get_program_and_queue, get_files_to_zip
_ISABELLA_MODULE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_ISABELLA_BIN_DIR = os.path.join(_ISABELLA_MODULE_DIR, 'bin')


class IsabellaException(Exception):
    pass


def write_str_in_file(filename, s):
    with open(filename, 'w') as r:
        r.write(s)


def check_is_directory_processing():
    # Provjeriti jel direktorij vec obrada
    if os.path.isfile('obrada.status'):
        raise IsabellaException('Directory is already in processing!')


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
                      num_threads=1, simulate=False):
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
        cmd = threads_cmd.format(num_threads=("$NSLOTS" if max_num_threads > 1 else 1))
    else:
        cmd = single_cmd
    assert cmd

    #
    script = make_script(program_type, program.program + ' ' + cmd, queue.queue,
                         name=name, project=project, email=email,
                         num_threads=(num_threads if max_num_threads > 1 else None),
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
                env_path=None):
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

    script += f"""
# Run script
python3 job_pre_run.py {program_type}
{cmd}
python3 job_post_run.py
"""

    return script


#
def write_obrada_status(jobs, email):
    with open('obrada.status', 'w') as _out:
        for i, d in enumerate(jobs):
            _out.write(f'job_dir_{i}: {d}\n')
        if email:
            _out.write(f'email: {email}\n')


def read_obrada_data():
    # This is called from posao directory. Obrada directory is that or some up.
    _dir = os.path.abspath('.')
    while True:
        o_file = os.path.join(_dir, 'obrada.status')
        if os.path.isfile(o_file):
            with open('obrada.status', 'r') as _in:
                data = dict(tuple(x.strip() for x in line.split(':', 1)) for line in _in if line)
                return _dir, data
        #
        n_dir = os.path.abspath(os.path.join(_dir, '..'))
        if _dir == n_dir:
            return
        _dir = n_dir


def read_posao_data(cwd=None):
    p_file = os.path.join(cd, 'posao.status') if cwd else 'posao.status'
    with open(p_file, 'r') as _in:
        return dict(tuple(x.strip() for x in l.split(':', 1)) for l in _in)


def is_obrada_finished():
    obrada_data = read_obrada_data()
    if not obrada_data:
        return
    obrada_dir, obrada_data = obrada_data
    for k, v in obrada_data.items():
        if k.startswith('job_dir_'):
            o_file = os.path.join(obrada_dir, v, 'posao.status')
            if not os.path.isfile(o_file):
                return
            with open(o_file, 'r') as _in:
                if not any(line.startswith('ended:') for line in _in):
                    return
    return obrada_dir, obrada_data


def collect_obrada_output(obrada_dir, obrada_data):
    from zipfile import ZipFile, ZIP_DEFLATED
    os.chdir(obrada_dir)
    files_to_zip = []
    for k, _dir in obrada_data.items():
        if k.startswith('job_dir_'):
            posao_data = read_posao_data(cwd=_dir)
            files_to_zip.extend(os.path.join(_dir, f) for f in get_files_to_zip(posao_data['program_type']))
            files_to_zip.append(os.path.join(_dir, 'posao.status'))
    #
    with ZipFile('obrada_output.zip', 'w', compression=ZIP_DEFLATED) as output:
        for f_name in files_to_zip:
            output.write(f_name)


def send_pre_email():
    obrada_data = read_obrada_data()
    if not obrada_data:
        return
    obrada_dir, obrada_data = obrada_data
    if 'mail_send' in obrada_data:
        return
    email = obrada_data.get('email')
    if not email:
        return
    if any(os.path.isfile(os.path.join(obrada_dir, v, 'posao.status'))
           for k, v in obrada_data.items() if k.startswith('job_dir_')):
        return

    #
    try:
        with AtomicOpen(os.path.join(obrada_dir, 'obrada.status'), 'r+') as _out:
            for l in _out:
                if l.startswith('mail_send'):
                    return
            _out.write('mail_send: 1\n')
    except:
        return

    send_email(email, 'Isabella obrada', f'Počeo je prvi posao obrada u direktoriju {obrada_dir}.')


def send_post_email(obrada_data):
    email = obrada_data.get('email')
    if email:
        send_email(email, 'Isabella obrada', f'Završila je obrada u direktoriju {obrada_dir}.')


def send_email(to_email, subject, text, server='localhost'):
    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg.set_content(text)
    msg['Subject'] = subject
    msg['From'] = 'isabella@isabella'
    msg['To'] = to_email.split(',')

    # Send the message via our own SMTP server.
    s = smtplib.SMTP(server)
    s.send_message(msg)
    s.quit()


# Lock file
# https://stackoverflow.com/questions/489861/locking-a-file-in-python
try:
    # Posix based file locking (Linux, Ubuntu, MacOS, etc.)
    #   Only allows locking on writable files, might cause
    #   strange results for reading.
    import fcntl

    def lock_file(f):
        if f.writable():
            fcntl.lockf(f, fcntl.LOCK_EX)

    def unlock_file(f):
        if f.writable():
            fcntl.lockf(f, fcntl.LOCK_UN)
except ModuleNotFoundError:
    # Windows file locking
    import msvcrt

    def file_size(f):
        return os.path.getsize(os.path.realpath(f.name))

    def lock_file(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_RLCK, file_size(f))

    def unlock_file(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, file_size(f))


# Class for ensuring that all file operations are atomic, treat
# initialization like a standard call to 'open' that happens to be atomic.
# This file opener *must* be used in a "with" block.
class AtomicOpen:
    # Open the file with arguments provided by user. Then acquire
    # a lock on that file object (WARNING: Advisory locking).
    def __init__(self, path, *args, **kwargs):
        # Open the file and acquire a lock on the file before operating
        self.file = open(path, *args, **kwargs)
        # Lock the opened file
        lock_file(self.file)

    # Return the opened file object (knowing a lock has been obtained).
    def __enter__(self, *args, **kwargs):
        return self.file

    # Unlock the file and close the file object.
    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        # Flush to make sure all buffered contents are written to file.
        self.file.flush()
        os.fsync(self.file.fileno())
        # Release the lock on the file.
        unlock_file(self.file)
        self.file.close()
        # Handle exceptions that may have come up during execution, by
        # default any exceptions are raised to the user.
        return exc_type is None
