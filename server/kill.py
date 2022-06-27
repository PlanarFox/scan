from pathlib import Path
import util
import requests
from task_creation import SUB_TASK_FILE
import json

def kill_single_task(cwd, uuid, task_type):
    probes = json.load(open(cwd / 'config.json'))['args']['probe']
    for probe in probes:
        url = util.api_url(probe, f'/kill/{task_type}/{uuid}')
        r = requests.get(url)
        if not r.status_code == 200:
            return r.text
    (Path(cwd) / 'killed').touch()
    return None

def kill_task(cwd, task_type, task_id):
    if (Path(cwd) / SUB_TASK_FILE).is_file():
        sub_task_uuids = open(Path(cwd) / SUB_TASK_FILE, 'r').readlines()
        sub_task_uuids = list(map(str.strip, sub_task_uuids))
        for sub_task_uuid in sub_task_uuids:
            message = kill_single_task(Path(cwd).resolve().parent / sub_task_uuid,
                                        sub_task_uuid, task_type)
            if message is not None:
                return message
        (Path(cwd) / 'killed').touch()
        return None
    else:
        return kill_single_task(cwd, task_id, task_type)