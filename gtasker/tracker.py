from .utils import execute_cmd, get_children_pids
from collections import defaultdict
import psutil
import os
import subprocess
import json
import logging

logger = logging.getLogger(__name__)

class GPUTracker:
    # this class is used to track the GPU usage
    # there are three types of GPU usage:
    # 1. busy: the GPU is currently used by a process
    # 2. booked: the GPU will be used by a process in the future, booked by the parent process
    # 3. free: the GPU is not used by any process

    def __init__(self):
        self.GPUSTAT_TIMEOUT = 20
        self.busy_memory = defaultdict(int)
        self.booked_memory = defaultdict(dict)
        self.free_memory = defaultdict(int)

        self.gpu_info = {'gpus': []} 


    def _get_gpu_info(self):
        cmd = "gpustat --json"
        gpu_info = execute_cmd(cmd, self.GPUSTAT_TIMEOUT)
        if not gpu_info: return None
        gpu_info = gpu_info.decode('utf-8', 'strict')
        gpu_info = json.loads(gpu_info)
        
        return gpu_info

    def book_memory(self, gpu_index, gpu_mem, pid):
        self.booked_memory[gpu_index][pid] = gpu_mem

    def _flush_booked_memory(self):
        # make a set of processes in the busy memory
        busy_pids = set()
        for index, gpu in enumerate(self.gpu_info["gpus"]):
            for proc in gpu["processes"]:
                busy_pids.add(proc["pid"])

        # for each booked process, check if any of its children is in the busy memory
        # if so, remove the process from the booked memory
        pids_to_remove = set()
        for index in self.booked_memory:
            for pid in self.booked_memory[index]:
                child_pids = [c.pid for c in get_children_pids(pid)] + [pid]
                for child_pid in child_pids:
                    if child_pid in busy_pids:
                        pids_to_remove.add((index, pid))
        
        for index, pid in pids_to_remove:
            del self.booked_memory[index][pid]
        
        

    def unbook_memory(self, gpu_index, pid):
        if pid in self.booked_memory[gpu_index]:
            del self.booked_memory[gpu_index][pid]


    def update(self):
        # update the GPU usage
        gpu_info = self._get_gpu_info()
        if not gpu_info:
            logger.warning("#> ERROR: GPUSTAT Failed...")
            gpu_info = self.gpu_info
        self.gpu_info = gpu_info

        # update the busy memory
        for index, gpu in enumerate(gpu_info["gpus"]):
            self.free_memory[index] = gpu['memory.total'] - gpu['memory.used']

        # flush the booked memory
        self._flush_booked_memory()

        # update the free memory
        for index in self.free_memory:
            self.free_memory[index] -= sum([self.booked_memory[index][p] for p in self.booked_memory[index]])


    