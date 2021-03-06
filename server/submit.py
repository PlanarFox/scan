import hashlib
import os
from pathlib import Path
import sys
sys.path.append(os.path.join(os.getcwd(), '..'))
from server import app
import util
from flask import request
import json
import submit_proc
import logging
from io import StringIO
import threading
import store

logger = logging.getLogger('server')
errIO = StringIO()
stream_handler = logging.StreamHandler(errIO)
stream_handler.setLevel(level=logging.ERROR)
stream_handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s"))
logger.addHandler(stream_handler)

@app.route('/myplatform/submit/<task_type>', methods=['POST'])
def submition_recv(task_type):
    try:
        args_size = int(request.stream.readline().strip())
        args = request.stream.read(args_size)
        if request.args.get('md5', None) != hashlib.md5(args).hexdigest():
            return util.bad_request(util.error_record('User posted config is broken.', logger, stream_handler, errIO))
        args = json.loads(args)
    except Exception as e:
        return util.bad_request(util.error_record('Args must be in json format.', logger, stream_handler, errIO))

    uuid = args['uuid']
    probe = args['addr']
    error = args['error']

    logger.debug('POST from probe:%s', uuid)

    cwd = os.path.join(os.path.join(os.path.join(os.getcwd(), 'data'), task_type), uuid)
    if not os.path.isdir(cwd):
        logger.error('Unknown task submitted.')
        return util.bad_request('Unknown task.')
    probe_path = Path(cwd) / 'probe' / probe
    if not probe_path.is_dir():
        logger.error('Unknown probe specified.')
        return util.bad_request('Unknown probe.')

    try:
        util.file_saver(request, str(probe_path))
        for key, value in args['md5'].items():
            if not util.integrity_check(str(probe_path / str(key)), value):
                logger.error('User uploaded data is broken. File location:%s', str(probe_path / str(key)))
                return util.bad_request('File is broken.')
            else:
                logger.info('Result from task received, uuid:%s', uuid)
    except:
        return util.bad_request(util.error_record('Fail to load data from user\'s post.', logger, stream_handler, errIO))

    valid, message = getattr(submit_proc, task_type)(cwd, uuid, probe, error)

    if not valid:
        return util.bad_request(message=message)
    logger.info('Data from %s submitted.', probe)

    t1 = threading.Thread(target=store.store_result, args=(cwd, uuid))
    t1.start()

    return util.ok()

    