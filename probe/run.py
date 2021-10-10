import json
import requests
import subprocess
import util
import os
import time

def zmap(cwd, uuid, config, ip, myaddr, **kw):
    command = '/usr/local/sbin/zmap -M ipv6_tcp_synscan -O csv -f \"saddr\"'
    command += (' -p ' + config.get('port', '80'))
    command += ' --ipv6-source-ip=\"' + ip[0] + '\"'
    command += ' --ipv6-target-file=\"' + os.path.join(cwd, 'target.txt') + '\"'
    command += ' -o \"' + os.path.join(cwd, 'output.csv') + '\"'
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', check=False)

    with open(os.path.join(cwd, 'output.csv'), 'r') as f:
        f.readline()
        result_addr = f.read()
        # May cause memory error when output file is too large
    
    url = util.api_url(config['scheduler']['addr'], '/submit/zmap', config['scheduler']['port'])
    for i in range(5):
        try:
            r = requests.post(url, files = {'file':result_addr.encode('utf-8')},
                                data = {'data':json.dumps({'uuid':uuid, 'addr':myaddr})})
            if r.status_code == 200:
                break
        except:
            time.sleep(1.0)
            continue

    




