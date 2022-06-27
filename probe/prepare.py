import run
import threading
import util
import logging
from io import StringIO
import json
import os

logger = logging.getLogger('probe')
errIO = StringIO()
stream_handler = logging.StreamHandler(errIO)
stream_handler.setLevel(level=logging.ERROR)
stream_handler.setFormatter(logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)d - %(message)s"))
logger.addHandler(stream_handler)

def zmap(cwd, uuid, config, myaddr, target_files_loc, module=None):
    if config is None:
        logger.error('Config for %s not found.', uuid)
        return False, 'Config not found.'
    if myaddr is None:
        logger.error('Probe addr for %s not found.', uuid)
        return False, 'Can\'t get probe addr.'
    try:
        if config['args'].get('ipv6', None) == 'disable':
            ipv6 = False
            netinfo_filename = os.path.join(os.getcwd(), 'v4_netinfo.json')
            if config['args'].get('refresh_netinfo', None) or not os.path.isfile(netinfo_filename):
                valid, net_info = util.getv4info(myaddr.split(':')[0], logger)
                with open(netinfo_filename, 'w') as f:
                    json.dump(net_info, f)
            else:
                valid = True
                with open(netinfo_filename, 'r') as f:
                    net_info = json.load(f)
        else:
            ipv6 = True
            netinfo_filename=os.path.join(os.getcwd(), 'v6_netinfo.json')
            if config['args'].get('refresh_netinfo', None) or not os.path.isfile(netinfo_filename):
                valid, net_info = util.getv6addr(logger)
                with open(netinfo_filename, 'w') as f:
                    json.dump(net_info, f)
            else:
                valid = True
                with open(netinfo_filename, 'r') as f:
                    net_info = json.load(f)
        if not valid:
            logger.error(net_info)
            return False, net_info
        logger.debug('Got interface info.')
        if net_info[0] != myaddr:
            logger.warning('Probe may running behind router using NAT or port forwarding.')
    except:
        return False, util.error_record('Fail when getting interface info.', logger, stream_handler, errIO)
    try:
        if module is None:
            t1 =threading.Thread(target=getattr(run, 'zmap'), 
                                args=(cwd, uuid, config, net_info, myaddr, ipv6, target_files_loc))
        else:
            t1 =threading.Thread(target=getattr(run, module), 
                                args=(cwd, uuid, config, net_info, myaddr, ipv6, target_files_loc))
        t1.start()
    except Exception:
        return False, util.error_record('', logger, stream_handler, errIO)
    return True, None

def zgrab(cwd, uuid, config, myaddr, target_files_loc, **args):
    if config is None:
        logger.error('Config for %s not found.', uuid)
        return False, 'Config not found.'
    if myaddr is None:
        logger.error('Probe addr for %s not found.', uuid)
        return False, 'Can\'t get probe addr.'
    try:
        t1 =threading.Thread(target=getattr(run, 'zgrab'), 
                                args=(cwd, uuid, config, myaddr, target_files_loc))
        t1.start()
    except Exception:
        return False, util.error_record('', logger, stream_handler, errIO)
    return True, None

def zMnG(cwd, uuid, config, myaddr, target_files_loc, **args):
    valid, message = zmap(cwd, uuid, config, myaddr, target_files_loc, 'zMnG')
    return valid, message

def lzr(cwd, uuid, config, myaddr, target_files_loc, **args):
    valid, message = zmap(cwd, uuid, config, myaddr, target_files_loc, 'lzr')
    return valid, message