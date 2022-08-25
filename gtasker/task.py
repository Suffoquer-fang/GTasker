import subprocess
import os
import time
import datetime
from enum import Enum 
from .utils import get_log_file_path, pack_command

class TaskStatus(Enum):
    PENDING = 0 # Task is waiting to be executed
    STASHED = 1 # Task is stashed, will not be executed until it is unstashed manually
    RUNNING = 2 # Task is running
    SUCCESS = 3 # Task is done successfully
    FAILED = 4 # Task is done with error
    KILLED = 5 # Task is killed by user
    LOCKED = 6 # Task is being edited 



class Task:
    def __init__(self,
        id: int,                        # task id, start from 1, 0 is reserved.
        cmd: str,                       # command to be executed
        req_memory: int,                # required GPU memory in MB
        path: str,                      # working directory, default is current directory
        req_gpu_index: list = [],       # required GPU index, default is empty, means any GPU is OK
        pre_reqt: list = [],            # prerequisite tasks, default is empty, means no prerequisite
        priority: int = 0,              # priority, default is 0, higher priority task will be executed first
    ) -> None:
        self.id = id
        self.cmd = cmd 
        self.req_memory = req_memory
        self.req_gpu_index = req_gpu_index
        self.pre_reqt = pre_reqt
        self.path = path

        self.priority = priority


        # runtime variables
        self.status = TaskStatus.PENDING

        self.executed_proc = None
        self.assigned_gpu = None
        self.start_time = None
        self.end_time = None
        self.log_file = None


    def check_exec_mem(self, free_memory):
        if len(self.req_gpu_index) == 0:
            available_gpus = [i for i in free_memory if free_memory[i] > self.req_memory] 
        else:
            available_gpus = [i for i in self.req_gpu_index if free_memory[i] > self.req_memory]
        return len(available_gpus) > 0, available_gpus

    def check_exec_status(self):
        return self.status in [TaskStatus.PENDING, TaskStatus.STASHED]

    def modify_pre_reqt(self, old_id, new_id = -1):
        if new_id == -1:
            self.pre_reqt = [i for i in self.pre_reqt if i != old_id]
        else:
            self.pre_reqt = [new_id if i == old_id else i for i in self.pre_reqt]


    def spawn(self, mutex, assigned_gpu=None, gpu_tracker=None):
        # lock
        mutex.acquire()
        self.assigned_gpu = assigned_gpu
        self.status = TaskStatus.RUNNING
        self.start_time = datetime.datetime.now().strftime("%m-%d %H:%M:%S")

        self.log_file = get_log_file_path(self.id)
        
        log_file = open(self.log_file, "w")
        log_file.write(self._meta_str())
        log_file.flush()
        log_file.close()

        # execute
        cmd = pack_command(self.cmd, None)
        print('Executing: {}'.format(cmd))
        
        log_file = open(self.log_file, "ab")

        subprocess_env = os.environ.copy()
        if assigned_gpu is not None:
            subprocess_env["CUDA_VISIBLE_DEVICES"] = f"{assigned_gpu}"
        proc = subprocess.Popen(cmd, shell=True, cwd=self.path, stdout=log_file, stderr=log_file, bufsize=1, start_new_session=True, env = subprocess_env, executable="/bin/bash")

        self.executed_proc = proc

        if assigned_gpu is not None and gpu_tracker is not None:
            gpu_tracker.book_memory(self.assigned_gpu, self.req_memory, proc.pid)

        mutex.release()

        exit_code = self.executed_proc.wait()

        log_file.close()

        mutex.acquire()
        self.end_time = datetime.datetime.now().strftime("%m-%d %H:%M:%S")

        if assigned_gpu is not None and gpu_tracker is not None:
            gpu_tracker.unbook_memory(assigned_gpu, proc.pid)
        
        if exit_code == 0:
            self.status = TaskStatus.SUCCESS
        elif exit_code == -9:
            self.status = TaskStatus.KILLED
        else:
            self.status = TaskStatus.FAILED
        mutex.release()
        
        log_file = open(self.log_file, "a+")
        log_file.write("\n"*3 + self._ending_str())
        log_file.flush()
        log_file.close()

        return self.executed_proc

    def _meta_str(self):
        ret_str = "-" * 50 + "\n"
        ret_str += "Task ID: {}\n".format(self.id)
        ret_str += "Command: {}\n".format(self.cmd)
        if self.req_memory > 0:
            ret_str += "Type: GPU ({} MB)\n".format(self.req_memory)
        else:
            ret_str += "Type: CPU\n"
        if self.start_time is not None:
            ret_str += "Execute Time: {}\n".format(self.start_time)
        if self.assigned_gpu is not None:
            ret_str += "Assigned GPU: {}\n".format(self.assigned_gpu)
        ret_str += "_" * 50 + "\n\n"
        return ret_str

    def _ending_str(self):
        ret_str = "-" * 50 + "\n"
        ret_str += "Task Status: {}\n".format(self.status.name)
        if self.end_time is not None:
            ret_str += "End Time: {}\n".format(self.end_time)
        ret_str += "_" * 50 + "\n\n"
        return ret_str
    
    def __str__(self):
        return "Task {}: {}".format(self.id, self.cmd)

    def detail_str(self):
        return self.__str__()


# predefined tasks for testing
def echo_task():
    return Task(
        id=1,
        cmd="echo 'Hello World'",
        req_memory=0,
        path=os.getcwd(),
        req_gpu_index=[],
        pre_reqt=[],
        priority=0
    )

def sleep_task():
    return Task(
        id=2,
        cmd="sleep 5",
        req_memory=0,
        path=os.getcwd(),
        req_gpu_index=[],
        pre_reqt=[],
        priority=0
    )

def failing_task():
    return Task(
        id=3,
        cmd="echo 'Hello World' && exit 1",
        req_memory=0,
        path=os.getcwd(),
        req_gpu_index=[],
        pre_reqt=[],
        priority=0
    )

def ls_task():
    return Task(
        id=4,
        cmd="ls",
        req_memory=0,
        path="/home/fangyan/Workspace/ColBERT/",
        req_gpu_index=[],
        pre_reqt=[],
        priority=0
    )


