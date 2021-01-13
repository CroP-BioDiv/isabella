import os
from datetime import datetime
from .environment_desc import IsabellaException, lasted_seconds, get_program_desc

PROCESSING_FILENAME = 'obrada.status'
JOB_FILENAME = 'posao.status'
PROCESSING_OUTPUT_FILENAME = 'obrada_output.zip'

_datetime_fromiso = datetime.fromisoformat if hasattr(datetime, 'fromisoformat') else \
    (lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f'))


def write_processing_status(jobs, email):
    with open(PROCESSING_FILENAME, 'w') as _out:
        for i, d in enumerate(jobs):
            _out.write(f'job_dir_{i}: {d}\n')
        if email:
            _out.write(f'email: {email}\n')


def check_is_directory_processing():
    if os.path.isfile(PROCESSING_FILENAME):
        raise IsabellaException('Directory is already in processing!')


def read_job_data(cwd=None):
    p_file = os.path.join(cwd, JOB_FILENAME) if cwd else JOB_FILENAME
    with open(p_file, 'r') as _in:
        return dict(tuple(x.strip() for x in l.split(':', 1)) for l in _in)


def lasted_str(started, ended):
    # Returns string (of length 7) that describes passsed time
    s = _datetime_fromiso(started).timestamp()
    e = _datetime_fromiso(ended).timestamp()
    lasted = int(e - s)  # Just seconds
    return lasted_seconds(lasted)
    #
    parts = []
    days = lasted // (24 * 60 * 60)
    if days:
        parts.append(f'{days:2}d')
    #
    rest = lasted - days * 24 * 3600
    hours = rest // 3600
    if hours:
        parts.append(f'{hours:02}h' if parts else f'{hours:2}h')
    #
    rest -= hours * 3600
    mins = rest // 60
    parts.append(f'{mins:02}m')
    #
    secs = rest - mins * 60
    parts.append(f'{secs:02}s')
    return ':'.join(parts[:2])


class Processing:
    def __init__(self):
        self.directory = None
        self.data = None
        self._find_directory()

    def _find_directory(self):
        # This is called from processing or job directory.
        # Check current directory and up ones
        _dir = os.path.abspath('.')
        while True:
            o_file = os.path.join(_dir, PROCESSING_FILENAME)
            if os.path.isfile(o_file):
                with open(o_file, 'r') as _in:
                    self.directory = _dir
                    self.data = dict(tuple(x.strip() for x in line.split(':', 1)) for line in _in if line)
                    return
            #
            n_dir = os.path.abspath(os.path.join(_dir, '..'))
            if _dir == n_dir:
                return
            _dir = n_dir

    def job_directories(self):
        return (v for k, v in self.data.items() if k.startswith('job_dir_'))

    def job_directories_with_data(self):
        return ((v, read_job_data(os.path.join(self.directory, v)))
                for k, v in self.data.items() if k.startswith('job_dir_'))

    def is_processing(self):
        return self.directory is not None

    def is_finished(self):
        if not self.is_processing():
            return False

        for j_dir in self.job_directories():
            o_file = os.path.join(self.directory, j_dir, JOB_FILENAME)
            if os.path.isfile(o_file):
                with open(o_file, 'r') as _in:
                    if not any(line.startswith('ended:') for line in _in):
                        return False
        return True

    def print_status(self):
        now = str(datetime.now())
        for j_dir, job_data in self.job_directories_with_data():
            # Vrijeme
            ended = job_data.get('ended')
            lasted = lasted_str(job_data['started'], ended or now)

            # Program specific
            prog_spec = 'finished'
            if not ended:
                program_desc = get_program_desc(job_data['program_type'])
                if program_desc:
                    prog_spec = program_desc.status_string(j_dir)
            if prog_spec:
                print(f"{j_dir}: {lasted} - {prog_spec}")
            else:
                print(f"{j_dir}: {lasted}")

    def collect_output(self):
        from zipfile import ZipFile, ZIP_DEFLATED
        prev_cwd = os.getcwd()
        os.chdir(self.directory)
        files_to_zip = []
        for j_dir, job_data in self.job_directories_with_data():
            program_desc = get_program_desc(job_data['program_type'])
            if program_desc:
                fz = program_desc.files_to_zip(job_data)
                if fz:
                    files_to_zip.extend(os.path.join(j_dir, f) for f in fz)
            files_to_zip.append(os.path.join(j_dir, JOB_FILENAME))
        #
        with ZipFile(PROCESSING_OUTPUT_FILENAME, 'w', compression=ZIP_DEFLATED) as output:
            for f_name in files_to_zip:
                output.write(f_name)
        os.chdir(prev_cwd)

    # Meils
    def send_pre_email(self):
        if not self.is_processing():
            return
        if 'mail_send' in self.data:
            return
        email = self.data.get('email')
        if not email:
            return
        if any(os.path.isfile(os.path.join(self.directory, v, JOB_FILENAME))
               for k, v in self.data.items() if k.startswith('job_dir_')):
            return

        #
        try:
            with AtomicOpen(os.path.join(self.directory, PROCESSING_FILENAME), 'r+') as _out:
                for l in _out:
                    if l.startswith('mail_send'):
                        return
                _out.write('mail_send: 1\n')
        except Exception:
            print(f"Error: locking of file {os.path.join(self.directory, PROCESSING_FILENAME)}!")
            return

        send_email(email, 'Isabella obrada', f'Počeo je prvi posao obrada u direktoriju {self.directory}.')

    def send_post_email(self):
        email = self.data.get('email')
        if email:
            send_email(email, 'Isabella obrada', f'Završila je obrada u direktoriju {self.directory}.')


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
