import json
import os
import json

def zmap(cwd, uuid, probe, **kw):
    probe_cwd = os.path.join(cwd, probe)
    try:
        if not os.path.isfile(os.path.join(probe_cwd, 'done')):
            count = 0
            total_num = 0
            has_total = False
            with open(os.path.join(probe_cwd, 'tmp_data'), 'r') as result:
                result.readline()
                while True:
                    result_line = result.readline()
                    if not result_line:
                        break
                    with open(os.path.join(probe_cwd, 'target.txt'), 'r') as target:
                        while True:
                            target_line = target.readline()
                            if not target_line:
                                has_total = True
                                break
                            if not has_total:
                                total_num += 1
                            if target_line == result_line:
                                count += 1
            os.rename(os.path.join(probe_cwd, 'tmp_data'), os.path.join(probe_cwd, 'result.txt'))
            with open(os.path.join(probe_cwd, 'done'), 'w') as f:
                f.write(json.dumps({'total':total_num, 'hit':count}))
    except Exception as e:
        return False, str(e)
    return True, None
                