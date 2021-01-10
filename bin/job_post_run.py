#!/usr/bin/python3

import os.path
import datetime
from isabella.utils import on_finish_job


with open('posao.status', 'a') as _out:
    _out.write(f'ended: {datetime.datetime.now()}\n')

on_finish_job()
