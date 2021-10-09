import json
import os
import json

def zmap(cwd, uuid, probe, data, **kw):
    probe_cwd = os.path.join(cwd, probe)
    try:
        if not os.path.isfile(os.path.join(probe_cwd, 'done')):
            with open(os.path.join(probe_cwd, 'result.txt'), 'w') as f:
                f.write(data.read().decode('utf-8'))
                # Memory error warning

            count = 0
            with open(os.path.join(probe_cwd, 'target.txt'), 'r') as target:
                with open(os.path.join(probe_cwd, 'result.txt'), 'r') as result:
                    target_ip = target.readlines()
                    total_num = len(target_ip)
                    for line in result:
                        if line in target_ip:
                            count += 1 
            
            with open(os.path.join(probe_cwd, 'done'), 'w') as f:
                f.write(json.dumps({'total':total_num, 'hit':count}))
    except Exception as e:
        return False, e.args
    return True, None
                