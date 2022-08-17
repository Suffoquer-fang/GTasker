from gtasker.task import Task, TaskStatus, echo_task, sleep_task, failing_task, ls_task
import threading

def test_task_init():
    task = echo_task()
    assert task.id == 1
    assert task.cmd == "echo 'Hello World'"
    assert task.req_memory == 0
    print(task.path)

    task = sleep_task()
    assert task.id == 2
    assert task.cmd == "sleep 5"
    assert task.req_memory == 0
    print(task.path)

def test_task_success():
    task = echo_task()
    task.spawn(threading.Lock(), None)
    assert task.status == TaskStatus.SUCCESS
    assert task.executed_proc is not None
    assert task.start_time is not None
    assert task.end_time is not None
    print(task.executed_proc)
    print(task.start_time)
    print(task.end_time)
    print(task.status)

def test_task_failed():
    task = failing_task()
    task.spawn(threading.Lock(), None)
    assert task.status == TaskStatus.FAILED
    assert task.executed_proc is not None
    assert task.start_time is not None
    assert task.end_time is not None
    print(task.executed_proc)
    print(task.start_time)
    print(task.end_time)
    print(task.status)

def test_task_path():
    task = ls_task()
    task.spawn(threading.Lock(), None)
    assert task.path == "/home/fangyan/Workspace/ColBERT/"
    print(task.path)


def test_subprocess_execute():
    task = sleep_task()
    mutex = threading.Lock()
    t = threading.Thread(target=task.spawn, args=(mutex, None))
    t.start()

    mutex.acquire()
    assert task.status == TaskStatus.RUNNING
    assert task.executed_proc is not None
    assert task.start_time is not None
    assert task.end_time is None
    print(task.executed_proc)
    print(task.start_time)
    print(task.end_time)
    print(task.status)

    mutex.release()

    t.join()
    assert task.status == TaskStatus.SUCCESS
    assert task.executed_proc is not None
    assert task.start_time is not None
    assert task.end_time is not None
    print(task.executed_proc)
    print(task.start_time)
    print(task.end_time)
    print(task.status)



# test_subprocess_execute()
test_task_path()