from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
import os
from .task import Task, TaskStatus
from .utils import get_children_pids
from .tracker import GPUTracker
import threading
import time
import subprocess
import json

import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(thread)s %(funcName)s %(message)s"
)

# class QueueThread (threading.Thread):
#     def __init__(self, tq):
#         threading.Thread.__init__(self)
#         self.tq = tq

#         self.EXECUTE_INERVAL = 5
#         self.time_cnt = self.EXECUTE_INERVAL

#     def try_to_execute(self):
#         for task in self.tq.queue:
#             if task.execute_task(): 
#                 print("execute task:", task)
#                 return
    
#     def check_task_status(self):
#         for task in self.tq.queue:
#             if task.status != "RUNNING": continue 
#             task.update_status()

#     def run(self):
#         while True:
#             self.tq.lock.acquire()
            
#             for task in self.tq.queue:
#                 if task.status != "PENDING": continue
#                 if not self.tq.check_pretask_done(task.after): continue

#                 ok, indexes = task.check_exec_status()
#                 if not ok: continue

#                 print("Task ready. Try to execute...", task)
#                 task.status = "RUNNING"
#                 t = threading.Thread(target=run_task, args=(task, indexes, self.tq))
#                 t.start()
#                 time.sleep(5)

#             self.tq.lock.release()
#             time.sleep(5)


class TaskScheduler:
    def __init__(self):
        self.mutex = threading.Lock()
        self.cur_id = 0
        self.gpu_tracker = GPUTracker()

        self.tasks = {}

        self.serving = False


    def get_status(self):
        # tasks status string
        ret_str = f"Task Num: {len(self.tasks)}\n"
        for task_id, task in self.tasks.items():
            ret_str += f"{task} {task.status}\n"
        
        return ret_str

    def add_task(self, cmd, req_memory, path, req_gpu_index, pre_reqt):
        logging.info(f"Add task: {cmd}")
        self.mutex.acquire()
        logging.info(f"Add Task {self.cur_id}")
        self.cur_id += 1
        
        if pre_reqt != "":
            pre_reqt = pre_reqt.split(',')
            pre_reqt = [int(x) for x in pre_reqt]
        else:
            pre_reqt = []

        if req_gpu_index != "":
            req_gpu_index = req_gpu_index.split(',')
            req_gpu_index = [int(x) for x in req_gpu_index]
        else:
            req_gpu_index = []


        
        task = Task(
            id=self.cur_id,
            cmd=cmd,
            req_memory=req_memory,
            path=path,
            req_gpu_index=req_gpu_index,
            pre_reqt=pre_reqt,
            priority=0
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
                pid = self.tasks[task_id].pid
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


    def restart_task(self, task_id):
        self.mutex.acquire()
        if task_id in self.tasks:
            # clone task
            self.add_task(
                cmd=self.tasks[task_id].cmd,
                req_memory=self.tasks[task_id].req_memory,
                path=self.tasks[task_id].path,
                req_gpu_index=self.tasks[task_id].req_gpu_index,
                pre_reqt=self.tasks[task_id].pre_reqt
            )
            ret_msg = f"Task {task_id} Restarted As New Task ({self.cur_id})"
        else:
            ret_msg = f"Task {task_id} Not Found"
        
        self.mutex.release()
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

            time.sleep(1)

            


    def serve_forever(self):
        self.serving = True
        t = threading.Thread(target=self._serve)
        t.start()

    def shutdown(self):
        self.serving = False

    def _undone_task_count(self):
        return sum([1 for task_id, task in self.tasks.items() if task.status not in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.KILLED]])

    def ready_to_shutdown(self):
        return self._undone_task_count() == 0
    # def kill_task(self, id):
    #     self.lock.acquire()
    #     task = self.find_task_with_id(self.running_tasks, id)
    #     if task:
    #         if task.status == TaskStatus.STATUS_RUNNING:
                
    #             proc_list = get_children_pids(task.pid_list[0], include_self=True)
    #             for p in proc_list:
    #                 p.kill()
    #             task.status = TaskStatus.STATUS_KILLED
    #             task.end_time = time.time()

    #             self.idle_tasks[id] = task 
    #             del self.running_tasks[id]

    #             ret_msg = f"[SUCCESS] Kill Task {id}"
    #         else:
    #             ret_msg = "[ERROR] Can Only Kill 'RUNNING' Task"
    #     else:
    #         ret_msg = f"[ERROR] Task {id} Not Exists"
    #     self.lock.release()
    #     return ret_msg

    # def restart_task(self, id):
    #     self.lock.acquire()
        
    #     task = self.find_task_with_id(self.idle_tasks, id)
    #     if task:
    #         if task.status in [TaskStatus.STATUS_DONE, TaskStatus.STATUS_FAIL, TaskStatus.STATUS_KILLED]:
    #             task.status = TaskStatus.PENDING
    #             ret_msg = f"[SUCCESS] Restart Task {id}"

    #             self.pending_tasks[id] = task 
    #             del self.idle_tasks[id]

    #         else:
    #             ret_msg = "[ERROR] Can Only Restart IDLE Task"
    #     else:
    #         ret_msg = f"[ERROR] Task {id} Not Exists"
    #     self.lock.release()
    #     return ret_msg
    
    
