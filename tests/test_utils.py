from gtasker.utils import execute_cmd, get_children_pids, parse_str_to_list
import psutil
import os

def test_execute_cmd():
    output = execute_cmd('echo "hello"')
    assert output == b'hello\n'
    output = execute_cmd('sleep 2s && echo "hello"', timeout=1)
    assert output is None

def test_get_children_pids():
    # output = get_children_pids(os.getpid())
    # assert len(output) == 0

    # output = get_children_pids(os.getpid(), include_self=True)
    # print(output)
    # assert len(output) == 1

    output = get_children_pids(9999999, include_self=False)
    print(output)
    assert len(output) == 0

def test_parse_str_to_list():
    str_ = '1,2,3'
    assert parse_str_to_list(str_) == ['1', '2', '3']
    assert parse_str_to_list(str_, int) == [1, 2, 3]

    str_ = ''
    assert parse_str_to_list(str_) == []
    assert parse_str_to_list(str_, int) == []

# test_get_children_pids()
test_parse_str_to_list()