import os
import sys
sys.path.append(os.path.join(os.getcwd(), '..'))
from server import app
import util
import args_is_valid
import task_creation 
from flask import request, send_file
import uuid
import json
import result

@app.route('/myplatform')
def hello():
    return 'Here is MyPlatform\n'

@app.route('/myplatform/tasks', methods=['POST'])
def create_task():
    try:
        config = json.loads(request.form['data'])
        md5 = config['md5']
        config = config['config']
    except Exception as e:
        return util.bad_request('Config must be in json format:' + e.args)
    try:
        data = request.files['file']
    except Exception as e:
        return util.bad_request('Fail when loading data file:' + e.args)
    try:
        valid, message = getattr(args_is_valid, config['type'])(config['args'])
    except AttributeError:
        return util.bad_request('Task type not supported.')
    
    if not valid:
        return util.bad_request(message=message)
    
    cwd = os.path.join(os.getcwd(), 'data')
    if not os.path.isdir(cwd):
        os.mkdir(cwd)

    cwd = os.path.join(cwd, config['type'])
    if not os.path.isdir(cwd):
        os.mkdir(cwd)

    task_id = str(uuid.uuid4())
    while os.path.isdir(os.path.join(cwd, task_id)):
        task_id = str(uuid.uuid4())
    cwd = os.path.join(cwd, task_id)
    os.mkdir(cwd)

    f = open(os.path.join(cwd, 'config.json'), 'w')
    f.write(json.dumps(config))
    f.close()

    data.save(os.path.join(cwd, 'data'))
    if not util.integrity_check(os.path.join(cwd, 'data'), md5):
        return util.bad_request('File is broken.')

    valid, message = getattr(task_creation, config['type'])(cwd, config, task_id)

    if not valid:
        return util.bad_request(message=message)
    return util.ok(util.api_url(config['scheduler']['addr'], '/result/'+config['type']+'/'+task_id, config['scheduler']['port']))
    
@app.route('/myplatform/result/<task_type>/<task_id>', methods=['GET'])
def return_result(task_type, task_id):
    cwd = os.path.join(os.path.join(os.path.join(os.getcwd(), 'data'), task_type), task_id)
    if not os.path.isdir(cwd):
        return util.bad_request('Invalid task id.')
    isdone = True
    for item in os.listdir(cwd):
        path = os.path.join(cwd, item)
        if os.path.isdir(path):
            if not os.path.isfile(os.path.join(path, 'done')):
                isdone = False
                break
    if not isdone:
        return util.bad_request('Task hasn\'t done yet.')

    valid, message = getattr(result, task_type)(cwd)
    if not valid:
        return util.bad_request(message=message)
    return send_file(os.path.join(cwd, 'result.txt'), mimetype='text/plain', as_attachment=True)
    

