import os 
import time
import argparse
from .scheduler import TaskScheduler
import jsonrpclib 
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
import sys
import threading
import subprocess
from .utils import GTASTER_ROOT, HOST, PORT


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
    os.makedirs(GTASTER_ROOT, exist_ok=True)
    

def start_server():
    # Create server
    os.environ["PYTHONUNBUFFERED"] = "1"
    server = MyRPCServer((HOST, PORT))
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
    server.register_function(server.shutdown, "server_shutdown")

    # print("Starting scheduler....")

    ret_msg = scheduler.serve_forever()
    server.serve_forever()
    # print(ret_msg)
    exit(0)

def fork_daemon():
    cmd = "python3 -m gtasker.cmdparser start-server"
    subprocess.Popen(cmd, shell=True, cwd=os.getcwd(), env=os.environ.copy(), executable="/bin/bash", start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    exit(0)
    

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
    ret_msg = server.restart_task(args.task)
    print(ret_msg)

@rpc_cmd
def clean_task_func(args):
    server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
    ret_msg = server.clean_task()
    print(ret_msg)

@rpc_cmd
def follow_task_func(args):
    server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
    ret_msg = server.follow_task(args.task)
    print(ret_msg)

@rpc_cmd
def log_task_func(args):
    server = jsonrpclib.Server(f"http://{HOST}:{PORT}")
    ret_msg = server.log_task(args.task)
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
    ret_msg = server.get_status()
    print(ret_msg)
    # Format the output # TODO





# def watch_func(args):
#     server = jsonrpclib.Server("http://127.0.0.1:6789")
#     while True:
#         os.system("clear")
#         print(server.get_status())
#         time.sleep(3.0)


def main():
    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers(help='operation')

    start_server_parser = subparsers.add_parser(name='start-server')
    start_server_parser.add_argument('--daemon', action='store_true', help='run the server as a daemon')
    start_server_parser.set_defaults(func=start_server_func)

    add_parser = subparsers.add_parser(name='add')
    add_parser.add_argument('--cmd', required=True, help='command', type=str)
    add_parser.add_argument('--mem', required=False, help='required memory (in MB)', type=int, default=0)
    add_parser.add_argument('--path', required=False, help='working directory', type=str, default=os.getcwd())
    add_parser.add_argument('--gpu', required=False, help='gpu device id list', type=str, default="")
    add_parser.add_argument('--after', required=False, help='after task id list', type=str, default="")
    
    add_parser.set_defaults(func=add_task_func)



    remove_parser = subparsers.add_parser(name='remove')
    remove_parser.add_argument('--task', required=True, help='task id', type=int, default=-1)
    remove_parser.set_defaults(func=remove_task_func)


    stash_parser = subparsers.add_parser(name='stash')
    stash_parser.add_argument('--task', required=True, help='task id', type=int, default=-1)
    stash_parser.set_defaults(func=stash_task_func)

    kill_parser = subparsers.add_parser(name='kill')
    kill_parser.add_argument('--task', required=True, help='task id', type=int, default=-1)
    kill_parser.set_defaults(func=kill_task_func)

    restart_parser = subparsers.add_parser(name='restart')
    restart_parser.add_argument('--task', required=True, help='task id', type=int, default=-1)
    restart_parser.set_defaults(func=restart_task_func)

    clean_parser = subparsers.add_parser(name='clean')
    clean_parser.set_defaults(func=clean_task_func)

    follow_parser = subparsers.add_parser(name='follow')
    follow_parser.add_argument('--task', required=True, help='task id', type=int, default=-1)
    follow_parser.set_defaults(func=follow_task_func)

    log_parser = subparsers.add_parser(name='log')
    log_parser.add_argument('--task', required=True, help='task id', type=int, default=-1)
    log_parser.set_defaults(func=log_task_func)

    shutdown_parser = subparsers.add_parser(name='shutdown')
    shutdown_parser.add_argument('--force', required=False, help='force shutdown', default=False, action='store_true')
    shutdown_parser.set_defaults(func=shutdown_func)

    get_status_parser = subparsers.add_parser(name='status')
    get_status_parser.set_defaults(func=get_status_func)



    args = parser.parse_args()
    
    if len(sys.argv) > 1:
        args.func(args)
    else:   
        parser.print_help()


if __name__ == "__main__":
    main()
    
