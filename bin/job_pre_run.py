#!/usr/bin/python3

import os
import sys
import datetime
from isabella.utils import send_pre_email
from isabella.processing import JOB_FILENAME

if len(sys.argv) < 2:
    print('No program type specified')
    sys.exit(0)

program_type = sys.argv[1]
add_params = None
if len(sys.argv) > 2:
    add_params = [x.split('=', 1) for x in sys.argv[2].split(':')]

# Note: posao.status is created after checking for mailing
send_pre_email()

with open(JOB_FILENAME, 'w') as _out:
    _out.write(f'program_type: {program_type}\n')
    if add_params:
        for k, v in add_params:
            _out.write(f'{k}: {v}\n')
    _out.write(f'started: {datetime.datetime.now()}\n')
    # ToDo: Jos neka varijable?
    for env in ('JOB_ID', 'QUEUE', 'HOSTNAME', 'JOB_NAME', 'NSLOTS',
                'SGE_TASK_ID', 'SGE_O_HOST', 'SGE_O_PATH', 'SGE_O_WORKDIR', 'PE_HOSTFILE'):
        _out.write(f"{env}: {os.environ.get(env, '')}\n")
