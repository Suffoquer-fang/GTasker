import os
import subprocess
import json
from collections import defaultdict
from typing import List, Callable
import psutil
import sys, time
from appdirs import user_data_dir, site_data_dir

# GTASKER_LOG_PATH = './gtasker_logs/'
GTASKER_LOG_PATH = user_data_dir('gtasker', 'suffoquer')
GTASKER_SERVER_LOG_PATH = os.path.join(GTASKER_LOG_PATH, 'server/')
SERVER_INTERVAL = 2
HOST = "127.0.0.1"
PORT = 6789

def execute_cmd(cmd: str, timeout: int=60) -> bytes or None:
    try:
        output = subprocess.check_output(cmd, timeout=timeout, shell=True)
    except Exception:
        output = None
    finally:
        return output

def get_children_pids(ppid: int, include_self: bool=False) -> List:
    try:
        ret = psutil.Process(ppid).children(recursive=True)
        if include_self:
            ret = [psutil.Process(ppid)] + ret
    except Exception:
        ret = []
    finally:
        return ret

def get_log_file_path(task_id: int) -> str:
    return os.path.join(GTASKER_LOG_PATH, f"{task_id}.log")


def parse_str_to_list(str_: str, map_func: Callable=None) -> List:
    if str_ == '':
        return []
    if map_func is not None:
        return list(map(map_func, str_.split(',')))
    else:
        return list(str_.split(','))


def pack_command(cmd, assigned_gpu):
    if 'conda activate' in cmd:
        env = '. $CONDA_PREFIX/etc/profile.d/conda.sh\n'
    else:
        env = ''
    if assigned_gpu is not None:   
        env += f'export CUDA_VISIBLE_DEVICES={assigned_gpu}\n'
    
    cmd = f'{env}{cmd}'
    return cmd


def follow(tailed_file, s=1, callback=sys.stdout.write, stop_func=None):
    if not os.path.exists(tailed_file):
        print(f"{tailed_file} not exists")
        return
    with open(tailed_file) as file_:
        # print last 5 lines
        last_lines = file_.readlines()[-5:]
        print(''.join(last_lines), end='')
        # Go to the end of file
        file_.seek(0,2)
        try:    
            while (stop_func is None or not stop_func()):
                curr_position = file_.tell()
                line = file_.readline()
                if not line:
                    file_.seek(curr_position)
                    time.sleep(s)
                else:
                    callback(line)
        except KeyboardInterrupt:
            print('\nKeyboardInterrupt')


def read_last_lines(file_path: str, num_lines: int) -> str:
    with open(file_path) as f:
        lines = f.readlines()
        return ''.join(lines[-num_lines:])