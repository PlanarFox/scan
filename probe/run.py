import json
from pathlib import Path
import shutil
import requests
import subprocess
import util
import os
import time
import logging
from io import StringIO

SHARD_UPPER_BOUND = 10

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
        logger.info('Running command:%s', command)
        result = subprocess.run(command, shell=True, stdout=None,
                                stderr=subprocess.PIPE, encoding='utf-8', check=True)
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

def file_sender(url, file_dict, cwd, config, uuid):
    for i in range(5):
        try:
            integrated, conf_md5 = util.file_integrater(file_dict, cwd, config)
            logger.debug('Trying to POST result of task %s', uuid)
            with open(integrated, 'rb') as f:
                r = requests.post(url, data = f, params={'md5':conf_md5}, stream=True)
            if r.status_code == 200:
                logger.info('Task POST success, uuid:%s', uuid)
                os.remove(integrated)
                break
        except:
            time.sleep(15)
            logger.error('Task POST failed %d time(s)\n' % (i), exc_info=True)
            continue

def zmap_command_parser(cwd, args, net_info, myaddr, ipv6, input_file):
    command = '/usr/local/sbin/zmap'
    if args is not None:
        filt_out_list = ['--ipv6-source-ip', '--ipv6-target-file', '-i', '-G', '--blocklist-file', '--allowlist-file']
        for key, item in args['args'].items():
            if key not in filt_out_list:
                if item != '':
                    command += ' ' + key + ' ' + item
                else:
                    command += ' ' + key
    if not ipv6:
        if args.get('blacklist', None) == 'enable':
            command += ' --blocklist-file=\"' + input_file + '\"'
        else:
            command += ' --allowlist-file=\"' + input_file + '\"'
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
        command += ' --ipv6-target-file=\"' + input_file + '\"'

    if net_info[1] is not None:
        command += ' -i \"' + net_info[1] + '\"'
    if net_info[2] is not None:
        command += ' -G \"' + net_info[2] + '\"'
    
    return command

def zgrab_command_parser(zgrab_type, zgrab_args, cwd):
    command = '/usr/local/sbin/zgrab ' + str(zgrab_type)
    if isinstance(zgrab_args, dict):
        filt_out_list = ['-c']
        for key, item in zgrab_args.items():
            if key not in filt_out_list:
                if item != '':
                    command += ' ' + key + ' ' + item
                else:
                    command += ' ' + key
    if os.path.isfile(os.path.join(cwd, 'mul')) and zgrab_type == 'multiple':
        with open(os.path.join(cwd, 'mul.ini'), 'w') as fw:
            with open(os.path.join(cwd, 'mul'), 'r') as fr:
                #origin = fr.readlines()
                for line in fr.readlines():
                    if 'output-file' not in line and 'input-file' not in line:
                        fw.writelines(line)
                #fw.writelines('[Application Options]\n')                
                #fw.writelines(origin[3:])
        command += ' -c \"' + os.path.join(cwd, 'mul.ini') + '\"'
    return command

def lzr_command_parser(cwd, args, net_info, ipv6):
    command = '/usr/local/sbin/lzr'
    if ipv6:
        command += ' -6'
    args['-sendInterface'] = '\"' + net_info[1] + '\"'
    args['-gatewayMac'] = '\"' + net_info[2] + '\"'
    args['-sourceIP'] = '\"' + net_info[0] + '\"'
    for key, item in args.items():
        command += ' ' + key + ' ' + item
    return command
    
def target_generator(cwd, target_files_loc, upper_bound) -> Path():
    target_files = list(Path(target_files_loc).iterdir())
    target_idx = 0
    round_count = 0
    line_count = 0
    no_more_file = False
    # TODO:根据内存大小判断读取地址数目
    load_file = open(target_files[target_idx], 'r')
    while True:
        input_file_loc = os.path.join(cwd, f'target-{round_count}.txt')
        with open(input_file_loc, 'w') as input_file:
            while line_count < upper_bound:
                while (line:= load_file.readline()) and (line_count < upper_bound):
                    input_file.writelines(line)
                    line_count += 1
                if line_count < upper_bound:
                    load_file.close()                    
                    target_idx += 1
                    if target_idx == len(target_files):
                        no_more_file = True
                        break
                    load_file = open(target_files[target_idx], 'r')
        yield input_file_loc
        if no_more_file:
            return
        line_count = 0
        round_count += 1
        


