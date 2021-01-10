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
    _Queue('p28-mpisingle', 'threads', 28, 128, 7, ('AVX2',)),
    _Queue('p28-mpi', 'mpi', 28, 128, 7, ('AVX2',)),
    _Queue('p28-mpifull', 'mpifull', 28, 128, 7, ('AVX2',)),
    #
    _Queue('p28-long.q', 'single', 28, 128, 30, ('AVX2',)),
    _Queue('p28-mpisingle-long', 'threads', 28, 128, 30, ('AVX2',)),
    _Queue('p28-mpi-long', 'mpi', 28, 128, 30, ('AVX2',)),
    _Queue('p28-mpifull-long', 'mpifull', 28, 128, 30, ('AVX2',)),

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


def get_program_method(program):
    if program == 'raxml':
        from .utils import simple_run_script
        return simple_run_script
    #
    print(f'Warning: no method for program {program}!')


_PROGRAM_FILES_TO_ZIP = dict(
    raxml=('RAxML_bestTree.raxml_output', 'RAxML_bipartitionsBranchLabels.raxml_output',
           'RAxML_bipartitions.raxml_output', 'RAxML_bootstrap.raxml_output', 'RAxML_info.raxml_output'),
)


def get_files_to_zip(program):
    files = _PROGRAM_FILES_TO_ZIP.get(program)
    if not files:
        print(f'Warning: no files to zip for program type {program}!')
    return files or []