class TaskQueue:
    def __init__(self, user):
        self.user = user
        self.queue = []
        self.lock = threading.Lock()
        self.cur_id = 0
        

    
    def get_status(self):
        ret_str = f"User: {self.user} --- Task Num: {len(self.queue)}\n"
        # task_str = [str(task) for task in self.queue]
        task_str = [task.detail_str() for task in self.queue]
        return ret_str + '\n'.join(task_str)

    def check_pretask_done(self, after):
        if len(after) <= 0: return True
        for task in self.queue:
            if task.id in after and task.status != "DONE":
                return False
        return True

    def enqueue(self, cmd, min_memory, gpu_index, after):
        self.lock.acquire()
        self.cur_id += 1
        
        if after != "":
            after = after.split(',')
            after = [int(x) for x in after]
        else:
            after = []
        task = Task(self.cur_id, cmd, min_memory, gpu_index, after)
        task.user = self.user
        
        self.queue.append(task)
        task_id = self.cur_id
        self.lock.release()

        print('Enqueue task', task)
        ret_msg = f"[SUCCESS] Append Task {task_id}"
        return ret_msg

    def find_task_with_id(self, id):
        for task in self.queue:
            if task.id == id:
                return task
        return None

    def dequeue(self, id):
        self.lock.acquire()
        task = self.find_task_with_id(id)
        if task:
            if task.status != "RUNNING":
                self.queue.remove(task)
                ret_msg = f"[SUCCESS] Remove Task {id}"
            else:
                ret_msg = "[ERROR] Can Not Remove 'RUNNING' Task"
        else:
            ret_msg = f"[ERROR] Task {id} Not Exists"
        self.lock.release()
        return ret_msg

    def commit_task(self, id):
        self.lock.acquire()
        if id == -1:
            for task in self.queue:
                if task.status == "READY":
                    task.status = "PENDING"
            ret_msg = "[SUCCESS] Commit All Task"
        else:
            task = self.find_task_with_id(id)
            if task:
                if task.status == "READY":
                    task.status = "PENDING"
                    ret_msg = f"[SUCCESS] Commit Task {id}"
                else:
                    ret_msg = "[ERROR] Can Only Commit 'READY' Task"
            else:
                ret_msg = f"[ERROR] Task {id} Not Exists"
        self.lock.release()
        return ret_msg

    def restart_task(self, id):
        self.lock.acquire()
        if id == -1:
            for task in self.queue:
                if task.status == "FAIL":
                    task.status = "PENDING"
            ret_msg = "[SUCCESS] Restart All Failed Task"
        else:
            task = self.find_task_with_id(id)
            if task:
                if task.status == "FAIL" or task.status == "DONE":
                    task.status = "PENDING"
                    ret_msg = f"[SUCCESS] Restart Task {id}"
                else:
                    ret_msg = "[ERROR] Can Only Restart 'FAIL' or 'DONE' Task"
            else:
                ret_msg = f"[ERROR] Task {id} Not Exists"
        self.lock.release()
        return ret_msg

    def kill_task(self, id):
        self.lock.acquire()
        task = self.find_task_with_id(id)
        if task:
            if task.status == "RUNNING":
                subprocess.check_output(f"kill_tree {task.pid+1})", shell=True, timeout=20)
                ret_msg = f"[SUCCESS] Kill Task {id}"
            else:
                ret_msg = "[ERROR] Can Only Kill 'RUNNING' Task"
        else:
            ret_msg = f"[ERROR] Task {id} Not Exists"
        self.lock.release()
        return ret_msg

    # def modify_task(self, id, cmd, mem, gpu_index):
    #     self.lock.acquire()
    #     task = self.find_task_with_id(id)
    #     if task:
    #         if task.status == "RUNNING":
    #             subprocess.check_output(f"kill_tree {task.pid+1})", shell=True, timeout=20)
    #             ret_msg = f"[SUCCESS] Kill Task {id}"
    #         else:
    #             ret_msg = "[ERROR] Can Only Kill 'RUNNING' Task"
    #     else:
    #         ret_msg = f"[ERROR] Task {id} Not Exists"

    #     task = Task(self.cur_id, cmd, min_memory, gpu_index)
    #     task.user = self.user
        
    #     self.queue.append(task)
    #     task_id = self.cur_id
    #     self.lock.release()


if __name__ == "__main__":
    
    print('done')