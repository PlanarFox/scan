import os
import json
import util
import logging
from io import StringIO

logger = logging.getLogger('server')
errIO = StringIO()
stream_handler = logging.StreamHandler(errIO)
stream_handler.setLevel(level=logging.ERROR)
stream_handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s"))
logger.addHandler(stream_handler)

def zmap(cwd):
    total = 0
    count = 0
    try:
        for item in os.listdir(cwd):
            path = os.path.join(cwd, item)
            if os.path.isdir(path):
                with open(os.path.join(path, 'done'), 'r') as f:
                    statistics = json.loads(f.read())
                    total += statistics['total']
                    count += statistics['hit']
        
        with open(os.path.join(cwd, 'result'), 'w') as f:
            f.writelines(['total:'+str(total), '\nhit:'+str(count), '\n-------------------\n'])
            for item in os.listdir(cwd):
                path = os.path.join(cwd, item)
                if os.path.isdir(path):
                    with open(os.path.join(path, 'result.txt'), 'r') as fp:
                        fp.readline()
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
        with open(os.path.join(cwd, 'result'), 'w') as f:
            for item in os.listdir(cwd):
                path = os.path.join(cwd, item)
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