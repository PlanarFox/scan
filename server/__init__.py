from flask import Flask

app = Flask(__name__)

from task import *
from submit import *

if __name__ == '__main__':
    app.run(debug=True, port=80)