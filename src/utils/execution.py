import subprocess
import sys
import ast
import tempfile
import os

def get_function_name(code: str) -> str:
    """
    Extracts the name of the last function defined in the code string.
    """
    try:
        tree = ast.parse(code)
        for node in reversed(tree.body):
            if isinstance(node, ast.FunctionDef):
                return node.name
    except Exception:
        pass
    return None

def run_code(code: str, test_input: str) -> str:
    """
    Executes the given code with the provided test_input.
    
    Args:
        code: The python code containing the function to test.
        test_input: A string representation of the arguments to pass to the function.
                    e.g., "1, 2" or "[1, 2], 3".
    
    Returns:
        The string representation of the return value, or 'UNDEFINED' if execution fails.
    """
    func_name = get_function_name(code)
    if not func_name:
        return "UNDEFINED"

    # Construct the script to run
    # We use string concatenation instead of f-string for the whole block
    # to avoid issues if 'code' contains triple quotes.
    
    script = "import sys\n"
    script += "from typing import List, Tuple, Optional, Dict, Any\n\n"
    script += code + "\n\n"
    
    script += "try:\n"
    script += f"    result = {func_name}({test_input})\n"
    script += "    print(repr(result))\n"
    script += "except Exception as e:\n"
    script += "    print('UNDEFINED')\n"
    script += "    print(e)\n"

    tmp_path = ""
    try:
        # Write to a temporary file to execute
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
            tmp.write(script)
            tmp_path = tmp.name
            
        # Run the subprocess
        # Set a timeout to prevent infinite loops
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        output = result.stdout.strip()
        
        # If there was an error during execution (caught by try/except in script)
        if "UNDEFINED" in output:
            return output # Return the full output including the error message
            
        # If the subprocess failed (e.g. syntax error not caught)
        if result.returncode != 0:
            return "UNDEFINED"
            
        return output

    except subprocess.TimeoutExpired:
        return "UNDEFINED"
    except Exception as e:
        return "UNDEFINED"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
