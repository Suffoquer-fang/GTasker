import os 
import time
import argparse
from .scheduler import TaskScheduler
from . import __version__
import jsonrpclib 
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
import sys
import threading
import subprocess
from .utils import GTASKER_LOG_PATH, HOST, PORT, GTASKER_SERVER_LOG_PATH, follow, get_log_file_path
from .format_printer import format_print_task_status

class MyRPCServer(SimpleJSONRPCServer):
    def __init__(self, *args, **kwargs):
        SimpleJSONRPCServer.__init__(self, *args, **kwargs)
        self._shutdown = False

    def shutdown(self):
        self._shutdown = True

    def serve_forever(self):
        while not self._shutdown:
            self.handle_request()


def prepare_everything():
    os.makedirs(GTASKER_LOG_PATH, exist_ok=True)
    print("GTASKER_LOG_PATH: %s" % GTASKER_LOG_PATH)
    os.makedirs(GTASKER_SERVER_LOG_PATH, exist_ok=True)

    

def start_server():
    # Create server
    os.environ["PYTHONUNBUFFERED"] = "1"
    try:
        server = MyRPCServer((HOST, PORT))
    except Exception:
        print("Cannot start the server. Please make sure the server is not running.")
        exit(0)

    print("Starting RPC server on %s:%d" % (HOST, PORT))

    prepare_everything()

    scheduler = TaskScheduler()
    server.register_function(scheduler.add_task)
    server.register_function(scheduler.remove_task)
    server.register_function(scheduler.stash_task)
    server.register_function(scheduler.kill_task)
    server.register_function(scheduler.restart_task)
    server.register_function(scheduler.clean_task)
    server.register_function(scheduler.follow_task)
    server.register_function(scheduler.log_task)
    server.register_function(scheduler.shutdown, "scheduler_shutdown")
    server.register_function(scheduler.ready_to_shutdown)
    server.register_function(scheduler.serve_forever)
    server.register_function(scheduler.get_status)
    server.register_function(scheduler.task_is_running)
    server.register_function(scheduler.task_exists)
    server.register_function(server.shutdown, "server_shutdown")

    # print("Starting scheduler....")

    ret_msg = scheduler.serve_forever()
    server.serve_forever()
    # print(ret_msg)
    # exit(0)

def fork_daemon():
    # cmd = "python3 -m gtasker.cmdparser start-server"
    cmd = "gta start-server"
    log_file = open(os.path.join(GTASKER_SERVER_LOG_PATH, "server.log"), "wb")
    err_file = open(os.path.join(GTASKER_SERVER_LOG_PATH, "server.err"), "wb")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    subprocess.Popen(cmd, shell=True, cwd=os.getcwd(), env=env, executable="/bin/bash", start_new_session=True, stdout=log_file, stderr=err_file)
    print("Server started on %s:%d" % (HOST, PORT))
    

def start_server_func(args):
    if args.daemon:
        fork_daemon()
    else:
        start_server()

def rpc_cmd(func):
    def wrapper(args):
        try:
            os.environ["PYTHONUNBUFFERED"] = "1"
            func(args)
        except ConnectionRefusedError:
            print("Cannot connect to the server. Please make sure the server is running.")
    return wrapper

@rpc_cmd
def add_task_func(args):
    server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
    ret_msg = server.add_task(args.cmd, args.mem, args.path, args.gpu, args.after)
    print(ret_msg)

@rpc_cmd
def remove_task_func(args):
    server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
    ret_msg = server.remove_task(args.task)
    print(ret_msg)

@rpc_cmd
def stash_task_func(args):
    server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
    ret_msg = server.stash_task(args.task)
    print(ret_msg)

@rpc_cmd
def kill_task_func(args):
    server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
    ret_msg = server.kill_task(args.task)
    print(ret_msg)

@rpc_cmd
def restart_task_func(args):
    server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
    ret_msg = server.restart_task(args.task, args.inplace)
    print(ret_msg)

@rpc_cmd
def clean_task_func(args):
    server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
    ret_msg = server.clean_task()
    print(ret_msg)

# @rpc_cmd
# def follow_task_func(args):
#     server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
#     ret_msg = server.follow_task(args.task)
#     print(ret_msg)


@rpc_cmd
def follow_task_func(args):
    server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
    if not server.task_exists(args.task):
        print(f"Task {args.task} Not Found")
        return
    log_file_path = get_log_file_path(args.task)
    
    stop_func = lambda: not server.task_is_running(args.task)
    follow(log_file_path, stop_func=stop_func)