def zmap(cwd, uuid, config, net_info, myaddr, ipv6, target_files_loc, **kw):
    try:
        args = config.get('args', None)
        output_dir = os.path.join(cwd, 'output_single.csv')
        full_output_dir = os.path.join(cwd, 'output.csv')

        if not isinstance(args, dict):
            args = dict()
            args['args'] = dict()
        args['args']['-O'] = 'csv'
        args['args']['-o'] = '\"' + output_dir + '\"'

        try:
            input_file_gen = target_generator(cwd, target_files_loc, SHARD_UPPER_BOUND)
            while True:
                input_dir = next(input_file_gen)
                command = zmap_command_parser(cwd, args, net_info, myaddr, ipv6, input_dir)
                error_message = run_command(command, output_dir)
                if error_message is None:
                    with open(full_output_dir, 'a') as  write_f:
                        with open(output_dir, 'r') as read_f:
                            read_f.readline()
                            while line:= read_f.readline():
                                write_f.writelines(line)
                    os.remove(output_dir)
                    os.remove(input_dir)
                else:
                    Path(output_dir).replace(full_output_dir)
                    break
        except StopIteration:
            logger.debug('all target addresses have been covered.')
              
        
        url = util.api_url(config['scheduler']['addr'], '/submit/zmap', config['scheduler']['port'])
        file_dict = {full_output_dir:'result.txt'}
        md5 = util.gen_md5(full_output_dir)
        json_conf = json.dumps({'uuid':uuid, 'addr':myaddr, \
                                'md5':{'result.txt':md5}, 'error':error_message is not None})
        file_sender(url, file_dict, cwd, json_conf, uuid)
    except:
        logger.error('Error when running zmap task.\n', exc_info=True)

def zgrab(cwd, uuid, config, myaddr, target_files_loc, **kw):
    try:
        try:
            zgrab_type = config['args']['type']
        except:
            raise Exception(logger.error('Zgrab task type of task %s not found' % (uuid), logger, stream_handler, errIO))
        zgrab_args = config['args'].get('args', None)
        if not isinstance(zgrab_args, dict):
            zgrab_args = dict()
        zgrab_args['-f'] = '\"' + os.path.join(cwd, 'target.txt') + '\"'
        zgrab_args['-o'] = '\"' + os.path.join(cwd, 'output.json') + '\"'
        command = zgrab_command_parser(zgrab_type, zgrab_args, cwd)

        error_message = run_command(command, os.path.join(cwd, 'output.json'))
        url = util.api_url(config['scheduler']['addr'], '/submit/zgrab', config['scheduler']['port'])
        file_dict = {os.path.join(cwd, 'output.json'):'result.json'}
        md5 = util.gen_md5(os.path.join(cwd, 'output.json'))
        json_conf = json.dumps({'uuid':uuid, 'addr':myaddr, \
                                'md5':{'result.json':md5}, 'error':error_message is not None})
        file_sender(url, file_dict, cwd, json_conf, uuid)

    except:
        logger.error('Error when running zgrab task.\n', exc_info=True)
                
