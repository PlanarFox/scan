import json
import requests
import argparse
import util
import yaml

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

task_url = util.api_url(server, '/tasks', port)
if config['type'] == 'zmap':
    with open(config['args']['target'], 'rb') as f:
        r = requests.post(url = task_url, data={'data':json.dumps({'config':config})}, files={'file':f})
else:
    r = requests.post(url = task_url, data={'data':json.dumps({'config':config})})
status = r.status_code
print(r.text)
task_url = r.text[1:-2]

if status != 200:
    raise ValueError('Task post failed:\n' + task_url)
    