import hashlib
import os
from pathlib import Path
import sys
sys.path.append(os.path.join(os.getcwd(), '..'))
from server import app
import util
import args_is_valid
import task_creation 
from task_status import task_status
from flask import request
import uuid
import json
import result
import logging
from io import StringIO
import kill

CONFIG_FILE = 'config.json'

logger = logging.getLogger('server')
errIO = StringIO()
stream_handler = logging.StreamHandler(errIO)
stream_handler.setLevel(level=logging.ERROR)
stream_handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s"))
logger.addHandler(stream_handler)

@app.route('/myplatform')
def hello():
    return 'Here is MyPlatform\n'

@app.route('/myplatform/tasks', methods=['POST'])
def create_task():
    try:
        config_size = int(request.stream.readline().strip())
        config = request.stream.read(config_size)
        if request.args.get('md5', None) != hashlib.md5(config).hexdigest():
            return util.bad_request(util.error_record('User posted config is broken.', logger, stream_handler, errIO))
        config = json.loads(config)
        md5 = config.get('md5', None)
        config = config['config']
    except Exception as e:
        return util.bad_request(util.error_record('Fail to load config from user\'s post.', logger, stream_handler, errIO))
    try:
        valid, message = getattr(args_is_valid, config['type'])(config['args'])
    except AttributeError:
        logger.error('Task type defined by user is not supported.')
        return util.bad_request('Task type not supported.')
    
    if not valid:
        logger.error(message)
        return util.bad_request(message=message)
    else:
        info_dict = message
    
    try:
        cwd = os.path.join(os.getcwd(), 'data')
        if not os.path.isdir(cwd):
            os.mkdir(cwd)
            logger.debug('Directory created:%s', cwd)

        cwd = os.path.join(cwd, config['type'])
        if not os.path.isdir(cwd):
            os.mkdir(cwd)
            logger.debug('Directory created:%s', cwd)
    except:
        logger.error('Failed when create/find parent directory of task', exc_info=True)
        return util.bad_request('Failed when create/find parent directory of task')

    task_id = str(uuid.uuid4())
    while os.path.isdir(os.path.join(cwd, task_id)):
        task_id = str(uuid.uuid4())
    try:
        cwd = os.path.join(cwd, task_id)
        os.mkdir(cwd)
        logger.debug('Directory created:%s', cwd)
    except:
        logger.error('Failed when create task directory', exc_info=True)
        return util.bad_request('Failed when create task directory')

    f = open(os.path.join(cwd, CONFIG_FILE), 'w')
    f.write(json.dumps(config))
    f.close()

    try:
        util.file_saver(request, cwd)
        if isinstance(md5, dict):
            for key, value in md5.items():
                if not util.integrity_check(os.path.join(cwd, str(key)), value):
                    logger.error('User uploaded data is broken. File location:%s, md5 sent was %s', os.path.join(cwd, str(key)), value)
                    return util.bad_request('File is broken.')
    except:
        return util.bad_request(util.error_record('Fail to load data from user\'s post.', logger, stream_handler, errIO))

    #valid, message = getattr(task_creation, config['type'])(cwd, config, task_id, info_dict)
    valid, message = task_creation.create(cwd, config, task_id, info_dict)

    if not valid:
        return util.bad_request(message=message)
    logger.info('Task distributed.')
    return util.ok(util.api_url(config['scheduler']['addr'], '/result/'+config['type']+'/'+task_id, config['scheduler']['port']))
    
@app.route('/myplatform/result/<task_type>/<task_id>', methods=['GET'])
def return_result(task_type, task_id):
    cwd = os.path.join(os.path.join(os.path.join(os.getcwd(), 'data'), task_type), task_id)
    if not os.path.isdir(cwd):
        logger.error('Task not found:%s', task_id)
        return util.bad_request('Invalid task id.')
    
    isdone, message = task_status(cwd, task_id)
    if not isdone:
        logger.error(message)
        return util.bad_request(message)
    
    return result.get_task_result(cwd, task_type)

    #return send_file(os.path.join(cwd, 'result'), mimetype='text/plain', as_attachment=True)
    
@app.route('/myplatform/kill/<task_type>/<task_id>', methods=['GET'])
def kill_task(task_type, task_id):
    cwd = Path(Path.cwd() / 'data' / task_type / task_id)
    if not cwd.is_dir():
        logger.error('Task not found:%s', task_id)
        return util.bad_request('Invalid task id.')
    
    isdone, message = task_status(cwd, task_id)
    if isdone:
        return util.bad_request('Task has done.')
    
    if (cwd / 'killed').is_file():
        return util.bad_request('Task has been killed.')

    try:
        r = kill.kill_task(cwd, task_type, task_id)
        if r is not None:
            return util.bad_request(r)
        else:
            return util.ok()
    except:
        message = 'Failed when killing tasks.'
        logger.error(message, exc_info=True)
        return util.bad_request(message)
    