#!/usr/bin/python3

import os.path
import datetime
from isabella.utils import on_finish_job
from isabella.processing import JOB_FILENAME


with open(JOB_FILENAME, 'a') as _out:
    _out.write(f'ended: {datetime.datetime.now()}\n')

on_finish_job()
