import os.path
import datetime
from isabella.utils import is_obrada_finished, send_post_email, collect_obrada_output


with open('posao.status', 'a') as _out:
    _out.write(f'ended: {datetime.datetime.now()}\n')

d = is_obrada_finished()
if d:
    obrada_dir, obrada_data = d
    send_post_email(obrada_data)
    collect_obrada_output(obrada_dir, obrada_data)
