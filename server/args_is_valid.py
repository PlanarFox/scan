from collections import defaultdict
import server.util as util
import requests
import json

def check_probe(probes, task_type):
    tmp_dict = {}
    info_dict = defaultdict(list)
    for probe in probes:
        url = util.api_url(probe, '/tasks/' + task_type)
        r = requests.get(url)
        if r.status_code != 200:
            return [False, probe]
        tmp_dict[probe] = json.loads(r.text)
    for k, v in tmp_dict.items():
        info_dict['probe'].append(k)
        for item in ['cpu', 'bandwidth', 'disk']:
            info_dict[item].append(v.get(item, None))
    for item in ['cpu', 'bandwidth', 'disk']:
        if None in info_dict[item]:
            l = len(info_dict[item])
            info_dict[item] = [1] * l
    return [True, info_dict]

def zmap(args):
    temp = check_probe(args['probe'], 'zmap')
    if not temp[0]:
        return False, 'Probe '+ temp[1] +' aren\'t available.'
    return temp

def zgrab(args):
    temp = check_probe(args['probe'], 'zgrab')
    if not temp[0]:
        return False, 'Probe '+ temp[1] +' aren\'t available.'
    return temp

def zMnG(args):
    temp = check_probe(args['probe'], 'zMnG')
    if not temp[0]:
        return False, 'Probe '+ temp[1] +' aren\'t available.'
    return temp

def lzr(args):
    temp = check_probe(args['probe'], 'lzr')
    if not temp[0]:
        return False, 'Probe '+ temp[1] +' aren\'t available.'
    return temp
    