"""
Module describes environment of cluster Isabella. Environment consists of:
* cluster properties (queues, nodes, ...)
* properties of installed programs (multhithreaded, MPI, vector instuctions (AVX, AVX2))
"""

from os.path import join
import shutil
from collections import namedtuple

_ISABELLA_MAIN_DIR = '/home/aturudic/Isabella'
_ISABELLA_PROJET_DIR = join(_ISABELLA_MAIN_DIR, 'isabella')
_ISABELLA_PROGRAMS_DIR = join(_ISABELLA_MAIN_DIR, 'programs')


class IsabellaException(Exception):
    pass


# Values:
#  - parallel: single, threads, mpi, mpifull

# Description of cluster queues
# https://wiki.srce.hr/display/RKI/Redovi+poslova+i+paralelne+okoline
_Queue = namedtuple('_Queue', 'queue, parallel, cpus, memory_gb, max_days, flags')
_QUEUES = [
    # 76 x Lenovo NeXtScale nx360 M5
    # 2 x Intel Xeon E5-2683 v3
    # 128 GB RAM
    # 1 x 1 TB diskovnog prostora
    _Queue('p28.q', 'single', 1, 128, 7, ('AVX2',)),
    _Queue('p28.q', 'threads', 28, 128, 7, ('AVX2',)),
    _Queue('p28.q', 'mpi', 28, 128, 7, ('AVX2',)),
    _Queue('p28.q', 'mpifull', 28, 128, 7, ('AVX2',)),
    #
    _Queue('p28-long.q', 'single', 28, 128, 30, ('AVX2',)),
    _Queue('p28-long.q', 'threads', 28, 128, 30, ('AVX2',)),
    _Queue('p28-long.q', 'mpi', 28, 128, 30, ('AVX2',)),
    _Queue('p28-long.q', 'mpifull', 28, 128, 30, ('AVX2',)),

    # ToDo: Trebaju li nam uopce drugi redovi?
]

# Description of installed programs
_Program = namedtuple('_Program', 'program, directory, parallel, flags')

_RAxML_DIR = join(_ISABELLA_PROGRAMS_DIR, 'RAxML', 'bin')

_PROGRAMS = dict(
    raxml=[
        _Program('raxmlHPC-AVX2', _RAxML_DIR, 'single', ('AVX2',)),
        _Program('raxmlHPC-PTHREADS-AVX2', _RAxML_DIR, 'threads', ('AVX2',))
    ],
)

# # Check do program exist and fix data
# for prs in _PROGRAMS.values():
#     to_remove = []
#     for i, p in enumerate(prs):
#         exe = join(p.directory, p.program)
#         if not shutil.which(exe):
#             print(f'Warning: program {exe} is not executable!')
#             to_remove.append(i)
#     for i in reversed(to_remove):
#         prs.pop(i)


# ---------------------------------------------------------
# Methods
# ---------------------------------------------------------
def get_queue(parallel, num_cpus, flags):
    for q in _QUEUES:
        if q.parallel == parallel and all(f in q.flags for f in flags):
            return q


def get_program(program, parallel):
    for p in _PROGRAMS.get(program, []):
        if parallel == p.parallel:
            return p


def get_program_and_queue(program, num_threads, single_cmd, threads_cmd):
    queue = None

    # Try multithreaded
    if num_threads > 1 and threads_cmd:
        program = get_program(program, 'threads')
        if program:
            queue = get_queue('threads', num_threads, program.flags)

    # Try single CPU
    if not queue and single_cmd:
        program = get_program(program, 'single')
        if program:
            queue = get_queue('single', 1, program.flags)

    # Backup on threaded version
    if not queue and threads_cmd:
        program = get_program(program, 'threads')
        if program:
            queue = get_queue('single', 1, program.flags)

    return (program, queue) if queue else (None, None)


# ---------------------------------------------------------
# Program description has to implement this interface
# ---------------------------------------------------------
class ProgramDescription:
    @staticmethod
    def create_scripts_method():
        pass

    @staticmethod
    def files_to_zip():
        raise NotImplementedError(f'Method files_to_zip() is not implemented!')

    @staticmethod
    def status_string(job_directory):
        return ''


def get_program_desc(program_type):
    if program_type == 'raxml':
        from .raxml import RAxML
        return RAxML
