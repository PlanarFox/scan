import json
import requests
import subprocess
import util
import os
import time
import logging
from io import StringIO

logger = logging.getLogger('probe')
errIO = StringIO()
stream_handler = logging.StreamHandler(errIO)
stream_handler.setLevel(level=logging.ERROR)
stream_handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s"))
logger.addHandler(stream_handler)

def zmap(cwd, uuid, config, ip, myaddr, **kw):
    command = '/usr/local/sbin/zmap -O csv'
    args = config.get('args', None)
    if args is not None:
        for key, item in args['args'].items():
            command += ' ' + key + ' ' + item
    command += ' --ipv6-source-ip=\"' + ip[0] + '\"'
    command += ' --ipv6-target-file=\"' + os.path.join(cwd, 'target.txt') + '\"'
    command += ' -o \"' + os.path.join(cwd, 'output.csv') + '\"'
    error_message = None
    result = None
    try:
        result = subprocess.run(command, shell=True, stdout=None, 
                                stderr=subprocess.PIPE, encoding='utf-8', check=False)
        logger.debug('Running command:%s', command)
    except:
        error_message = util.error_record('Fail when running command:%s' % (command), logger, stream_handler, errIO)
        with open(os.path.join(cwd, 'output.csv'), 'w') as f:
            f.write(error_message)
    if result is not None:
        if result.returncode != 0:
            error_message = util.error_record('Fail when running command:%s\n%s' % (command, result.stderr), logger, stream_handler, errIO)
            with open(os.path.join(cwd, 'output.csv'), 'w') as f:
                f.write(error_message)
                
    url = util.api_url(config['scheduler']['addr'], '/submit/zmap', config['scheduler']['port'])
    for i in range(5):
        try:
            md5 = util.gen_md5(os.path.join(cwd, 'output.csv'))
            with open(os.path.join(cwd, 'output.csv'), 'rb') as f:
                r = requests.post(url, files = {'file':f},
                                    data = {'data':json.dumps({'uuid':uuid, 'addr':myaddr, 
                                                               'md5':md5, 'error':error_message is not None})})
            if r.status_code == 200:
                break
        except:
            time.sleep(1.0)
            continue

    




