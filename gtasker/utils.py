import os
import subprocess
import json
from collections import defaultdict
from pprint import pprint
from typing import List 
import psutil

GTASTER_ROOT = './gtasker_logs/'

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
            ret.append(psutil.Process(ppid))
    except Exception:
        ret = []
    finally:
        return ret

def get_log_file_path(task_id: int) -> str:
    return os.path.join(GTASTER_ROOT, f"{task_id}.log")