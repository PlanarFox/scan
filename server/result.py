import os
import json
from pathlib import Path
import zipfile
import util
import logging
from io import StringIO
from flask import Response
import sys
sys.path.append(os.path.join(os.getcwd(), '..'))
from task_creation import SUB_TASK_FILE

RESULT_ZIP_FILE = 'result.zip'
SINGLE_RESULT_FILENAME = 'result'

logger = logging.getLogger('server')
errIO = StringIO()
stream_handler = logging.StreamHandler(errIO)
stream_handler.setLevel(level=logging.ERROR)
stream_handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s"))
logger.addHandler(stream_handler)

def generate(filepath):
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(1048576)
            if not chunk:
                break
            yield chunk


def zmap(cwd):
    total = 0
    count = 0
    try:
        '''
        for item in os.listdir(cwd):
            path = os.path.join(cwd, item)
            if os.path.isdir(path):
                with open(os.path.join(path, 'done'), 'r') as f:
                    statistics = json.loads(f.read())
                    total += statistics['total']
                    count += statistics['hit']
        '''
        
        with open(os.path.join(cwd, SINGLE_RESULT_FILENAME), 'w') as f:
            #f.writelines(['total:'+str(total), '\nhit:'+str(count), '\n-------------------\n'])
            probe_path = os.path.join(cwd, 'probe')
            for item in os.listdir(probe_path):
                path = os.path.join(probe_path, item)
                if os.path.isdir(path):
                    with open(os.path.join(path, 'result_sorted.txt'), 'r') as fp:
                        while True:
                            line = fp.readline()
                            if not line:
                                break
                            f.writelines(line)
                        
    except Exception as e:
        return False, util.error_record('Failed when generating result.', logger, stream_handler, errIO)
    
    return True, None

def zgrab(cwd):
    try:
        with open(os.path.join(cwd, SINGLE_RESULT_FILENAME), 'w') as f:
            probe_path = os.path.join(cwd, 'probe')
            for item in os.listdir(probe_path):
                path = os.path.join(probe_path, item)
                if os.path.isdir(path):
                    with open(os.path.join(path, 'result.json'), 'r') as fp:
                        while True:
                            chunk = fp.read(2048)
                            if not chunk:
                                break
                            f.write(chunk)
    except:
        return False, util.error_record('Failed when generating result.', logger, stream_handler, errIO)
    return True, None

def zMnG(cwd):
    valid, message = zgrab(cwd)
    return valid, message

def lzr(cwd):
    valid, message = zgrab(cwd)
    return valid, message

def get_task_result(cwd, task_type) -> Response:
    try:
        mod = sys.modules[__name__]
        if (Path(cwd) /SUB_TASK_FILE).exists():
            sub_tasks = list(map(str.strip, open(Path(cwd, SUB_TASK_FILE)).readlines()))
            result_zip_path = Path(cwd) / RESULT_ZIP_FILE
            all_result = zipfile.ZipFile(result_zip_path, 'w', zipfile.ZIP_DEFLATED)
            cwd = Path(cwd).resolve().parent
            for sub_task in sub_tasks:
                valid, message = getattr(mod, task_type)(cwd / sub_task)
                if not valid:
                    return util.bad_request(message)
                else:
                    with open(cwd / sub_task / 'config.json', 'r') as f:
                        conf = json.load(f)
                    all_result.write(cwd / sub_task / SINGLE_RESULT_FILENAME, arcname=f'{conf["args"]["port"]}.txt')
            all_result.close()
            response = Response(generate(result_zip_path), mimetype='application/zip')
            response.headers['Content-Disposition'] = f'attachment; filename={RESULT_ZIP_FILE}'
            response.headers['content-length'] = os.path.getsize(str(result_zip_path))
        else:
            valid, message = getattr(mod, task_type)(cwd)
            if not valid:
                return util.bad_request(message)
            response = Response(generate(Path(cwd) / SINGLE_RESULT_FILENAME), mimetype='text/plain')
            response.headers['Content-Disposition'] = f'attachment; filename={SINGLE_RESULT_FILENAME}'
            response.headers['content-length'] = os.path.getsize(str(Path(cwd) / SINGLE_RESULT_FILENAME))
        return response
    except:
        return util.bad_request(util.error_record('Failed when generating result.', logger, stream_handler, errIO))


        
