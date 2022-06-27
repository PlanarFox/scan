import json
import os
import requests
import util
import logging
from pathlib import Path
import shutil
from typing import Dict, List
import numpy as np
from gekko import GEKKO
from collections import defaultdict

logger = logging.getLogger('server')

SHARD_OUT_DIR = 'target_shards'

class AssignMethod:
    """ 探测任务分配方法
    """
    BAND = 'bandwidth'  # 按带宽分配
    AVG  = 'avg'        # 均分
    OPT  = 'optimize'   # 基于优化理论的方法
    ALL  = [BAND, AVG, OPT]

def optimization_for_task_assign(probe, task_num, bandwidth_list, 
        cpu_info_list=None, disk_info_list=None) -> List[int]:
    """ 基于优化理论的探测任务分配算法
    Args:
        probe: 探针列表
        task_num: 总任务数
        bandwidth_list: 主机带宽信息
        cpu_info_list: 主机cpu主频信息
        disk_info_list: 主机磁盘读写速度信息
    Returns:
        List[int]: 每个主机所分配的任务数量, 与probe一一对应
    """
    
    cpus = np.array(cpu_info_list)
    disks = np.array(disk_info_list)

    cpus = cpus / np.amin(cpus)
    cpus = np.ones_like(cpus) + (cpus - 1) * 0.5

    disks = disks / np.amin(disks)
    disks = np.ones_like(disks) + (disks - 1) * 0.35

    # 利用GEKKO进行求解
    n = len(probe)
    m = GEKKO(remote=False)
    *x, Z = m.Array(m.Var, n + 1, integer=True)
    m.Minimize(Z)
    m.Equation(sum(x) == task_num)
    m.Equations([Z >= x[i] / (cpus[i] * disks[i] * bandwidth_list[i]) for i in range(n)])
    m.options.solver = 1
    m.solve(disp=False)
    return [int(k.value[0]) for k in x]


def task_assign(task_list_len, probe_list, rand_seed=None,
                method=AssignMethod.BAND, bandwidth_list=None,
                cpu_dict=None, disk_dict=None) -> Dict:
    """ 根据探测任务分配算法, 将task_list分配给host_names
    Args:
        task_list     : 探测任务列表
        host_names    : 主机名列表
        rand_seed     : 随机种子
        method        : 探测任务分配算法
        bandwidth_list: 主机带宽信息
    Returns:
        Dict: 任务分配结果 
        {probe:[task num 1, task num 2, ...]...}
    """
    rnd = np.random.RandomState(rand_seed)
    indexs = rnd.permutation(range(task_list_len))
    assignment = defaultdict(list)

    if method in [AssignMethod.BAND, AssignMethod.OPT]:
        #每个探针分配到的列表中的任务数量，与probe列表的顺序严格对应
        task_num_list = optimization_for_task_assign(probe_list, task_list_len,
                                                    bandwidth_list, cpu_dict, disk_dict)
        cur_idx = 0
        for i, num in enumerate(task_num_list):
            probe = probe_list[i]
            logger.debug(f'tasks num for {probe}:{num}')
            for idx in indexs[cur_idx:cur_idx + num]:
                assignment[probe].append(int(idx))
            cur_idx += num
    elif method == AssignMethod.AVG:
        for i in indexs:
            i = int(i)
            probe = probe_list[i % len(probe_list)]
            assignment[probe].append(i)
        for k, v in assignment.items():
            logger.debug(f'tasks num for {k}:{len(v)}')
    return assignment
            

def target_file_split(cwd, origin, shards_num) -> Path:
    out_dir = Path(cwd) / SHARD_OUT_DIR
    # if splited directory exists, it won't split again
    if not out_dir.exists():
        Path.mkdir(out_dir)
        shards_list = []
        for i in range(shards_num):
            shards_list.append(open(out_dir / f'{i}.txt', 'w'))
        
        n = 0
        with open(origin, 'r') as f:
            while line := f.readline():
                shards_list[n].write(line)
                n += 1
                n %= shards_num
        for fp in shards_list:
            fp.close()
    return out_dir

def get_num_args(cwd, config):
    try:
        args = config['args']
        with open(os.path.join(cwd, 'target'), 'r') as f:
            num = 0
            for line in f:
                num += 1
        num = num // len(args['probe'])
    except KeyError:
        logger.error('Wrong task config.', exc_info=True)
        return None, 'Wrong task config in key field:args, probe'
    return args, num

