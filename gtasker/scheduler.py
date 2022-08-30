from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
import os
from .task import Task, TaskStatus
from .utils import get_children_pids, parse_str_to_list, follow, read_last_lines, SERVER_INTERVAL
from .tracker import GPUTracker
import threading
import time
import subprocess
import json
import sys
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(thread)s %(funcName)s %(message)s"
)

os.environ["PYTHONUNBUFFERED"] = "1"

class TaskScheduler:
    def __init__(self):
        self.mutex = threading.Lock()
        self.cur_id = 0
        self.gpu_tracker = GPUTracker()

        self.tasks = {}

        self.serving = False


    def get_status(self):
        task_status_tuple_list = []
        for task_id, task in self.tasks.items():
            task_status_tuple_list.append(task._get_status_tuple())
        return task_status_tuple_list

    def add_task(self, cmd, req_memory, path, req_gpu_index, pre_reqt, env):
        logging.info(f"Add task: {cmd}")
        self.mutex.acquire()
        logging.info(f"Add Task {self.cur_id}")
        
        
        
        pre_reqt = parse_str_to_list(pre_reqt, int)
        req_gpu_index = parse_str_to_list(req_gpu_index, int)

        path = os.path.abspath(path)
        if not os.path.exists(path):
            ret_msg = f"Path {path} Not Found"
            self.mutex.release()
            return ret_msg

        self.cur_id += 1
        task = Task(
            id=self.cur_id,
            cmd=cmd,
            req_memory=req_memory,
            path=path,
            req_gpu_index=req_gpu_index,
            pre_reqt=pre_reqt,
            priority=0,
            env=env
        )
        self.tasks[self.cur_id] = task

        self.mutex.release()

        ret_msg = f"New Task Added ({self.cur_id})"
        return ret_msg

    def remove_task(self, task_id):
        self.mutex.acquire()
        if task_id in self.tasks:
            if self.tasks[task_id].status == TaskStatus.RUNNING:
                ret_msg = f"Task {task_id} is running. Please kill it first."
            else:
                del self.tasks[task_id]
                ret_msg = f"Task {task_id} Removed"
        else:
            ret_msg = f"Task {task_id} Not Found"
        
        self.mutex.release()
        return ret_msg
    
    def stash_task(self, task_id):
        self.mutex.acquire()
        if task_id in self.tasks:
            if self.tasks[task_id].status != TaskStatus.PENDING:
                ret_msg = f"Task {task_id} is not pending. Please check."
            else:
                self.tasks[task_id].status = TaskStatus.STASHED
                ret_msg = f"Task {task_id} Stashed"
        else:
            ret_msg = f"Task {task_id} Not Found"
        
        self.mutex.release()
        return ret_msg

    def kill_task(self, task_id):
        self.mutex.acquire()
        if task_id in self.tasks:
            if self.tasks[task_id].status == TaskStatus.RUNNING:
                #kill task
                pid = self.tasks[task_id].executed_proc.pid
                proc_list = get_children_pids(pid, include_self=True)
                for p in proc_list:
                    p.kill()
                ret_msg = f"Task {task_id} Killed"
            else:
                ret_msg = f"Task {task_id} Not Running"
        else:
            ret_msg = f"Task {task_id} Not Found"
        
        self.mutex.release()
        return ret_msg


    def restart_task(self, task_id, in_place=False):
        self.mutex.acquire()
        if task_id in self.tasks:
            # clone task
            new_task = Task(
                id=task_id,
                cmd=self.tasks[task_id].cmd,
                req_memory=self.tasks[task_id].req_memory,
                path=self.tasks[task_id].path,
                req_gpu_index=self.tasks[task_id].req_gpu_index,
                pre_reqt=self.tasks[task_id].pre_reqt,
                priority=self.tasks[task_id].priority,
                env=self.tasks[task_id].env
            )
            if in_place:
                self.tasks[task_id] = new_task
                ret_msg = f"Task {task_id} Restarted In Place"
            else:
                self.cur_id += 1
                new_task.id = self.cur_id
                self.tasks[self.cur_id] = new_task

                # modify pre-requisit tasks
                for id, task in self.tasks.items():
                    task.modify_pre_reqt(task_id, self.cur_id)
                
                ret_msg = f"Task {task_id} Restarted As New Task ({self.cur_id})"
        else:
            ret_msg = f"Task {task_id} Not Found"
        
        self.mutex.release()
        return ret_msg

    def clean_task(self):
        # remove all success tasks, modify the pre-requisit tasks of pending tasks
        self.mutex.acquire()
        success_task_ids = [id for id, task in self.tasks.items() if task.status == TaskStatus.SUCCESS]
        for id in success_task_ids:
            del self.tasks[id]
        
        for id, task in self.tasks.items():
            if task.status == TaskStatus.PENDING:
                for pre_id in task.pre_reqt:
                    if pre_id in success_task_ids:
                        task.modify_pre_reqt(pre_id, -1)

        self.mutex.release()

        ret_msg = f"{len(success_task_ids)} Success Tasks Removed"
        return ret_msg

    def task_is_running(self, task_id):
        return task_id in self.tasks and self.tasks[task_id].status == TaskStatus.RUNNING

    def task_exists(self, task_id):
        return task_id in self.tasks

    def follow_task(self, task_id, callback=sys.stdout.write):
        logging.info(f"Follow task: {task_id}")
        if task_id in self.tasks:
            if self.tasks[task_id].status == TaskStatus.RUNNING:
                task_log_file = self.tasks[task_id].log_file
                stop_func = lambda: (task_id not in self.tasks or self.tasks[task_id].status != TaskStatus.RUNNING)
                follow(task_log_file, stop_func=stop_func, callback=callback)
                ret_msg = f"Task {task_id} Follow Done"
            else:
                ret_msg = f"Task {task_id} Not Running"
        else:
            ret_msg = f"Task {task_id} Not Found"
        
        return ret_msg
    
    

    def log_task(self, task_id, lines=10):
        logging.info(f"Log task: {task_id}")
        if task_id in self.tasks:
            task_log_file = self.tasks[task_id].log_file
            if task_log_file is not None:
                ret_msg = read_last_lines(task_log_file, lines)
            else:
                ret_msg = f"Task {task_id} Log File Not Found"
        else:
            ret_msg = f"Task {task_id} Not Found"
        
        return ret_msg


    def _run_task(self, task_id, assigned_gpu=None):
        if task_id not in self.tasks: return
        task = self.tasks[task_id]
        t = threading.Thread(target=task.spawn, args=(self.mutex, assigned_gpu, self.gpu_tracker))
        t.start()

    def _check_pre_reqt(self, task_id):
        task = self.tasks[task_id]
        for pre_task_id in task.pre_reqt:
            if self.tasks[pre_task_id].status != TaskStatus.SUCCESS:
                return False
        return True


    def _find_task_to_run(self):
        self.gpu_tracker.update()
        for task_id, task in self.tasks.items():
            if not task.check_exec_status(): continue
            if not self._check_pre_reqt(task_id): continue
            
            # check if task is ready to run
            if task.req_memory > 0:
                ok, indexes = task.check_exec_mem(self.gpu_tracker.free_memory)
                if not ok: continue
                assigned_gpu = indexes[0]

            else:
                assigned_gpu = None

            return task_id, assigned_gpu
        return None, None


    def _serve(self):
        while self.serving:
            self.mutex.acquire()
            task_id, assigned_gpu = self._find_task_to_run()
            self.mutex.release()

            if task_id is not None:
                logging.info(f"Task {task_id} Found. Assigned GPU: {assigned_gpu}")
                self._run_task(task_id, assigned_gpu)

            time.sleep(SERVER_INTERVAL)

            
    def _kill_all_tasks(self):
        for task_id, task in self.tasks.items():
            self.kill_task(task_id)

    def serve_forever(self):
        self.serving = True
        t = threading.Thread(target=self._serve)
        t.daemon = True
        t.start()
        ret_msg = "Server Started"
        return ret_msg

    def shutdown(self):
        self.serving = False
        self._kill_all_tasks()
        time.sleep(1)
        ret_msg = "Server Shutdown\nGoodbye!\n"
        return ret_msg

    def _undone_task_count(self):
        return sum([1 for task_id, task in self.tasks.items() if task.status not in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.KILLED]])

    def ready_to_shutdown(self):
        return self._undone_task_count() == 0
    
if __name__ == "__main__":
    
    print('done')