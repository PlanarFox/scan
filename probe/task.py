import os
import sys
sys.path.append(os.path.join(os.getcwd(), '..'))
from probe import app
from flask import request
import json
import util
import prepare

@app.route('/myplatform')
def hello():
    return 'Here is MyPlatform\n'

@app.route('/myplatform/tasks/<task_type>', methods=['POST', 'GET'])
def receive_task(task_type):
    if request.method == 'POST':
        try:
            config = json.loads(request.form['data'])
        except:
            return util.bad_request('Config must be in json format.')
        try:
            data = request.files['file']
        except:
            return util.bad_request('Failed when loading data file.')

        uuid = config.get('uuid', None)
        if uuid is None:
            return util.bad_request('A specify uuid is needed.')

        cwd = os.path.join(os.getcwd(), 'data')
        if not os.path.isdir(cwd):
            os.mkdir(cwd)
        cwd = os.path.join(cwd, task_type)
        if not os.path.isdir(cwd):
            os.mkdir(cwd)
        cwd = os.path.join(cwd, uuid)
        if not os.path.isdir(cwd):
            os.mkdir(cwd)

        with open(os.path.join(cwd, 'data'), 'wb') as f:
            f.write(data.stream.read())
        
        valid, message = getattr(prepare, task_type)(cwd, uuid, config.get('config', None), config.get('probe'))

        if not valid:
            return util.bad_request('Failed to complete task:' + message)
        return util.ok()
    else:
        try:
            getattr(prepare, task_type)
        except AttributeError:
            return util.bad_request('Such type of tasks are not supported.')
        return util.ok()
    




