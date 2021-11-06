import json
import os
import requests
import util
import logging

logger = logging.getLogger('server')

def zmap(cwd, config, task_id):
    try:
        args = config['args']
        with open(os.path.join(cwd, 'target'), 'r') as f:
            num = 0
            for line in f:
                num += 1
        num = num // len(args['probe'])
    except KeyError:
        logger.error('Wrong task config.', exc_info=True)
        return False, 'Wrong task config in key field:args, probe'
    with open(os.path.join(cwd, 'target'), 'r') as f:
        for i in range(len(args['probe'])):
            probe = args['probe'][i]

            try:
                if os.path.isdir(os.path.join(cwd, probe)):
                    os.rmdir(os.path.join(cwd, probe))
                os.mkdir(os.path.join(cwd, probe))
            except:
                logger.error('Error when creating probe directory', exc_info=True)
                return False, 'Error when creating probe directory'

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
                            break
                        fp.writelines(line)
            md5 = util.gen_md5(os.path.join(os.path.join(cwd, probe), 'target.txt'))
            try:
                file_dict = {os.path.join(os.path.join(cwd, probe), 'target.txt'):'target.txt'}
                integrated, conf_md5 = util.file_integrater(file_dict, \
                                            json.dumps({'uuid':task_id, 'probe':probe, 'config':config, 'md5':{'target.txt':md5}}))
                with open(integrated, 'rb') as fp:
                    r = requests.post(url, data = fp, params={'md5':conf_md5}, stream=True)
                if r.status_code != 200:
                    logger.error('Task distribution to %s failed:%s', probe, r.text)
                    return False, 'Task distribution failed:' + r.text
                os.remove(integrated)
            except:
                logger.error('Error when posting.', exc_info=True)
                return False, 'Error occured when posting.'

    return True, None

def zgrab(cwd, config, task_id):
    try:
        args = config['args']
        with open(os.path.join(cwd, 'target'), 'r') as f:
            num = 0
            for line in f:
                num += 1
        num = num // len(args['probe'])
    except KeyError:
        logger.error('Wrong task config.', exc_info=True)
        return False, 'Wrong task config in key field:args, probe'

    with open(os.path.join(cwd, 'target'), 'r') as f:
        for i in range(len(args['probe'])):
            probe = args['probe'][i]

            try:
                if os.path.isdir(os.path.join(cwd, probe)):
                    os.rmdir(os.path.join(cwd, probe))
                os.mkdir(os.path.join(cwd, probe))
            except:
                logger.error('Error when creating probe directory', exc_info=True)
                return False, 'Error when creating probe directory'

            url = util.api_url(probe, '/tasks/zgrab')
            with open(os.path.join(os.path.join(cwd, probe), 'target.txt'), 'w') as fp:
                if i+1 != len(args['probe']):
                    for i in range(num):
                        line = f.readline()
                        fp.writelines(line)
                else:
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        fp.writelines(line)
            md5 = {'target.txt':util.gen_md5(os.path.join(os.path.join(cwd, probe), 'target.txt'))}
            try:
                file_dict = {os.path.join(os.path.join(cwd, probe), 'target.txt'):'target.txt'}
                #file = {'target.txt':open(os.path.join(os.path.join(cwd, probe), 'target.txt'), 'rb')}
                if os.path.isfile(os.path.join(cwd, 'mul')):
                    #file['mul'] = open(os.path.join(cwd, 'mul'), 'rb')
                    file_dict[os.path.join(cwd, 'mul')] = 'mul'
                    md5['mul'] = util.gen_md5(os.path.join(cwd, 'mul'))
                integrated, conf_md5 = util.file_integrater(file_dict, \
                                json.dumps({'uuid':task_id, 'probe':probe, 'config':config, 'md5':md5}))
                with open(integrated, 'rb') as fp:
                    r = requests.post(url, data = fp, params={'md5':conf_md5}, stream=True)
                #for _, value in file.items():
                #    value.close()
                if r.status_code != 200:
                    logger.error('Task distribution to %s failed:%s', probe, r.text)
                    return False, 'Task distribution failed:' + r.text
                os.remove(integrated)
            except:
                logger.error('Error when posting.', exc_info=True)
                return False, 'Error occured when posting.'

    return True, None
