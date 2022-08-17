from gtasker.tracker import GPUTracker

def test_init():
    gpu_tracker = GPUTracker()
    gpu_tracker._get_gpu_info = lambda: {'gpus': [{'memory.total': 100, 'memory.used': 0, 'processes': []}, {'memory.total': 200, 'memory.used': 0, 'processes': []}]}
    gpu_tracker.update()
    
    assert gpu_tracker.free_memory[0] == 100
    assert gpu_tracker.free_memory[1] == 200

def test_book():
    gpu_tracker = GPUTracker()
    gpu_tracker._get_gpu_info = lambda: {'gpus': [{'memory.total': 100, 'memory.used': 0, 'processes': []}, {'memory.total': 200, 'memory.used': 0, 'processes': []}]}
    gpu_tracker.book_memory(0, 80, 1234)
    gpu_tracker.book_memory(1, 100, 1235)
    gpu_tracker.update()
    assert gpu_tracker.free_memory[0] == 20
    assert gpu_tracker.free_memory[1] == 100

    gpu_tracker.unbook_memory(0, 1234)
    gpu_tracker.update()
    assert gpu_tracker.free_memory[0] == 100
    assert gpu_tracker.free_memory[1] == 100

def test_flush():
    gpu_tracker = GPUTracker()
    gpu_tracker._get_gpu_info = lambda: {'gpus': [{'memory.total': 100, 'memory.used': 0, 'processes': []}, {'memory.total': 200, 'memory.used': 0, 'processes': []}]}
    gpu_tracker.book_memory(0, 80, 1234)
    gpu_tracker.book_memory(1, 100, 1235)
    gpu_tracker.update()
    assert gpu_tracker.free_memory[0] == 20
    assert gpu_tracker.free_memory[1] == 100

    gpu_tracker._get_gpu_info = lambda: {'gpus': [{'memory.total': 100, 'memory.used': 75, 'processes': [{"pid": 1234}]}, {'memory.total': 200, 'memory.used': 0, 'processes': []}]}
    gpu_tracker.update()
    assert gpu_tracker.free_memory[0] == 25
    assert gpu_tracker.free_memory[1] == 100

    gpu_tracker._get_gpu_info = lambda: {'gpus': [{'memory.total': 100, 'memory.used': 75, 'processes': [{"pid": 1234}]}, {'memory.total': 200, 'memory.used': 70, 'processes': [{"pid": 2345}]}]}
    gpu_tracker.update()
    assert gpu_tracker.free_memory[0] == 25
    assert gpu_tracker.free_memory[1] == 30

def test_timeout():
    from collections import defaultdict
    gpu_tracker = GPUTracker()
    gpu_tracker._get_gpu_info = lambda: None
    gpu_tracker.update()

    assert gpu_tracker.free_memory == defaultdict(int)
    
def test_real():
    gpu_tracker = GPUTracker()
    gpu_tracker.update()

    assert len(gpu_tracker.free_memory) == 10
    print(gpu_tracker.free_memory)

if __name__ == "__main__":
    # test_init()
    test_timeout()
    test_real()
