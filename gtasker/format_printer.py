from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.box import SIMPLE_HEAVY
from .task import Task, echo_task, sleep_task, failing_task, ls_task, TaskStatus
import os
import datetime

status_to_colortext = {
    "SUCCESS": Text("Success", style="green"),
    "FAILED": Text("Failed", style="red"),
    "RUNNING": Text("Running", style="green"),
    "PENDING": Text("Pending", style="yellow"),
    "KILLED": Text("Killed", style="red"),
}

def format_print_task_status(task_status_tuple_list):
    table = Table(show_header=True, show_lines=True, box=SIMPLE_HEAVY, header_style="bold", title="Task Status")
    # set column 
    table.add_column("ID", style=None)
    table.add_column("Status", style=None)
    table.add_column("Command", style=None)
    table.add_column("Path", style=None)
    table.add_column("Type", style=None)
    table.add_column("Req GPU", style=None)
    table.add_column("Pre Task", style=None)
    table.add_column("Start", style=None)
    table.add_column("End", style=None)

    for task_status_tuple in task_status_tuple_list:
        task_status_tuple = list(task_status_tuple)
        task_status_tuple[1] = status_to_colortext[task_status_tuple[1]]
        table.add_row(*task_status_tuple)


    console = Console()
    console.print(table)

