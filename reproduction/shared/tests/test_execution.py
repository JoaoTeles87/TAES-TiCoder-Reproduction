from execution import execute_code
import time

def test_execute_code_success():
    code = "def add(a, b):\n    return a + b"
    test = "def test_add():\n    assert add(1, 2) == 3"
    result, error = execute_code(code, test, func_name="add")
    assert result, f"Test failed with error: {error}"
    print("Success test passed")

def test_execute_code_failure():
    code = "def add(a, b):\n    return a + b"
    test = "def test_add():\n    assert add(1, 2) == 4"
    result, error = execute_code(code, test, func_name="add")
    assert not result, "Test succeeded but should have failed"
    assert "AssertionError" in error, f"Unexpected error message: {error}"
    print("Failure test passed")

def test_execute_code_timeout():
    code = "import time\ndef loop():\n    while True:\n        time.sleep(0.1)"
    test = "def test_loop():\n    loop()"
    start_time = time.time()
    result, error = execute_code(code, test, func_name="loop", timeout=1.0)
    end_time = time.time()
    
    assert not result, "Test succeeded but should have timed out"
    assert "TimeoutError" in error, f"Unexpected error message: {error}"
    assert end_time - start_time >= 1.0, "Timeout happened too quickly"
    print("Timeout test passed")

def test_execute_code_syntax_error():
    code = "def add(a, b):" # Missing body
    test = "def test_add():\n    add(1, 2)"
    result, error = execute_code(code, test, func_name="add")
    assert not result, "Test succeeded but should have failed with syntax error"
    # SyntaxError might be reported differently depending on python version/context, but it should fail
    print(f"Syntax error test passed with error: {error}")

if __name__ == "__main__":
    try:
        test_execute_code_success()
        test_execute_code_failure()
        test_execute_code_timeout()
        test_execute_code_syntax_error()
        print("All tests passed")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

