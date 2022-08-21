from gtasker.scheduler import TaskScheduler
import os, threading, time

def test_init():
    scheduler = TaskScheduler()
    print(scheduler.get_status())


def test_add_task():
    scheduler = TaskScheduler()
    scheduler.add_task(cmd="echo hello", req_memory=0, path=os.getcwd(), req_gpu_index="", pre_reqt="")
    scheduler.add_task(cmd="echo world", req_memory=0, path=os.getcwd(), req_gpu_index="", pre_reqt="")
    print(scheduler.get_status())


def test_add_task_with_pre_reqt():
    scheduler = TaskScheduler()
    scheduler.add_task(cmd="echo hello", req_memory=0, path=os.getcwd(), req_gpu_index="", pre_reqt="")
    scheduler.add_task(cmd="echo world", req_memory=0, path=os.getcwd(), req_gpu_index="", pre_reqt="1")
    print(scheduler.get_status())

def test_run_task():
    scheduler = TaskScheduler()
    scheduler.add_task(cmd="echo hello", req_memory=0, path=os.getcwd(), req_gpu_index="", pre_reqt="")
    print(scheduler.get_status())
    scheduler._run_task(1)
    print(scheduler.get_status())
    time.sleep(2)
    print(scheduler.get_status())

    

def test_run_task_with_reqt_gpu_index():
    scheduler = TaskScheduler()
    scheduler.add_task(cmd="echo hello", req_memory=1000, path=os.getcwd(), req_gpu_index="0", pre_reqt="")
    scheduler.add_task(cmd="echo world", req_memory=1000, path=os.getcwd(), req_gpu_index="1", pre_reqt="")
    print(scheduler.get_status())
    scheduler._run_task(1)
    scheduler._run_task(2)
    print(scheduler.get_status())
    time.sleep(2)
    print(scheduler.get_status())
    
    
def test_find_task_to_run_gpu():
    scheduler = TaskScheduler()
    scheduler.serve_forever()
    
    scheduler.add_task(cmd="sleep 4s && echo hello", req_memory=10000, path=os.getcwd(), req_gpu_index="", pre_reqt="")
    scheduler.add_task(cmd="echo world", req_memory=100, path=os.getcwd(), req_gpu_index="", pre_reqt="1")
    scheduler.add_task(cmd="echo hw", req_memory=18000, path=os.getcwd(), req_gpu_index="", pre_reqt="")

    while not scheduler.ready_to_shutdown():
        time.sleep(1)
    
    scheduler.shutdown()
  
def test_find_task_to_run_cpu():
    scheduler = TaskScheduler()
    scheduler.serve_forever()
    scheduler.add_task(cmd="sleep 4s && echo hello", req_memory=0, path=os.getcwd(), req_gpu_index="", pre_reqt="")
    scheduler.add_task(cmd="echo world", req_memory=0, path=os.getcwd(), req_gpu_index="", pre_reqt="1")
    scheduler.add_task(cmd="echo hw", req_memory=0, path=os.getcwd(), req_gpu_index="", pre_reqt="")
    
    while not scheduler.ready_to_shutdown():
        time.sleep(1)
    
    scheduler.shutdown()


# test_init()
# test_add_task()
# test_add_task_with_pre_reqt()
# test_run_task()
# test_find_task_to_run()
# test_run_task_with_reqt_gpu_index()