def target_split(cwd, probe, probe_index, num, total_probe, f, filename):
    path = Path(cwd) / probe
    try:
        if path.exists:
            raise Exception('Task directory already exists. UUID may be duplicated.')
        os.mkdir(path)
        #if os.path.isdir(os.path.join(cwd, probe)):
        #    os.rmdir(os.path.join(cwd, probe))
        #os.mkdir(os.path.join(cwd, probe))
    except:
        logger.error('Error when creating probe directory', exc_info=True)
        return False, 'Error when creating probe directory'
    with open(path / filename, 'w') as fp:
        if probe_index+1 != total_probe:
            for i in range(num):
                line = f.readline()
                fp.writelines(line)
        else:
            while True:
                line = f.readline()
                if not line:
                    break
                fp.writelines(line)


def zmap_like(cwd, config, task_id, info_dict, location='/tasks/zmap'):
    try:
        args = config['args']
    except KeyError:
        logger.error('Wrong task config.', exc_info=True)
        return None, 'Wrong task config in key field:args'

    if args.get('target', None):

        origin_target = Path(cwd) / 'target'
        shards_dir = target_file_split(cwd, origin_target, args.get('shards', 10))
        try:
            assignment = task_assign(len(list(shards_dir.iterdir())), info_dict['probe'], args.get('rand_seed', 0),
                                    args['method'], info_dict['bandwidth'], info_dict['cpu'], info_dict['disk'])
        except KeyError:
            logger.error('Wrong task config.', exc_info=True)
            return None, 'Wrong task config in key field:probe or rand_seed'
        
        shards_list = list(shards_dir.iterdir())
        for probe in info_dict['probe']:
            try:
                probe_path = Path(cwd) / 'probe' / probe
                Path.mkdir(probe_path, parents=True)
                with open(probe_path / 'assignment.txt', 'w') as f:
                    json.dump([str(shards_list[idx]) for idx in assignment[probe]], f)

                url = util.api_url(probe, location)
                #file_dict = {os.path.join(os.path.join(cwd, probe), 'target.txt'):'target.txt'}
                file_dict = {str(shards_list[idx]):str(shards_list[idx].name) for idx in assignment[probe]}
                md5 = {str(shards_list[idx].name):util.gen_md5(str(shards_list[idx])) for idx in assignment[probe]}
                integrated, conf_md5 = util.file_integrater(file_dict, probe_path,\
                                            json.dumps({'uuid':task_id, 'probe':probe, 'config':config, 'md5':md5}))
                with open(integrated, 'rb') as fp:
                    r = requests.post(url, data = fp, params={'md5':conf_md5}, stream=True)
                if r.status_code != 200:
                    logger.error('Task distribution to %s failed:%s', probe, r.text)
                    return False, 'Task distribution failed:' + r.text
                os.remove(integrated)
            except:
                logger.error('Error when posting.', exc_info=True)
                return False, 'Error occured when posting.'

    return True, None

def zgrab_like(cwd, config, task_id, info_dict, location='/tasks/zgrab'):
    args, num = get_num_args(cwd, config)
    if args is None:
        return False, num

    origin_target = Path(cwd) / 'target'

    with open(origin_target, 'r') as f:
        for i in range(len(args['probe'])):
            probe = args['probe'][i]

            target_split(cwd, probe, i, num, len(args['probe']), f, 'target.txt')
            try:
                url = util.api_url(probe, location)

                md5 = {'target.txt':util.gen_md5(os.path.join(os.path.join(cwd, probe), 'target.txt'))}
                file_dict = {os.path.join(os.path.join(cwd, probe), 'target.txt'):'target.txt'}
                if os.path.isfile(os.path.join(cwd, 'mul')):
                    file_dict[os.path.join(cwd, 'mul')] = 'mul'
                    md5['mul'] = util.gen_md5(os.path.join(cwd, 'mul'))
                integrated, conf_md5 = util.file_integrater(file_dict, os.path.join(cwd, probe),\
                                json.dumps({'uuid':task_id, 'probe':probe, 'config':config, 'md5':md5}))
                with open(integrated, 'rb') as fp:
                    r = requests.post(url, data = fp, params={'md5':conf_md5}, stream=True)
                if r.status_code != 200:
                    logger.error('Task distribution to %s failed:%s\nurl:%s', probe, r.text, url)
                    return False, 'Task distribution failed:' + r.text
                os.remove(integrated)
            except:
                logger.error('Error when posting.', exc_info=True)
                return False, 'Error occured when posting.'

    return True, None

def zMnG(cwd, config, task_id, info_dict):
    valid, message = zgrab_like(cwd, config, task_id, info_dict, '/tasks/zMnG')
    return valid, message

def zgrab(cwd, config, task_id, info_dict):
    valid, message = zgrab_like(cwd, config, task_id, info_dict)
    return valid, message

def zmap(cwd, config, task_id, info_dict):
    valid, message = zmap_like(cwd, config, task_id, info_dict)
    return valid, message

def lzr(cwd, config, task_id, info_dict):
    valid, message = zmap_like(cwd, config, task_id, info_dict, '/tasks/lzr')
    return valid, message