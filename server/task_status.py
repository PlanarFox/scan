import os
from pathlib import Path
import sys
sys.path.append(os.path.join(os.getcwd(), '..'))
from task_creation import SUB_TASK_FILE, PARENT_UUID_FILE
import util

def single_task_status(cwd, uuid) -> tuple[bool, str]:
    isdone = True
    haserror = False
    error_probe = None
    probe_path = os.path.join(cwd, 'probe')
    for item in os.listdir(probe_path):
        path = os.path.join(probe_path, item)
        if os.path.isdir(path):
            if os.path.isfile(os.path.join(path, 'error')):
                haserror = True
                error_probe = item
                break
            if not os.path.isfile(os.path.join(path, 'done')):
                isdone = False
                break
    
    if haserror:
        return False, f'Task {uuid} can\'t be done because error occured. Please check the log of probe {error_probe}'
    
    if not isdone:
        return False, f'Task {uuid} hasn\'t done yet.'
    return True, ''

def task_status(cwd, uuid, trace_parent = False) -> tuple[bool, str]:
    if trace_parent:
        cwd, uuid = util.get_parent_task_dir(cwd, uuid)
            
    if (Path(cwd) / SUB_TASK_FILE).exists():
        sub_tasks = list(map(str.strip, open(Path(cwd, SUB_TASK_FILE)).readlines()))
        cwd = Path(cwd).resolve().parent
        for sub_task in sub_tasks:
            isdone, message = single_task_status(cwd / sub_task, sub_task)
            if not isdone:
                break
        return isdone, message
    else:
        return single_task_status(cwd, uuid)
        