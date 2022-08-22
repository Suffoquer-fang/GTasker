import os, time
from gtasker.scheduler import TaskScheduler

if __name__ == "__main__":
    scheduler = TaskScheduler()
    scheduler.serve_forever()

    scheduler.add_task(cmd="sleep 10s && echo hello", req_memory=10000, path=os.getcwd(), req_gpu_index="", pre_reqt="")
    scheduler.add_task(cmd="echo world", req_memory=100, path=os.getcwd(), req_gpu_index="", pre_reqt="1")
    scheduler.add_task(cmd="echo hw", req_memory=18000, path=os.getcwd(), req_gpu_index="", pre_reqt="")

    tick = 0
    while not scheduler.ready_to_shutdown():
        time.sleep(1)
        tick += 1
        print(tick, scheduler.get_status())

        if tick == 5:
            print(scheduler.kill_task(1))
            print(scheduler.kill_task(3))
        
        if tick == 10:
            print(scheduler.restart_task(1))

        if tick == 15:
            print(scheduler.remove_task(2))
            print(scheduler.remove_task(3))
    
    scheduler.shutdown()