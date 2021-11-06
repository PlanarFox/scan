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


def zmap(cwd, uuid, config, net_info, myaddr, **kw):
    try:
        command = '/usr/local/sbin/zmap -O csv'
        args = config.get('args', None)
        if args is not None:
            for key, item in args['args'].items():
                if key != '--ipv6-source-ip' and key != '--ipv6-target-file' and key != '-o':
                    command += ' ' + key + ' ' + item
        if args.get('ipv6', None) == 'disable':
            if args.get('blacklist', None) == 'enable':
                command += ' --blocklist-file=\"' + os.path.join(cwd, 'target.txt') + '\"'
            else:
                command += ' --allowlist-file=\"' + os.path.join(cwd, 'target.txt') + '\"'
            probe_spec_conf = args.get('probe', None)
            if isinstance(probe_spec_conf, dict):
                probe_spec_conf = probe_spec_conf.get(myaddr, None)
                for key, item in probe_spec_conf.items():
                    if key == '-i':
                        net_info[1] = item
                    elif key == '-G':
                        net_info[2] = item
                    else:
                        command += ' ' + key + ' ' + item
        else:
            probe_spec_conf = args.get('probe', None)
            if isinstance(probe_spec_conf, dict):
                probe_spec_conf = probe_spec_conf.get(myaddr, None)
                for key, item in probe_spec_conf.items():
                    if key == '--ipv6-source-ip':
                        net_info[0] = item
                    elif key == '-i':
                        net_info[1] = item
                    elif key == '-G':
                        net_info[2] = item
                    else:
                        command += ' ' + key + ' ' + item
            command += ' --ipv6-source-ip=\"' + net_info[0] + '\"'
            command += ' --ipv6-target-file=\"' + os.path.join(cwd, 'target.txt') + '\"'

        if net_info[1] is not None:
            command += ' -i \"' + net_info[1] + '\"'
        if net_info[2] is not None:
            command += ' -G \"' + net_info[2] + '\"'
        
        command += ' -o \"' + os.path.join(cwd, 'output.csv') + '\"'
        error_message = run_command(command, os.path.join(cwd, 'output.csv'))      
        
        url = util.api_url(config['scheduler']['addr'], '/submit/zmap', config['scheduler']['port'])
        for i in range(5):
            try:
                file_dict = {os.path.join(cwd, 'output.csv'):'result.txt'}
                md5 = util.gen_md5(os.path.join(cwd, 'output.csv'))
                integrated, conf_md5 = util.file_integrater(file_dict, \
                                    json.dumps({'uuid':uuid, 'addr':myaddr, \
                                                'md5':{'result.txt':md5}, 'error':error_message is not None}))
                with open(integrated, 'rb') as f:
                    r = requests.post(url, data = f, params={'md5':conf_md5}, stream=True)
                if r.status_code == 200:
                    os.remove(integrated)
                    break
            except:
                time.sleep(1.0)
                logger.error('Task POST failed %d time(s)\n' % (i), exc_info=True)
                continue
    except:
        logger.error('Error when running zmap task.\n', exc_info=True)

def zgrab(cwd, uuid, config, myaddr, **kw):
    try:
        try:
            zgrab_type = config['args']['type']
        except:
            raise logger.error('Zgrab task type of task %s not found' % (uuid), logger, stream_handler, errIO)

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
                file_dict = {os.path.join(cwd, 'output.json'):'result.json'}
                md5 = util.gen_md5(os.path.join(cwd, 'output.json'))
                integrated, conf_md5 = util.file_integrater(file_dict, 
                                    json.dumps({'uuid':uuid, 'addr':myaddr, \
                                                'md5':{'result.json':md5}, 'error':error_message is not None}))
                logger.debug('Trying to POST result of task %s', uuid)
                with open(integrated, 'rb') as f:
                    r = requests.post(url, data = f, params={'md5':conf_md5}, stream=True)
                if r.status_code == 200:
                    logger.info('Task POST success, uuid:%s', uuid)
                    os.remove(integrated)
                    break
            except:
                time.sleep(1.0)
                logger.error('Task POST failed %d time(s)\n' % (i), exc_info=True)
                continue
        logger.error('Task POST failed, uuid:%s', uuid)
    except:
        logger.error('Error when running zgrab task.\n', exc_info=True)
                




