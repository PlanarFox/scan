import subprocess
import requests
import time
import util
import sys

def restart():
    try:
        subprocess.run('/usr/local/bin/uwsgi --stop /var/lib/scan/probe/uwsgi.pid', shell=True, check=False)
        subprocess.run('/usr/sbin/nginx -s stop', shell=True, check=False)
    except:
        pass
    subprocess.run('/usr/local/bin/uwsgi /var/lib/scan/probe/uwsgi.ini', shell=True, check=True)
    subprocess.run('cp -f /var/lib/scan/probe/nginx-flask.conf /etc/nginx/conf.d/probe.conf', shell=True, check=True)
    subprocess.run('/usr/sbin/nginx', shell=True, check=True)

def probe_daemon(port):
    time.sleep(17.0)
    while True:
        try:
            r = requests.get(util.api_url('localhost', port=port))
            if r.status_code != 200:
                raise Exception('Server not running. Restarting...')
        except:
            try:
                restart()
            except:
                pass
        time.sleep(17.0)

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        raise AttributeError('No port assigned.')
    else:
        probe_daemon(sys.argv[1])
