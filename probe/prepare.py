import os
import run
import threading
import util



def zmap(cwd, uuid, config, myaddr, **args):
    if config is None:
        return False, 'Invalid config.'
    if myaddr is None:
        return False, 'Can\'t get probe addr.'
    os.rename(os.path.join(cwd, 'data'), os.path.join(cwd, 'target.txt'))
    valid, ip = util.getv6addr()
    if not valid:
        return False, ip
    try:
        t1 =threading.Thread(target=getattr(run, 'zmap'), 
                                args=(cwd, uuid, config, ip, myaddr))
        t1.start()
    except Exception as e:
        return False, e.args
    return True, None
