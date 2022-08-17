import os 
import time
import argparse
from .server import start_server
import jsonrpclib 
import sys

def start_server_func(args):
    start_server()

def parse_list(arg):
    if arg != "":
        arg = arg.split(',')
        arg = [int(x) for x in arg]
    else:
        arg = []
    return arg

def add_func(args):
    server = jsonrpclib.Server("http://127.0.0.1:6789")
    
    ret_msg = server.enqueue(args.cmd, args.mem, args.gpu, args.after)
    print(ret_msg)

def remove_func(args):
    server = jsonrpclib.Server("http://127.0.0.1:6789")
    ret_msg = server.dequeue(args.task)
    print(ret_msg)

def status_func(args):
    server = jsonrpclib.Server("http://127.0.0.1:6789")
    print(server.get_status())

def commit_func(args):
    server = jsonrpclib.Server("http://127.0.0.1:6789")
    ret_msg = server.commit_task(args.task)
    print(ret_msg)

def kill_func(args):
    server = jsonrpclib.Server("http://127.0.0.1:6789")
    ret_msg = server.kill_task(args.task)
    print(ret_msg)

def restart_func(args):
    server = jsonrpclib.Server("http://127.0.0.1:6789")
    ret_msg = server.restart_task(args.task)
    print(ret_msg)

# def modify_func(args):
#     server = jsonrpclib.Server("http://127.0.0.1:6789")
#     ret_msg = server.restart_task(args.task, args.cmd, args.mem, args.gpu)
#     print(ret_msg)

def watch_func(args):
    server = jsonrpclib.Server("http://127.0.0.1:6789")
    while True:
        os.system("clear")
        print(server.get_status())
        time.sleep(3.0)


def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument("--mem", default=20, type=int)
    # parser.add_argument("--mem_inMB", default=-1, type=int)
    # parser.add_argument("--device_id", default=0, type=int)
    # parser.add_argument("operation", default="start-server", type=str)
    # parser.add_argument("--cmd", default="echo this is ", type=str)

    subparsers = parser.add_subparsers(help='operation')

    start_server_parser = subparsers.add_parser(name='start-server')
    start_server_parser.set_defaults(func=start_server_func)

    add_parser = subparsers.add_parser(name='add')
    add_parser.add_argument('--cmd', required=True, help='command', type=str)
    add_parser.add_argument('--mem', required=True, help='required memory (in MB)', type=int)
    add_parser.add_argument('--gpu', required=False, help='gpu device id', type=int, default=-1)
    add_parser.add_argument('--after', required=False, help='after task id list', type=str, default="")
    
    add_parser.set_defaults(func=add_func)

    remove_parser = subparsers.add_parser(name='remove')
    remove_parser.add_argument('--task', required=True, help='task id', type=int, default=-1)
    remove_parser.set_defaults(func=remove_func)

    watch_parser = subparsers.add_parser(name='watch')
    watch_parser.set_defaults(func=watch_func)

    status_parser = subparsers.add_parser(name='status')
    status_parser.set_defaults(func=status_func)

    commit_parser = subparsers.add_parser(name='commit')
    commit_parser.add_argument('--task', required=False, help='task id', type=int, default=-1)
    commit_parser.set_defaults(func=commit_func)

    restart_parser = subparsers.add_parser(name='restart')
    restart_parser.add_argument('--task', required=False, help='task id', type=int, default=-1)
    restart_parser.set_defaults(func=restart_func)

    kill_parser = subparsers.add_parser(name='kill')
    kill_parser.add_argument('--task', required=True, help='task id', type=int, default=-1)
    kill_parser.set_defaults(func=kill_func)

    args = parser.parse_args()
    
    if len(sys.argv) > 1:
        args.func(args)
    else:   
        parser.print_help()


if __name__ == "__main__":
    main()
    
