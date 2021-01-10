import os
import sys
import datetime
from isabella.utils import send_pre_email

# Note: posao.status is created after checking for mailing
send_pre_email()

with open('posao.status', 'w') as _out:
    _out.write(f'program_type: {sys.argv[1]}\n')
    _out.write(f'started: {datetime.datetime.now()}\n')
    # ToDo: Jos neka varijable?
    for env in ('JOB_ID', 'QUEUE', 'HOSTNAME', 'JOB_NAME', 'NSLOTS',
                'SGE_TASK_ID', 'SGE_O_HOST', 'SGE_O_PATH', 'SGE_O_WORKDIR', 'PE_HOSTFILE'):
        _out.write(f"{env}: {os.environment.get(env, '')}\n")
