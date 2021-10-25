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

def run_command(command, error_file):
    result = None
    error_message = None
    try:
        result = subprocess.run(command, shell=True, stdout=None,
                                stderr=subprocess.PIPE, encoding='utf-8', check=False)
        logger.info('Running command:%s', command)
    except:
        error_message = util.error_record('Fail when running command:%s' % (command), logger, stream_handler, errIO)
        with open(error_file, 'w') as f:
            f.write(error_message)
    if result is not None:
        if result.returncode != 0:
            error_message = util.error_record('Fail when running command:%s\n%s' % (command, result.stderr), logger, stream_handler, errIO)
            with open(error_file, 'w') as f:
                f.write(error_message)
    return error_message


def zmap(cwd, uuid, config, ip, myaddr, **kw):
    command = '/usr/local/sbin/zmap -O csv'
    args = config.get('args', None)
    if args is not None:
        for key, item in args['args'].items():
            if key != '--ipv6-source-ip' and key != '--ipv6-target-file' and key != '-o':
                command += ' ' + key + ' ' + item
    if config.get('ipv6', None) == 'disable':
        if config.get('blacklist', None) == 'enable':
            command += ' --blocklist-file=\"' + os.path.join(cwd, 'target.txt') + '\"'
        else:
            command += ' --allowlist-file=\"' + os.path.join(cwd, 'target.txt') + '\"'
    else:
        command += ' --ipv6-source-ip=\"' + ip[0] + '\"'
        command += ' --ipv6-target-file=\"' + os.path.join(cwd, 'target.txt') + '\"'
    command += ' -o \"' + os.path.join(cwd, 'output.csv') + '\"'
    error_message = run_command(command, os.path.join(cwd, 'output.csv'))      
    
    url = util.api_url(config['scheduler']['addr'], '/submit/zmap', config['scheduler']['port'])
    for i in range(5):
        try:
            md5 = util.gen_md5(os.path.join(cwd, 'output.csv'))
            with open(os.path.join(cwd, 'output.csv'), 'rb') as f:
                r = requests.post(url, files = {'result.txt':f},
                                    data = {'data':json.dumps({'uuid':uuid, 'addr':myaddr, 
                                                               'md5':{'result.txt':md5}, 'error':error_message is not None})})
            if r.status_code == 200:
                break
        except:
            time.sleep(1.0)
            continue

def zgrab(cwd, uuid, config, myaddr, **kw):
    try:
        zgrab_type = config['args']['type']
    except:
        raise Exception(util.error_record('Zgrab task type of task %s not found' % (uuid), logger, stream_handler, errIO))

    command = '/usr/local/sbin/zgrab ' + str(zgrab_type)
    command += ' -f \"' + os.path.join(cwd, 'target.txt') + '\"'
    command += ' -o \"' + os.path.join(cwd, 'output.json') + '\"'
    if os.path.isfile(os.path.join(cwd, 'mul')) and zgrab_type == 'multiple':
        with open(os.path.join(cwd, 'mul.ini'), 'w') as fw:
            with open(os.path.join(cwd, 'mul'), 'r') as fr:
                origin = fr.readlines()
                fw.writelines('[Application Options]\n')
                fw.writelines('output-file=\"%s\"\n' % (os.path.join(cwd, 'output.json')))
                fw.writelines('input-file=\"%s\"\n' % (os.path.join(cwd, 'target.txt')))
                fw.writelines(origin[3:])
        command += ' -c \"' + os.path.join(cwd, 'mul.ini') + '\"'
    error_message = run_command(command, os.path.join(cwd, 'output.json'))
    url = util.api_url(config['scheduler']['addr'], '/submit/zgrab', config['scheduler']['port'])
    for i in range(5):
        try:
            md5 = util.gen_md5(os.path.join(cwd, 'output.json'))
            with open(os.path.join(cwd, 'output.json'), 'rb') as f:
                r = requests.post(url, files = {'result.json':f},
                                    data = {'data':json.dumps({'uuid':uuid, 'addr':myaddr, 
                                                               'md5':{'result.json':md5}, 'error':error_message is not None})})
            if r.status_code == 200:
                break
        except:
            time.sleep(1.0)
            continue
                




