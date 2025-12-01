import sys
import os
import json
from unittest.mock import MagicMock

# Mock openai module BEFORE importing models
sys.modules["openai"] = MagicMock()

# Add src to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../ticode/src')))

# Import reproduction modules
import prompt
from data_parser import DataParser, ProgramData
import cache_parser
import models

# Mock Model
class MockChoice:
    def __init__(self, content, index=0):
        self.message = MagicMock()
        self.message.content = content
        self.finish_reason = "stop"
        self.index = index

class MockResponse:
    def __init__(self, choices):
        self.choices = choices

class MockModel:
    def __init__(self, model_name="gpt-5-nano"):
        self.model_name = model_name

    def create_completion(self, **kwargs):
        n = kwargs.get('n', 1)
        choices = []
        for i in range(n):
            choices.append(MockChoice(f"def solution():\n    return 'solution_{i}'", index=i))
        return choices

# Monkey patch models.GPT5Nano
models.GPT5Nano = MockModel

def main():
    print("Starting serialization test...")
    
    # 1. Load Data
    mbpp_file = os.path.join(os.path.dirname(__file__), "../datasets/mbpp/sanitized-mbpp.json")
    if not os.path.exists(mbpp_file):
        print(f"Error: Dataset file not found at {mbpp_file}")
        return

    data = DataParser.read_json_or_jsonl_to_list(mbpp_file)[:1] # Take 1 task
    prog_data: ProgramData = DataParser.parse_sanitized_mbpp_data(data[0])
    
    print(f"Loaded task: {prog_data.func_name}")

    # 2. Generate Prompts
    code_prompt_msgs = prompt.code_prompt(prog_data)
    test_prompt_msgs = prompt.test_prompt(prog_data)
    
    # 3. "Call" Model
    model = models.GPT5Nano()
    
    # Generate Solutions
    print("Generating solutions...")
    solution_choices = model.create_completion(messages=code_prompt_msgs, n=3)
    
    # Generate Tests
    print("Generating tests...")
    test_choices = model.create_completion(messages=test_prompt_msgs, n=3)
    
    # We need to extract the user prompt content for the key
    # CodeT expects the prompt in the saved file to match what it expects from source (MBPP prompt)
    prompt_key = prog_data.original_prompt
    
    # Prepare output paths
    output_dir = os.path.join(os.path.dirname(__file__), "codet_test_output")
    os.makedirs(output_dir, exist_ok=True)
    
    sol_file = os.path.join(output_dir, "solutions.jsonl")
    test_file = os.path.join(output_dir, "tests.jsonl")
    
    # Clean previous files
    if os.path.exists(sol_file): os.remove(sol_file)
    if os.path.exists(test_file): os.remove(test_file)

    cache = cache_parser.CacheParser()

    cache.save_codet_jsonl(solution_choices, prompt_key, sol_file)
    cache.save_codet_jsonl(test_choices, prompt_key, test_file)
    
    print(f"Saved solutions to {sol_file}")
    print(f"Saved tests to {test_file}")
    
    # 5. Run CodeT
    # We need to call codet/CodeT/main.py
    # Arguments:
    # --source_path_for_solution (original mbpp file)
    # --predict_path_for_solution (our sol_file)
    # --source_path_for_test (original mbpp file)
    # --predict_path_for_test (our test_file)
    # --cache_dir (output_dir)
    
    # Convert MBPP to JSONL for CodeT
    mbpp_jsonl_file = os.path.join(output_dir, "mbpp.jsonl")
    with open(mbpp_file, 'r', encoding='utf-8') as f:
        mbpp_data = json.load(f)
    
    with open(mbpp_jsonl_file, 'w', encoding='utf-8') as f:
        for entry in mbpp_data:
            # CodeT expects 'entry_point'
            if 'entry_point' not in entry:
                try:
                    func_name, _, _ = DataParser.get_func_details(entry)
                    entry['entry_point'] = func_name
                except Exception as e:
                    print(f"Failed to extract entry_point for task {entry.get('task_id')}: {e}")
                    pass

            # CodeT expects 'test' field, but MBPP has 'test_list'
            if 'test_list' in entry:
                entry['test'] = entry.pop('test_list')

            f.write(json.dumps(entry) + "\n")
            
    codet_main = os.path.abspath(os.path.join(os.path.dirname(__file__), "../codet/CodeT/main.py"))
    
    cmd = (
        f"\"{sys.executable}\" {codet_main} "
        f"--source_path_for_solution {mbpp_jsonl_file} "
        f"--predict_path_for_solution {sol_file} "
        f"--source_path_for_test {mbpp_jsonl_file} "
        f"--predict_path_for_test {test_file} "
        f"--cache_dir {output_dir} "
        f"--test_case_limit 1 "
        f"--timeout 1.0"
    )
    
    import subprocess
    print(f"Running CodeT: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("CodeT execution SUCCESS")
        print("STDOUT:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("CodeT execution FAILED")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)

if __name__ == "__main__":
    main()
