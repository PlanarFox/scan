import server.util as util
import requests

def check_probe(probes, task_type):
    for probe in probes:
        url = util.api_url(probe, '/tasks/' + task_type)
        r = requests.get(url)
        if r.status_code != 200:
            return [False, probe]
    return [True, None]

def zmap(args):
    temp = check_probe(args['probe'], 'zmap')
    if not temp[0]:
        return False, 'Probe '+ temp[1] +' aren\'t available.'
    return True, None
    