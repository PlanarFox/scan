import os
import sys
sys.path.append(os.path.join(os.getcwd(), '..'))
from server import app
import util
from flask import request
import json
import submit_proc

@app.route('/myplatform/submit/<task_type>', methods=['POST'])
def submition_recv(task_type):
    try:
        args = json.loads(request.form['data'])
    except Exception as e:
        return util.bad_request('Args must be in json format:' + e.args)
    try:
        data = request.files['file']
    except Exception as e:
        return util.bad_request('Fail when loading data file:' + e.args)

    uuid = args['uuid']
    probe = args['addr']

    cwd = os.path.join(os.path.join(os.path.join(os.getcwd(), 'data'), task_type), uuid)
    if not os.path.isdir(cwd):
        return util.bad_request('Unknown task.')
    if not os.path.isdir(os.path.join(cwd, probe)):
        return util.bad_request('Unknown probe.')

    data.save(os.path.join(os.path.join(cwd, probe), 'tmp_data'))
    if not util.integrity_check(os.path.join(os.path.join(cwd, probe), 'tmp_data'), args['md5']):
        return util.bad_request('File is broken.')

    valid, message = getattr(submit_proc, task_type)(cwd, uuid, probe)

    if not valid:
        return util.bad_request(message=message)
    return util.ok()

    