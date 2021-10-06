import os
from requests.api import request
import yaml
import argparse
import util

parser = argparse.ArgumentParser(description='submit task to scheduler')
parser.add_argument('--config', type=str, help='config file location')

if parser.config is None:
    raise 'Must provide the config file location!'
    
file = open(parser.config, 'r', encoding='utf-8')
config = file.read()
file.close()
try:
    config = yaml.load(config)
except:
    raise 'Config must be in yaml format.'

server = config['scheduler']['addr']
port = config['scheduler']['port']

if not util.api_has_platform(server + ':' + port):
    raise ValueError('Platform Server Error.')

task_url = util.api_url(server, '/tasks', port)
print('get task url:', task_url)
r = 