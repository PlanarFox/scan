import os
import json

def zmap(cwd):
    total = 0
    count = 0
    try:
        for item in os.listdir(cwd):
            path = os.path.join(cwd, item)
            if os.path.isdir(path):
                with open(os.path.join(path, 'done'), 'r') as f:
                    statistics = json.loads(f.read())
                    total += statistics['total']
                    count += statistics['hit']
        
        with open(os.path.join(cwd, 'result.txt'), 'w') as f:
            f.writelines(['total:'+str(total), '\nhit:'+str(count), '\n-------------------\n'])
            for item in os.listdir(cwd):
                path = os.path.join(cwd, item)
                if os.path.isdir(path):
                    with open(os.path.join(path, 'result.txt'), 'r') as fp:
                        fp.readline()
                        while True:
                            line = fp.readline()
                            if not line:
                                break
                            f.writelines(line)
                        
    except Exception as e:
        return False, str(e)
    
    return True, None
