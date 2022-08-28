import os, time, logging
from gtasker.scheduler import TaskScheduler
from gtasker.utils import follow

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    # os.environ["PYTHONUNBUFFERED"] = "1"
    scheduler = TaskScheduler()
    scheduler.serve_forever()

    scheduler.add_task(cmd="conda activate torchenv && sh run_real_gpu_test.sh", req_memory=2500, path="./local_test", req_gpu_index="", pre_reqt="")
    # scheduler.add_task(cmd="sleep 10s && echo hello", req_memory=3000, path=os.getcwd(), req_gpu_index="1", pre_reqt="")
    # scheduler.add_task(cmd="sleep 10s && echo world", req_memory=0, path=os.getcwd(), req_gpu_index="", pre_reqt="2")
    time.sleep(5)
    print(scheduler.get_status())
    print(scheduler.follow_task(1))
    while not scheduler.ready_to_shutdown():
        time.sleep(1)

    scheduler.shutdown()