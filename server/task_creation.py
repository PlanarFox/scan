import json
import os
import requests
import util

def zmap(cwd, config, task_id):
    args = config['args']
    with open(os.path.join(cwd, 'data'), 'r') as f:
        num = 0
        for line in f:
            num += 1
    num = num // len(args['probe'])
    with open(os.path.join(cwd, 'data'), 'r') as f:
        for i in range(len(args['probe'])):
            probe = args['probe'][i]

            if os.path.isdir(os.path.join(cwd, probe)):
                os.rmdir(os.path.join(cwd, probe))
            os.mkdir(os.path.join(cwd, probe))

            url = util.api_url(probe, '/tasks/zmap')
            with open(os.path.join(os.path.join(cwd, probe), 'target.txt'), 'w') as fp:
                if i+1 != len(args['probe']):
                    for i in range(num):
                        line = f.readline()
                        fp.writelines(line)
                else:
                    while True:
                        line = f.readline()
                        if not line:
                            fp.writelines('\n')
                            break
                        fp.writelines(line)
            md5 = util.gen_md5(os.path.join(os.path.join(cwd, probe), 'target.txt'))
            with open(os.path.join(os.path.join(cwd, probe), 'target.txt'), 'rb') as fp:
                r = requests.post(url, files = {'file':fp}, 
                                    data={'data':json.dumps({'uuid':task_id, 'probe':probe, 'config':config, 'md5':md5})})
            if r.status_code != 200:
                return False, 'Task distribution failed:' + r.text

    return True, None