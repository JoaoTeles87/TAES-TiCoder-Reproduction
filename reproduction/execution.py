import multiprocessing
import sys
import time
from io import StringIO
from contextlib import redirect_stdout

# Constants matching ticode/src/config.py
TEST_PREFIX = 'test_'

def unsafe_execute(code, test, func_name, result_queue):
    """
    Function to be executed in a separate process.
    """
    try:
        # Create a new namespace for execution
        ns = {}
        
        # Capture stdout to avoid cluttering the console
        with redirect_stdout(StringIO()):
            # Execute the test
            # Based on ticode/src/execution.py logic:
            # sol = imports + code + "\n" + test
            # And then appends the function call:
            # sol += f"{config.TEST_PREFIX + func_name}()"
            
            full_code = code + "\n" + test + "\n"
            if func_name:
                full_code += f"{TEST_PREFIX}{func_name}()"
            
            exec(full_code, ns)
            
        result_queue.put(("PASSED", None))
    except Exception as e:
        msg = str(e)
        if not msg:
            msg = repr(e)
        result_queue.put(("FAILED", msg))

def execute_code(code, test, func_name=None, timeout=1.0):
    """
    Executes the code and test with a timeout.
    
    Args:
        code (str): Source code to execute.
        test (str): Test code (function definition) to execute.
        func_name (str): Name of the function being tested. 
                         The test function is assumed to be named 'test_' + func_name.
        timeout (float): Timeout in seconds.
        
    Returns:
        tuple: (bool, str) - (True, None) if passed, (False, error_message) if failed.
    """
    # Create a queue to communicate with the worker process
    queue = multiprocessing.Queue()
    
    # Create the worker process
    p = multiprocessing.Process(target=unsafe_execute, args=(code, test, func_name, queue))
    
    try:
        p.start()
        p.join(timeout)
        
        if p.is_alive():
            p.terminate()
            p.join()
            return False, f"TimeoutError: Execution exceeded {timeout} seconds"
        
        if not queue.empty():
            status, message = queue.get()
            if status == "PASSED":
                return True, None
            else:
                return False, message
        else:
            # This might happen if the process died without writing to queue (e.g. segfault)
            return False, "Process crashed or produced no result"
            
    except Exception as e:
        return False, f"Execution error: {str(e)}"