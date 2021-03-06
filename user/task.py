import json
import os
import requests
import argparse
import util
import yaml
import hashlib

parser = argparse.ArgumentParser(description='submit task to scheduler')
parser.add_argument('--config', type=str, help='config file location')
args, _ = parser.parse_known_args()

if args.config is None:
    raise ValueError('Must provide the config file location!')
    
file = open(args.config, 'r', encoding='utf-8')
config = file.read()
file.close()
try:
    config = yaml.load(config, Loader=yaml.FullLoader)
except:
    raise ValueError('Config must be in yaml format.')

server = config['scheduler']['addr']
port = config['scheduler']['port']

if not util.api_has_platform(server + ':' + port):
    raise ValueError('Platform Server Error.')

print('Uploading files. This may take a while...')
task_url = util.api_url(server, '/tasks', port)
file_dict = {}
md5 = {}

if config.get('db', None) is not None:
    if config['db'].get('public_key') is not None:
        file_dict[config['db']['public_key']] = 'public_key.pem'
        file_dict[config['db']['private_key']] = 'private_key.pem'
        md5['private_key.pem'] = util.gen_md5(config['db']['private_key'])
        md5['public_key.pem'] = util.gen_md5(config['db']['public_key'])
        
if config['type'] == 'zmap' or config['type'] == 'lzr':
    if config['args'].get('target', None) is not None:
        md5['target'] = util.gen_md5(config['args']['target'])
        file_dict[config['args']['target']] = 'target'
        integrated, conf_md5 = util.file_integrater(file_dict, json.dumps({'config':config, 'md5':md5}))
    else:
        integrated, conf_md5 = util.file_integrater(None, json.dumps({'config':config}))
elif config['type'] == 'zgrab':
    md5 = {}
    md5['target'] = util.gen_md5(config['args']['target'])
    file_dict[config['args']['target']] = 'target'
    if config['args'].get('multiple', None):
        md5['mul'] = util.gen_md5(config['args']['multiple'])
        file_dict[config['args']['multiple']] = 'mul'
    integrated, conf_md5 = util.file_integrater(file_dict, json.dumps({'config':config, 'md5':md5}))
elif config['type'] == 'zMnG':
    md5 = {}
    md5['target'] = util.gen_md5(config['args']['target'])
    file_dict[config['args']['target']] = 'target'
    if config['args'].get('zgrab', None):
        if config['args']['zgrab'].get('multiple', None):
            md5['mul'] = util.gen_md5(config['args']['zgrab']['multiple'])
            file_dict[config['args']['zgrab']['multiple']] = 'mul'
    integrated, conf_md5 = util.file_integrater(file_dict, json.dumps({'config':config, 'md5':md5}))
with open(integrated, 'rb') as f:
    r = requests.post(url = task_url, data = f, params={'md5':conf_md5}, stream=True)
os.remove(integrated)
        
    
status = r.status_code
print(r.text)
task_url = r.text[1:-2]

if status != 200:
    raise ValueError('Task post failed:\n' + task_url)
    