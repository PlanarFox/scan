import json
import os
import json
from pathlib import Path
import util
import logging
from io import StringIO
import subprocess

logger = logging.getLogger('server')
errIO = StringIO()
stream_handler = logging.StreamHandler(errIO)
stream_handler.setLevel(level=logging.ERROR)
stream_handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s"))
logger.addHandler(stream_handler)


def zmap(cwd, uuid, probe, error, **kw):
    probe_cwd = str(Path(cwd) / 'probe' / probe)
    try:
        if error:
            os.rename(os.path.join(probe_cwd, 'result.txt'), os.path.join(probe_cwd, 'error'))
            logger.debug('Error file renamed.')
        if not os.path.isfile(os.path.join(probe_cwd, 'done')):
            count = 0
            total_num = 0
            has_total = False
            command = os.path.join(os.getcwd(), 'sort.sh') + ' ' + \
                        'result.txt' + ' ' + \
                        'result_sorted.txt' + ' ' + \
                        probe_cwd
            cmdResult = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            logger.info('Running command:%s\n%s', command, cmdResult.stdout)
            if cmdResult.returncode != 0:
                return False, util.error_record('Failed when sorting result:\n%s' % (cmdResult.stderr), logger, stream_handler, errIO)
            '''
            with open(os.path.join(probe_cwd, 'result_sorted.txt'), 'r') as result:
                while True:
                    result_line = result.readline()
                    if not result_line:
                        break
                    if result_line != '\n':
                        count += 1
            with open(os.path.join(probe_cwd, 'target.txt'), 'r') as target:
                while True:
                    line = target.readline()
                    if not line:
                        break
                    if line != '\n':
                        total_num += 1 
            '''
            with open(os.path.join(probe_cwd, 'done'), 'w') as f:
                #f.write(json.dumps({'total':total_num, 'hit':count}))
                f.write('done')
            logger.info('Result of task %s, probe %s has analysed', uuid, probe)
        else:
            logger.info('Result of task %s, probe %s has already been uploaded.', uuid, probe)
            
    except Exception as e:
        return False, util.error_record('Failed when analysing result.', logger, stream_handler, errIO) 
    return True, None

def zgrab(cwd, uuid, probe, error, **kw):
    probe_cwd = os.path.join(cwd, probe)
    try:
        if error:
            os.rename(os.path.join(probe_cwd, 'result.json'), os.path.join(probe_cwd, 'error'))
            logger.debug('Error file renamed.')
        if not os.path.isfile(os.path.join(probe_cwd, 'done')):
            with open(os.path.join(probe_cwd, 'done'), 'w') as f:
                f.writelines('done.')
            logger.info('Result of task %s, probe %s has analysed', uuid, probe)
        else:
            logger.info('Result of task %s, probe %s has already been uploaded.', uuid, probe)
    except:
        return False, util.error_record('Failed when analysing result.', logger, stream_handler, errIO) 
    return True, None

def zMnG(cwd, uuid, probe, error, **kw):
    valid, message = zgrab(cwd, uuid, probe, error)
    return valid, message

def lzr(cwd, uuid, probe, error, **kw):
    valid, message = zgrab(cwd, uuid, probe, error)
    return valid, message