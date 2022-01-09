from flask import Flask
import logging.config
import yaml
import os

path = 'server_logger.yaml'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        log_config = yaml.load(f, Loader=yaml.FullLoader)
        logging.config.dictConfig(log_config)
else:
    raise FileNotFoundError('Logger config file not found at working diretory.')

app = Flask(__name__)

from task import *
from submit import *


if __name__ == '__main__':
    app.run(debug=True, port=80, host='0.0.0.0')