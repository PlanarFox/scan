from io import StringIO
import json
import os
import requests
import util

def zmap(cwd, config, task_id):
    args = config['args']
    with open(os.path.join(cwd, 'data'), 'r') as f:
        target = f.readlines()
        #this may cause memory error, fix later
        num = len(target) // len(args['probe'])
        for i in range(len(args['probe'])):
            probe = args['probe'][i]

            if os.path.isdir(os.path.join(cwd, probe)):
                os.rmdir(os.path.join(cwd, probe))
            os.mkdir(os.path.join(cwd, probe))

            url = util.api_url(probe, '/tasks/zmap')
            data = StringIO()
            with open(os.path.join(os.path.join(cwd, probe), 'target.txt'), 'w') as fp:
                if i+1 != len(args['probe']):
                    fp.writelines(target[num * i:num * (i+1)])
                    data.writelines(target[num * i:num * (i+1)])
                else:
                    fp.writelines(target[num * i:])
                    data.writelines(target[num * i:])
            r = requests.post(url, files = {'file':data.getvalue().encode('utf-8')}, 
                                data={'data':json.dumps({'uuid':task_id, 'probe':probe, 'config':config})})
            data.close()
            if r.status_code != 200:
                return False, 'Task distribution failed:' + r.text

    return True, None