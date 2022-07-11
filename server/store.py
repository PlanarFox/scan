from time import sleep
from urllib.parse import urlparse, urlunparse
import util
from pathlib import Path
import requests
import json
import logging
from io import StringIO
import task_status
from task_creation import SUB_TASK_FILE
import threading
import result
from copy import deepcopy

CONFIG_FILE = 'config.json'
PUBLIC_KEY_FILE = 'public_key.pem'
PRIVATE_KEY_FILE = 'private_key.pem'
LOGIN_PATH = '/api/login'
UPLOAD_PATH = '/api/syn/measurement_data'

logger = logging.getLogger('server')
errIO = StringIO()
stream_handler = logging.StreamHandler(errIO)
stream_handler.setLevel(level=logging.ERROR)
stream_handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s"))
logger.addHandler(stream_handler)

data_template = {
                    "ip": "",
                    "services": [
                        {
                            "title": "",
                            "banner": "",
                            "protocol": "HTTP",
                            "port": "80",
                            "product": '',
                            "version": '',
                            "request": {},
                            "response": {},
                            "source_ip": "",
                            "transport_protocol": "TCP"
                        }
                    ],
                    "location": {},
                    "autonomous_system": {},
                    "finger": ''
                }

def upload(data, api, crypto):
    message = ''
    for _ in range(5):
        r = requests.post(url=api, data=json.dumps({"data":crypto.encrypt(json.dumps(data))}))
        if r.status_code == 200:
            break
        message += (r.text + '\n')
        sleep(10)
    if r.status_code != 200:
        raise Exception(message)
    

def store_single_task_result(cwd, uuid, task_type, api, token, crypto, success_only):
    cwd = Path(cwd)
    if not (cwd / result.SINGLE_RESULT_FILENAME).exists():
        valid, message = getattr(result, task_type)(cwd)
        if not valid:
            logger.error(message)
            return

    config = json.load(open(cwd / 'config.json', 'r'))
    port = config['args']['port']

    #TODO: 添加多线程上传
    line_count = 0
    upload_data = {
            "data": [],
            "data_type": "1",
            "token": token
        }

    with open(cwd / result.SINGLE_RESULT_FILENAME, 'r') as f:
        while line := f.readline():
            json_data = deepcopy(data_template)
            if task_type in ['zmap']:
                json_data['ip'] = line.strip()
                json_data['services'][0]['port'] = str(port)
                json_data['services'][0]['protocol'] = 'TCP'
            else:
                json_line = json.loads(line)
                json_data['ip'] = json_line['ip']
                json_data['services'].clear()
                for protocol, info in json_line['data'].items():
                    if success_only and info['status'] != 'success':
                        continue
                    json_protocol = deepcopy(data_template['services'][0])
                    json_protocol['protocol'] = protocol
                    json_protocol['port'] = str(port)
                    json_protocol['response'] = info['result']
                    json_data['services'].append(json_protocol)
            upload_data['data'].append(json_data)
            line_count += 1
            if line_count >= 20000:
                try:
                    upload(upload_data, api, crypto)
                except:
                    logger.error('Fail when uploading data to database.', exc_info=True)
                    return
                upload_data['data'].clear()
        if len(upload_data['data']) != 0:
            try:
                upload(upload_data, api, crypto)
            except:
                logger.error('Fail when uploading data to database.', exc_info=True)
                return
        logger.info(f'Result of task {uuid} has been uploaded to database.')
                

def store_result(cwd, uuid):
    cwd, uuid = util.get_parent_task_dir(cwd, uuid)
    with open(Path(cwd) / CONFIG_FILE, 'r') as f:
        config = json.load(f)
    if config.get('db', None) is None:
        return
    
    isdone, message = task_status.task_status(cwd, uuid, True)
    if not isdone:
        if 'error' in message:
            logger.warning(f'Result cannot be stored because error occured when finishing task {uuid}.')
        else:
            logger.debug(f'Task {uuid} is not finished. Nothing to store.')
        return
    
    try:
        login_info = {
            "username": config['db']['username'],
            "password": config['db']['password']
        }
        task_type = config['type']
        success_only = config['db'].get('success_only', False)

        base_url = config['db']['addr']
        public_key = None if config['db'].get('public_key', None) is None else open(PUBLIC_KEY_FILE, 'r').read()
        private_key = None if config['db'].get('private_key', None) is None else open(PRIVATE_KEY_FILE, 'r').read()

        u = urlparse(base_url)
        login_url = urlunparse(u._replace(path=LOGIN_PATH))
        crypto = util.Rsa_Crypto(public_key, private_key)
        r = requests.post(url=login_url, data = json.dumps({'data':crypto.encrypt(json.dumps(login_info))}))
        if r.status_code != 200:
            raise Exception(f'Login fail when storing result.\n{r.text}')
        token = r.json()['data']['token']

        api_url = urlunparse(u._replace(path=UPLOAD_PATH))
        if (Path(cwd) / SUB_TASK_FILE).exists():
            sub_tasks = list(map(str.strip, open(Path(cwd, SUB_TASK_FILE)).readlines()))
            for sub_task in sub_tasks:
                sub_tasks_dir = Path(cwd).resolve().parent / sub_task
                t1 = threading.Thread(target=store_single_task_result,
                                        args=(sub_tasks_dir, uuid, task_type, api_url, token, crypto, success_only))
                t1.start()
        else:
            store_single_task_result(cwd, uuid, task_type, api_url, token, crypto, success_only)
    except:
        logger.error(f'Store result of task {uuid} failed.', exc_info=True)
