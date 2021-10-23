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
    try:
        data = request.files['file']
    except Exception as e:
        return util.bad_request(util.error_record('Fail when loading data file.', logger, stream_handler, errIO))

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

    data.save(os.path.join(os.path.join(cwd, probe), 'tmp_data'))
    if not util.integrity_check(os.path.join(os.path.join(cwd, probe), 'tmp_data'), args['md5']):
        logger.error('File submitted from %s is broken.', probe)
        return util.bad_request('File submitted is broken.')

    valid, message = getattr(submit_proc, task_type)(cwd, uuid, probe, error)

    if not valid:
        return util.bad_request(message=message)
    logger.info('Data from %s submitted.', probe)
    return util.ok()

    