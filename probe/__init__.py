from flask import Flask

app = Flask(__name__)
#import os
#if not os.path.isfile(os.path.join(os.getcwd(), 'uwsgi.socket')):
#    os.mknod(os.path.join(os.getcwd(), 'uwsgi.socket'))

from task import *

if __name__ == '__main__':
    app.run(debug=True, port=8888)