@rpc_cmd
def log_task_func(args):
    server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
    ret_msg = server.log_task(args.task, args.lines)
    print(ret_msg)

@rpc_cmd
def shutdown_func(args):
    server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
    ready_to_shutdown = server.ready_to_shutdown()
    if args.force or ready_to_shutdown:
        ret_msg = server.scheduler_shutdown()
        server.server_shutdown()
        print(ret_msg)
    else:
        print("There are task not finished. Please use --force to shutdown.")

@rpc_cmd
def get_status_func(args):
    server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
    format_print_task_status(server.get_status())





# def watch_func(args):
#     server = jsonrpclib.Server("http://127.0.0.1:6789")
#     while True:
#         os.system("clear")
#         print(server.get_status())
#         time.sleep(3.0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version',
                    version='%(prog)s {version}'.format(version=__version__))

    subparsers = parser.add_subparsers(title='commands')

    start_server_parser = subparsers.add_parser(name='start-server', help='Start the daemon server', description='Start the daemon server')
    start_server_parser.add_argument('-d', '--daemon', action='store_true', help='run the server as a daemon')
    start_server_parser.set_defaults(func=start_server_func)

    add_parser = subparsers.add_parser(name='add', help='Enqueue a task for execution', description='Enqueue a task for execution asd')
    add_parser.add_argument('cmd', help='Command of task', type=str)
    add_parser.add_argument('--mem', required=False, help='Required GPU memory (in MB)', type=int, default=0)
    add_parser.add_argument('--path', required=False, help='Working directory. Default is the current directory', type=str, default=os.getcwd())
    add_parser.add_argument('--gpu', required=False, help='Required GPU device id(s).', type=str, default="")
    add_parser.add_argument('--after', required=False, help='Prerequist task(s)', type=str, default="")
    add_parser.set_defaults(func=add_task_func)



    remove_parser = subparsers.add_parser(name='remove', help='Remove a task from the queue', description='Remove a task from the queue')
    remove_parser.add_argument('task', help='task id', type=int, default=-1)
    remove_parser.set_defaults(func=remove_task_func)


    # stash_parser = subparsers.add_parser(name='stash')
    # stash_parser.add_argument('task', help='task id', type=int, default=-1)
    # stash_parser.set_defaults(func=stash_task_func)

    kill_parser = subparsers.add_parser(name='kill', help='Kill a running task', description='Kill a running task')
    kill_parser.add_argument('task', help='task id', type=int, default=-1)
    kill_parser.set_defaults(func=kill_task_func)

    restart_parser = subparsers.add_parser(name='restart', help='Restart a task', description='Restart a task')
    restart_parser.add_argument('task', help='task id', type=int, default=-1)
    restart_parser.add_argument('--inplace', action='store_true', help='restart the task in place')
    restart_parser.set_defaults(func=restart_task_func)

    clean_parser = subparsers.add_parser(name='clean', help='Remove all success tasks from the queue', description='Remove all success tasks from the queue')
    clean_parser.set_defaults(func=clean_task_func)

    follow_parser = subparsers.add_parser(name='follow', help='Follow the output of a running task', description='Follow the output of a running task')
    follow_parser.add_argument('task', help='task id', type=int, default=-1)
    follow_parser.set_defaults(func=follow_task_func)

    log_parser = subparsers.add_parser(name='log', help='Display the output log of a task', description='Display the output log of a task')
    log_parser.add_argument('task', help='task id', type=int, default=-1)
    log_parser.add_argument('-l', '--lines', required=False, help='display last n lines', type=int, default=20)
    log_parser.set_defaults(func=log_task_func)

    shutdown_parser = subparsers.add_parser(name='shutdown', help='Remotely shutdown the daemon', description='Remotely shutdown the daemon')
    shutdown_parser.add_argument('-f', '--force', required=False, help='force shutdown', default=False, action='store_true')
    shutdown_parser.set_defaults(func=shutdown_func)

    get_status_parser = subparsers.add_parser(name='status', help='Display the status of the daemon', description='Display the status of the daemon')
    get_status_parser.set_defaults(func=get_status_func)



    args = parser.parse_args()
    
    if len(sys.argv) > 1:
        args.func(args)
    else:   
        parser.print_help()


if __name__ == "__main__":
    main()
    
