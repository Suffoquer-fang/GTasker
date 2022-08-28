# GTasker

![GTasker](https://github.com/Suffoquer-fang/GTasker/blob/main/imgs/gtasker.svg)

GTasker is a simple command-line scheduling tool for sequential and parallel execution of CPU or single-GPU tasks.

## Installation
Install from PyPI.
```shell
pip install gtasker
```
Or install from GitHub.
```
pip install git+https://github.com/suffoquer-fang/Gtasker.git@main
```
## Usage
```
usage: gta [-h] [-v] [commands]

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit

commands:
    start-server        Start the daemon server
    add                 Enqueue a task for execution
    remove              Remove a task from the queue
    kill                Kill a running task
    restart             Restart a task
    clean               Remove all success tasks from the queue
    follow              Follow the output of a running task
    log                 Display the output log of a task
    shutdown            Remotely shutdown the daemon
    status              Display the status of the daemon
```

## Quick Start

### Start the daemon server
You have to start the daemon before using `gta` client.

Run in the current shell.
```
gta start-server
```
Add the `-d` or `--daemon` flag to run in the background.
```
gta start-server -d
```

### Adding new tasks

To add a task:
```
gta add ls
```
Or a more complex command:
```
gta add "sleep 10 && echo 'hello world' && exit 0"
```

You can add `--path {path}` argument to specify the working directory for the task, which is set to current directoy by default.

If the task should be executed after some certain task(s), you can add `--after {after}` argument to set the pre-requist tasks. The task will be executed only after all pre-tasks have been successfully completed.

For GPU tasks, you can set the required GPU memory by `--mem {memory}`. The task will be executed on a GPU with more free memory than required. 

You may further set the required GPU device(s) by `--gpu {gpu_devices}`. The task will only be executed on the preset GPU device(s). 

### Controlling tasks

You can kill a running task by `gta kill {task_id}`.

To restart a killed (success / failed) task, you can simply use `gta restart {task_id}` and the task will be restarted as a new one. You can add `--inplace` flag to restart it in place.

### Displaying tasks

You can use `gta status` to get the current status of task queue.

To look at the output log of a task, you can use `gta log {task_id}` or `gta follow {task_id}` to follow the output of a running task.

## References
This repo is inspired by [pueue](https://github.com/Nukesor/pueue), sincerely grateful for it.




