import server.util as util
import requests

def check_probe(probes, task_type):
    for probe in probes:
        url = util.api_url(probe, '/tasks/' + task_type)
        r = requests.get(url)
        if r.status_code != 200:
            return False
    return True

def zmap(args):
    if not check_probe(args['probe'], 'zmap'):
        return False, 'Some probes aren\'t available.'
    return True, None
    