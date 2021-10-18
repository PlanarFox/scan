import subprocess
import requests
import time
import util
import sys

def probe_daemon(port):
    time.sleep(20.0)
    while True:
        r = requests.get(util.api_url('localhost', port=port))
        if r.status_code != 200:
            try:
                subprocess.run('/usr/local/bin/uwsgi --stop /var/lib/scan/server/uwsgi.pid', shell=True, check=True)
                subprocess.run('/usr/sbin/nginx -s stop', shell=True, check=True)
                subprocess.run('/usr/local/bin/uwsgi /var/lib/scan/server/uwsgi.ini', shell=True, check=True)
                subprocess.run('cp -f /var/lib/scan/server/nginx-flask.conf /etc/nginx/conf.d/server.conf', shell=True, check=True)
                subprocess.run('/usr/sbin/nginx', shell=True, check=True)
            except:
                pass
        time.sleep(10.0)

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        raise AttributeError('No port assigned.')
    else:
        probe_daemon(sys.argv[1])