def zMnG(cwd, uuid, config, net_info, myaddr, ipv6, target_files_loc, **kw):
    try:
        try:
            zgrab_type = config['args']['zgrab']['type']
        except:
            raise logger.error('Zgrab task type of task %s not found' % (uuid), logger, stream_handler, errIO)

        args = config.get('args', None)
        if isinstance(args, dict):
            args = args.get('zmap')
        else:
            args = dict()
            args['args'] = dict()
        args['args']['-O'] = 'csv'
        args['args']['-o'] = os.path.join(cwd, 'zmap_result.csv')

        command = zmap_command_parser(cwd, args, net_info, myaddr, ipv6)
        error_message = run_command(command, os.path.join(cwd, 'zmap_result.csv'))
        if error_message is not None:
            file_dict = {os.path.join(cwd, 'zmap_result.csv'):'result.json'}
            md5 = util.gen_md5(os.path.join(cwd, 'zmap_result.csv'))
            json_conf = json.dumps({'uuid':uuid, 'addr':myaddr, \
                                'md5':{'result.json':md5}, 'error':error_message is not None})
        else:
            command = os.path.join(os.getcwd(), 'sort.sh') + ' ' + \
                        'zmap_result.csv' + ' ' + \
                        'zmap_sorted.csv' + ' ' + \
                        cwd
            error_message = run_command(command, os.path.join(cwd, 'output.json'))

            if error_message is None:
                zgrab_args = config['args']['zgrab'].get('args', None)
                if not isinstance(zgrab_args, dict):
                    zgrab_args = dict()
                zgrab_args['-f'] = os.path.join(cwd, 'zmap_sorted.csv')
                zgrab_args['-o'] = '\"' + os.path.join(cwd, 'output.json') + '\"'
                command = zgrab_command_parser(zgrab_type, zgrab_args, cwd)

                error_message = run_command(command, os.path.join(cwd, 'output.json'))
            file_dict = {os.path.join(cwd, 'output.json'):'result.json'}
            md5 = util.gen_md5(os.path.join(cwd, 'output.json'))
            json_conf = json.dumps({'uuid':uuid, 'addr':myaddr, \
                                    'md5':{'result.json':md5}, 'error':error_message is not None})
        url = util.api_url(config['scheduler']['addr'], '/submit/zMnG', config['scheduler']['port'])
        file_sender(url, file_dict, cwd, json_conf, uuid)
    except:
        logger.error('Error when running zmap&zgrab task.\n', exc_info=True)

def lzr(cwd, uuid, config, net_info, myaddr, ipv6, target_files_loc, **kw):
    try:
        zmap_args = config.get('args', None)
        if isinstance(zmap_args, dict):
            zmap_args = zmap_args.get('zmap')
        else:
            zmap_args = dict()
            zmap_args['args'] = dict()
        zmap_args['args']['-O'] = 'json'
        zmap_args['args']['-f'] = '"saddr,daddr,sport,dport,seqnum,acknum,window"'
        port = zmap_args['args']['-p']

        command = zmap_command_parser(cwd, zmap_args, net_info, myaddr, ipv6)

        lzr_args = config.get('args', None)
        if isinstance(lzr_args, dict):
            lzr_args = lzr_args.get('lzr')
        else:
            lzr_args = dict()
        lzr_args['-feedZGrab'] = ''
        lzr_args['-f'] = '\"/dev/null\"'
        command += ' | ' + lzr_command_parser(cwd, lzr_args, net_info, ipv6)

        with open(os.path.join(os.getcwd(), 'lzr_zgrab.ini'), 'r') as fr:
            with open(os.path.join(cwd, 'zgrab.ini'), 'w') as fw:
                for line in fr.readlines():
                    if 'port=x' in line:
                        fw.writelines('port=' + port + '\n')
                    else:
                        fw.writelines(line)
        
        command += ' | /usr/local/sbin/zgrab multiple -c \"'
        command += os.path.join(cwd, 'zgrab.ini')
        command += '\" -o \"' + os.path.join(cwd, 'output.json') + '\"'

        error_message = run_command(command, os.path.join(cwd, 'output.json'))
        url = util.api_url(config['scheduler']['addr'], '/submit/lzr', config['scheduler']['port'])
        file_dict = {os.path.join(cwd, 'output.json'):'result.json'}
        md5 = util.gen_md5(os.path.join(cwd, 'output.json'))
        json_conf = json.dumps({'uuid':uuid, 'addr':myaddr, \
                                'md5':{'result.json':md5}, 'error':error_message is not None})
        file_sender(url, file_dict, cwd, json_conf, uuid)
        
    except:
        logger.error('Error when running LZR task.\n', exc_info=True)