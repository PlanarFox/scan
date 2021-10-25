import os
import sys
sys.path.append(os.path.join(os.getcwd(), '..'))
from server import app
import util
from flask import request
import json
import submit_proc
import logging
from io import StringIO

logger = logging.getLogger('server')
errIO = StringIO()
stream_handler = logging.StreamHandler(errIO)
stream_handler.setLevel(level=logging.ERROR)
stream_handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s"))
logger.addHandler(stream_handler)

@app.route('/myplatform/submit/<task_type>', methods=['POST'])
def submition_recv(task_type):
    try:
        args = json.loads(request.form['data'])
    except Exception as e:
        return util.bad_request(util.error_record('Args must be in json format.', logger, stream_handler, errIO))

    uuid = args['uuid']
    probe = args['addr']
    error = args['error']

    cwd = os.path.join(os.path.join(os.path.join(os.getcwd(), 'data'), task_type), uuid)
    if not os.path.isdir(cwd):
        logger.error('Unknown task submitted.')
        return util.bad_request('Unknown task.')
    if not os.path.isdir(os.path.join(cwd, probe)):
        logger.error('Unknown probe specified.')
        return util.bad_request('Unknown probe.')

    try:
        for key, _ in request.files.items():
            request.files[key].save(os.path.join(os.path.join(cwd, probe), str(key)))
            if not util.integrity_check(os.path.join(os.path.join(cwd, probe), str(key)), args['md5'][str(key)]):
                logger.error('User uploaded data is broken. File location:%s', os.path.join(os.path.join(cwd, probe), str(key)))
                return util.bad_request('File is broken.')
    except:
        return util.bad_request(util.error_record('Fail to load data from user\'s post.', logger, stream_handler, errIO))

    valid, message = getattr(submit_proc, task_type)(cwd, uuid, probe, error)

    if not valid:
        return util.bad_request(message=message)
    logger.info('Data from %s submitted.', probe)
    return util.ok()

    