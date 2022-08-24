import os, time, logging
from gtasker.scheduler import TaskScheduler
from gtasker.utils import follow

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    os.environ["PYTHONUNBUFFERED"] = "1"
    scheduler = TaskScheduler()
    scheduler.serve_forever()

    # scheduler.add_task(cmd="sleep 10s && echo hello", req_memory=10000, path=os.getcwd(), req_gpu_index="", pre_reqt="")
    # scheduler.add_task(cmd="echo world", req_memory=100, path=os.getcwd(), req_gpu_index="", pre_reqt="1")
    # scheduler.add_task(cmd="echo hw", req_memory=18000, path=os.getcwd(), req_gpu_index="", pre_reqt="")
    # scheduler.add_task(cmd="conda activate torchenv && python real_gpu_test.py", req_memory=3000, path=os.getcwd(), req_gpu_index="4", pre_reqt="")
    scheduler.add_task(cmd="conda activate torchenv && sh run_real_gpu_test.sh", req_memory=2500, path=os.getcwd(), req_gpu_index="1", pre_reqt="")
    scheduler.add_task(cmd="sleep 10s && echo hello", req_memory=3000, path=os.getcwd(), req_gpu_index="1", pre_reqt="")
    scheduler.add_task(cmd="sleep 10s && echo world", req_memory=0, path=os.getcwd(), req_gpu_index="", pre_reqt="2")

    # tick = 0
    # print(scheduler.log_task(1))
    time.sleep(5)
    print(scheduler.follow_task(1))
    
    print(scheduler.get_status())
    scheduler.shutdown()

    print(scheduler.ready_to_shutdown())
    
    # while not scheduler.ready_to_shutdown():
    #     time.sleep(1)
    #     tick += 1
    #     print(tick, scheduler.get_status())

    #     if tick == 10:
    #         # print(scheduler.kill_task(1))
    #         # print(scheduler.kill_task(3))

    #         scheduler.add_task(cmd="sleep 10s && echo world", req_memory=2000, path=os.getcwd(), req_gpu_index="", pre_reqt="")
        
        # if tick == 7:
        #     print(scheduler.restart_task(1, False))

        # if tick == 15:
            # print(scheduler.remove_task(2))
            # print(scheduler.remove_task(3))
    # print(scheduler.get_status())
    # scheduler.shutdown()