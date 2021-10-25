import json
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


def zmap(cwd, uuid, probe, error, **kw):
    probe_cwd = os.path.join(cwd, probe)
    try:
        if error:
            os.rename(os.path.join(probe_cwd, 'result.txt'), os.path.join(probe_cwd, 'error'))
            logger.debug('Error file renamed.')
        if not os.path.isfile(os.path.join(probe_cwd, 'done')):
            count = 0
            total_num = 0
            has_total = False
            with open(os.path.join(probe_cwd, 'result.txt'), 'r') as result:
                result.readline()
                while True:
                    result_line = result.readline()
                    if result_line == '\n':
                        continue
                    if not result_line:
                        if total_num == 0:
                            with open(os.path.join(probe_cwd, 'target.txt'), 'r') as target:
                                while True:
                                    line = target.readline()
                                    if not line:
                                        break
                                    if line != '\n':
                                        total_num += 1 
                        break
                    with open(os.path.join(probe_cwd, 'target.txt'), 'r') as target:
                        while True:
                            target_line = target.readline()
                            if not target_line:
                                has_total = True
                                break
                            if not has_total and target_line != '\n':
                                total_num += 1
                            if target_line == result_line:
                                count += 1
            with open(os.path.join(probe_cwd, 'done'), 'w') as f:
                f.write(json.dumps({'total':total_num, 'hit':count}))
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