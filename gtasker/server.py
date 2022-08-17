from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
import os
from task import Task
from utils import GPUTracker, TaskStatus
from scheduler import TaskScheduler
import threading
import time
import subprocess
import json
import sys

os.environ["PYTHONUNBUFFERED"] = "1"

def bash_execute_task(task, indexes, scheduler, gpu_tracker):
    index = indexes[0]

    env = f'export CUDA_VISIBLE_DEVICES={index}'
    working_dir_cmd = f'cd {task.working_dir}'
    exec_cmd = 'bash -c "{}\n{}\n{}\n"'.format(env, working_dir_cmd, task.cmd)
    exec_cmd = "{}\n{}\n{}\n".format(env, working_dir_cmd, task.cmd)

    with open(f"./experiment_logs/{task.name}.log", "w") as out:
        out.write(f'EXECUTE TIME: {time.strftime("%m-%d-%H:%M")}\n')
        out.write(f'WORKING DIR: {task.working_dir}\n')
        out.write(f'RUNNING CMD: {task.cmd}\n')
        if task.req_memory > 0:
            out.write(f'RUNNING GPU: {index}\n\n')
        out.write("\n")

    out_err = open(f"./experiment_logs/{task.name}.err", "wb")
    out_file = open(f"./experiment_logs/{task.name}.log", "ab")
    proc = subprocess.Popen(exec_cmd, stdout=out_file, stderr=out_err, bufsize=0, shell=True)

    running_pid = proc.pid
    print('Start Running in pid...', running_pid)
    scheduler.lock.acquire()
    task.start_time = time.time()
    task.pid_list = [running_pid]
    task.assigned_gpu = index


    gpu_tracker.set_busy(index, task.req_memory, running_pid)
    scheduler.lock.release()
    
    
    proc.wait()
    ret_code = proc.returncode

    scheduler.lock.acquire()
    if task.status != TaskStatus.STATUS_KILLED:
        task.status = TaskStatus.STATUS_DONE if ret_code == 0 else TaskStatus.STATUS_FAIL
    task.pid_list = []

    task.end_time = time.time()
    scheduler.task_finish(task.id)
    scheduler.lock.release()


    gpu_tracker.set_free(index, running_pid)

    out_file.close()
    out_err.close()

class ScheduleThread (threading.Thread ):
    def __init__(self, scheduler):
        threading.Thread.__init__(self)
        self.scheduler = scheduler
        self.gpu_tracker = GPUTracker()
        self.gpu_tracker.update()
        self.EXECUTE_INERVAL = 5
        self.time_cnt = self.EXECUTE_INERVAL

    def run(self):
        while True:
            self.scheduler.lock.acquire()
            
            for _, task in self.scheduler.pending_tasks.items():
                if not task.check_exec_status(): continue
                # if not self.scheduler.check_pretask_done(task.pre_reqt): continue

                self.gpu_tracker.update()
                print(self.gpu_tracker.available_memory)
                ok, indexes = task.check_exec_mem(self.gpu_tracker.available_memory)
                if not ok: continue

                print("Task ready. Try to execute...", task)
                task.status = TaskStatus.STATUS_RUNNING
                t = threading.Thread(target=bash_execute_task, args=(task, indexes, self.scheduler, self.gpu_tracker))
                t.start()

                self.scheduler.task_start(task.id)
                
                break

            self.scheduler.lock.release()
            time.sleep(5)
    


def start_server():
    server = SimpleJSONRPCServer(("127.0.0.1", 6789))
    queue = TaskQueue("fangyan")
    server.register_function(queue.get_status)
    server.register_function(queue.enqueue)
    server.register_function(queue.dequeue)
    server.register_function(queue.commit_task)
    server.register_function(queue.kill_task)
    server.register_function(queue.restart_task)

    os.makedirs('./experiment_logs', exist_ok=True)

    queue_thread = QueueThread(queue)
    queue_thread.start()

    server.serve_forever()


if __name__ == "__main__":
    os.makedirs('./experiment_logs', exist_ok=True)
    # server = SimpleJSONRPCServer(("127.0.0.1", 6789))
    scheduler = TaskScheduler("fangyan")
    # server.register_function(scheduler.get_status)
    # server.register_function(queue.enqueue)
    # server.register_function(queue.dequeue)

    scheduler.enqueue('sleep 20 && bash tmux_run_cmd.sh 0 4000', 4000, [0], "~/Workspace/scripts/", [])
    scheduler.enqueue('sleep 5 && bash tmux_run_cmd.sh 0 4000', 4000, [0], "~/Workspace/scripts/", [])

    print(scheduler.get_status())

    schedule_thread = ScheduleThread(scheduler)
    schedule_thread.start()

    # server.serve_forever()
    for i in range(6):
        print(scheduler.get_status())
        time.sleep(1)

    scheduler.kill_task(1)

    while True:
        print(scheduler.get_status())
        time.sleep(1)
    print('done')