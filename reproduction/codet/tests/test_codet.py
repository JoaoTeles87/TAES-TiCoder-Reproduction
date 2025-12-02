import os
import sys
import json
import subprocess

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ticode/src')))

from data_parser import DataParser

# Configuration
TOY_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../datasets/mbpp/sanitized-mbpp.json"))
CODET_OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "codet_output"))

def run_codet_execution(sol_file=None, test_file=None):
    """Run CodeT execution with generated solutions and tests"""
    print("--- Running CodeT Execution ---")
    
    # Use default paths if not provided
    if sol_file is None:
        sol_file = os.path.join(CODET_OUTPUT_DIR, 'solutions.jsonl')
    if test_file is None:
        test_file = os.path.join(CODET_OUTPUT_DIR, 'tests.jsonl')
    
    # Prepare MBPP JSONL for CodeT
    mbpp_jsonl_file = os.path.join(CODET_OUTPUT_DIR, "mbpp.jsonl")
    with open(TOY_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)[:10]
    
    with open(mbpp_jsonl_file, 'w', encoding='utf-8') as f:
        for entry in data:
            if 'prompt' not in entry and 'text' in entry:
                entry['prompt'] = entry['text']
            if 'entry_point' not in entry:
                try:
                    func_name, _, _ = DataParser.get_func_details(entry)
                    entry['entry_point'] = func_name
                except:
                    pass
            if 'test_list' in entry:
                test_list = entry.pop('test_list')
                if isinstance(test_list, list):
                    entry['test'] = "\n".join(test_list)
                else:
                    entry['test'] = test_list
            f.write(json.dumps(entry) + "\n")

    codet_main = os.path.abspath(os.path.join(os.path.dirname(__file__), "../codet/CodeT/main.py"))
    cmd = (
        f"\"{sys.executable}\" {codet_main} "
        f"--source_path_for_solution {mbpp_jsonl_file} "
        f"--predict_path_for_solution {sol_file} "
        f"--source_path_for_test {mbpp_jsonl_file} "
        f"--predict_path_for_test {test_file} "
        f"--cache_dir {CODET_OUTPUT_DIR} "
        f"--test_case_limit 1 "
        f"--timeout 2.0"
    )
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("CodeT execution finished.")
        # Parse output for accuracy
        for line in result.stdout.splitlines():
            if "pass@1" in line.lower() or "accuracy" in line.lower():
                print(f"CodeT Result: {line.strip()}")
        # Also check output file
        print("STDOUT snippet:", result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        print("STDERR snippet:", result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
    except subprocess.CalledProcessError as e:
        print("CodeT execution FAILED")
        print(e.stdout)
        print(e.stderr)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run CodeT execution")
    parser.add_argument("--input_dir", type=str, default=CODET_OUTPUT_DIR, help="Path to CodeT input directory (containing solutions.jsonl and tests.jsonl)")
    
    args = parser.parse_args()
    
    CODET_OUTPUT_DIR = os.path.abspath(args.input_dir)
    
    run_codet_execution()

    print("\n=== CodeT Execution Complete ===")
