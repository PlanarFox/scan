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

def zmap(cwd, uuid, config, myaddr, zgrab_enable=False, **args):
    if config is None:
        logger.error('Config for %s not found.', uuid)
        return False, 'Config not found.'
    if myaddr is None:
        logger.error('Probe addr for %s not found.', uuid)
        return False, 'Can\'t get probe addr.'
    try:
        if config['args'].get('ipv6', None) == 'disable':
            ipv6 = False
            valid, net_info = util.getv4info(myaddr.split(':')[0], logger)
        else:
            ipv6 = True
            valid, net_info = util.getv6addr(logger)
            if not valid:
                logger.error(net_info)
                return False, net_info
            logger.debug('Got interface info.')
        if net_info[0] != myaddr:
            logger.warning('Probe may running behind router using NAT or port forwarding.')
    except:
        return False, util.error_record('Fail when getting interface info.', logger, stream_handler, errIO)
    try:
        if not zgrab_enable:
            t1 =threading.Thread(target=getattr(run, 'zmap'), 
                                args=(cwd, uuid, config, net_info, myaddr, ipv6))
        else:
            t1 =threading.Thread(target=getattr(run, 'zMnG'), 
                                args=(cwd, uuid, config, net_info, myaddr, ipv6))
        t1.start()
    except Exception:
        return False, util.error_record('', logger, stream_handler, errIO)
    return True, None

def zgrab(cwd, uuid, config, myaddr, **args):
    if config is None:
        logger.error('Config for %s not found.', uuid)
        return False, 'Config not found.'
    if myaddr is None:
        logger.error('Probe addr for %s not found.', uuid)
        return False, 'Can\'t get probe addr.'
    try:
        t1 =threading.Thread(target=getattr(run, 'zgrab'), 
                                args=(cwd, uuid, config, myaddr))
        t1.start()
    except Exception:
        return False, util.error_record('', logger, stream_handler, errIO)
    return True, None

def zMnG(cwd, uuid, config, myaddr, **args):
    valid, message = zmap(cwd, uuid, config, myaddr, True)
    return valid, message