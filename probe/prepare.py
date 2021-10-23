import os
import run
import threading
import util
import logging
from io import StringIO

logger = logging.getLogger('probe')
errIO = StringIO()
stream_handler = logging.StreamHandler(errIO)
stream_handler.setLevel(level=logging.ERROR)
stream_handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s"))
logger.addHandler(stream_handler)

def zmap(cwd, uuid, config, myaddr, **args):
    if config is None:
        logger.error('Config for %s not found.', uuid)
        return False, 'Config not found.'
    if myaddr is None:
        logger.error('Probe addr for %s not found.', uuid)
        return False, 'Can\'t get probe addr.'
    try:
        os.rename(os.path.join(cwd, 'data'), os.path.join(cwd, 'target.txt'))
        logger.debug('Rename for task %s done.', uuid)
    except:
        return False, util.error_record('Fail to rename file.', logger, stream_handler, errIO)
    try:
        valid, ip = util.getv6addr()
        if not valid:
            logger.error(ip)
            return False, ip
        logger.debug('Got ipv6 address.')
    except:
        return False, util.error_record('Fail when getting ipv6 address.', logger, stream_handler, errIO)
    try:
        t1 =threading.Thread(target=getattr(run, 'zmap'), 
                                args=(cwd, uuid, config, ip, myaddr))
        t1.start()
    except Exception:
        return False, util.error_record('', logger, stream_handler, errIO)
    return True, None
