from email import message
import os
import signal
import sys
sys.path.append(os.path.join(os.getcwd(), '..'))
from probe import app
from flask import request
import json
import util
import prepare
import logging
from io import StringIO
import hashlib
from pathlib import Path
import shutil
from run import PID_FILE
import subprocess

logger = logging.getLogger('probe')
errIO = StringIO()
stream_handler = logging.StreamHandler(errIO)
stream_handler.setLevel(level=logging.ERROR)
stream_handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s"))
logger.addHandler(stream_handler)

@app.route('/myplatform')
def hello():
    return 'Here is MyPlatform\n'

@app.route('/myplatform/tasks/<task_type>', methods=['POST', 'GET'])
def receive_task(task_type):
    if request.method == 'POST':
        try:
            config_size = int(request.stream.readline().strip())
            config = request.stream.read(config_size)
            if request.args.get('md5', None) != hashlib.md5(config).hexdigest():
                return util.bad_request(util.error_record('User posted config is broken.', logger, stream_handler, errIO))
            config = json.loads(config)
        except:
            return util.bad_request(util.error_record('Config must be in json format.', logger, stream_handler, errIO))
        
        uuid = config.get('uuid', None)
        if uuid is None:
            logger.error('Uuid not found.')
            return util.bad_request('A specify uuid is needed.')

        try:
            cwd = os.path.join(os.getcwd(), 'data')
            if not os.path.isdir(cwd):
                os.mkdir(cwd)
                logger.debug('Directory created:%s', cwd)
            cwd = os.path.join(cwd, task_type)
            if not os.path.isdir(cwd):
                os.mkdir(cwd)
                logger.debug('Directory created:%s', cwd)
            cwd = os.path.join(cwd, uuid)
            if not os.path.isdir(cwd):
                os.mkdir(cwd)
                logger.debug('Directory created:%s', cwd)
        except:
            logger.error('Failed when create/find working directory.', exc_info=True)
            return util.bad_request('Failed when create/find working directory.')

        try:
            data_file_loc = Path(cwd) / 'rcv_data'
            if data_file_loc.exists():
                shutil.rmtree(data_file_loc)
            Path.mkdir(data_file_loc)
            util.file_saver(request, str(data_file_loc))
            for key, value in config['md5'].items():
                if not util.integrity_check(os.path.join(str(data_file_loc), str(key)), value):
                    logger.error('User uploaded data is broken. File location:%s, md5 sent was %s', os.path.join(str(data_file_loc), str(key)), value, exc_info=True)
                    return util.bad_request('File is broken.')

        except:
            return util.bad_request(util.error_record('Fail to load data from user\'s post.', logger, stream_handler, errIO))


        logger.debug('Preparing for task %s', uuid)
        valid, message = getattr(prepare, task_type)(cwd, uuid, config.get('config', None), config.get('probe'), data_file_loc)

        if not valid:
            return util.bad_request('Failed to complete task:' + message)
        return util.ok()
    else:
        try:
            getattr(prepare, task_type)
        except AttributeError:
            logger.error('Such type \"%s\" of tasks are not supported.' % (task_type), exc_info=True)
            return util.bad_request('Such type \"%s\" of tasks are not supported.' % (task_type))
        try:
            return util.json_return(json.dumps(util.get_hw_info(os.getcwd())))
        except:
            message = 'Error occured when getting hardware info.'
            logger.error(message, exc_info=True)
            return util.bad_request(message)
    

@app.route('/myplatform/kill/<task_type>/<task_id>', methods=['GET'])
def kill_task(task_type, task_id):
    try:
        cwd = Path(Path.cwd() / 'data' / task_type / task_id)
        if not (cwd / 'killed').is_file():
            with open(cwd / PID_FILE, 'r') as f:
                pid = int(f.read().strip()) + 1
            os.kill(pid, signal.SIGKILL)
            logger.debug(f'Task with pid {str(pid)} killed')
            Path(cwd / 'killed').touch()
        return util.ok()
    except:
        message = f'Error when killing task {task_id}.'
        logger.error(message, exc_info=True)
        return util.bad_request(message)

@app.route('/myplatform/killall', methods=['GET'])
def kill_all_task():
    try:
        for cmd in ['zmap', 'zgrab']:
            exe = f"ps -ef | grep {cmd} | grep -v grep | awk '{{print $2}}'"
            output = subprocess.getoutput(exe).strip()
            if len(output) == 0:
                continue
            pid_array = output.split('\n')
            for pid in pid_array:
                logger.debug(f'kill {cmd} with pid: {pid}')
                os.kill(int(pid), signal.SIGKILL)
        return util.ok()
    except:
        message = 'Error when killing task'
        logger.error(message, exc_info=True)
        return util.bad_request(message)

