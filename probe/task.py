import os
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
            util.file_saver(request, cwd)
            for key, value in config['md5'].items():
                if not util.integrity_check(os.path.join(cwd, str(key)), value):
                    logger.error('User uploaded data is broken. File location:%s, md5 sent was %s', os.path.join(cwd, str(key)), value)
                    return util.bad_request('File is broken.')

            #for key, _ in request.files.items():
            #    request.files[key].save(os.path.join(cwd, str(key)))
            #    if not util.integrity_check(os.path.join(cwd, str(key)), config['md5'][str(key)]):
        except:
            return util.bad_request(util.error_record('Fail to load data from user\'s post.', logger, stream_handler, errIO))


        logger.debug('Preparing for task %s', uuid)
        valid, message = getattr(prepare, task_type)(cwd, uuid, config.get('config', None), config.get('probe'))

        if not valid:
            return util.bad_request('Failed to complete task:' + message)
        return util.ok()
    else:
        try:
            getattr(prepare, task_type)
        except AttributeError:
            logger.error('Such type \"%s\" of tasks are not supported.' % (task_type))
            return util.bad_request('Such type \"%s\" of tasks are not supported.' % (task_type))
        return util.ok()
    




