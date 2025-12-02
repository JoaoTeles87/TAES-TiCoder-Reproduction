import json
import os
import sys
from collections import Counter
from tqdm import tqdm

# Add current directory to path to import execution
sys.path.append(os.path.dirname(__file__))
from execution import execute_code

# Configuration
BASE_DIR = os.path.dirname(__file__)
SOLUTIONS_PATH = os.path.join(BASE_DIR, "codet_output", "solutions.jsonl")
TESTS_PATH = os.path.join(BASE_DIR, "codet_output", "tests.jsonl")
GROUND_TRUTH_PATH = os.path.join(BASE_DIR, "../datasets/mbpp/sanitized-mbpp.json")
RESULTS_PATH = os.path.join(BASE_DIR, "simple_codet_results.json")

def load_jsonl(path):
    data = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            data[entry['task_id']] = entry
    return data

def load_ground_truth(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Convert list to dict keyed by task_id
    return {item['task_id']: item for item in data}

def create_ground_truth_test_code(test_list):
    """Wraps assert statements in a function."""
    test_code = "def check_solution():\n"
    for test in test_list:
        test_code += f"    {test}\n"
    return test_code

def clean_generated_test(test_code, func_name):
    """
    Simple cleanup to remove trailing calls that might crash execution.
    The generated tests sometimes end with a call to the function under test 
    without arguments, e.g., 'similar_elements()', which causes TypeError.
    """
    lines = test_code.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Remove lines that are just the function name call
        if stripped == f"{func_name}()":
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def main():
    print("Loading data...")
    solutions_data = load_jsonl(SOLUTIONS_PATH)
    tests_data = load_jsonl(TESTS_PATH)
    ground_truth_data = load_ground_truth(GROUND_TRUTH_PATH)

    results = []
    total_tasks = 0
    passed_tasks = 0

    # Filter to common task IDs (should be the 10 we processed)
    task_ids = sorted(list(set(solutions_data.keys()) & set(tests_data.keys()) & set(ground_truth_data.keys())))
    
    print(f"Processing {len(task_ids)} tasks...")

    for task_id in tqdm(task_ids):
        total_tasks += 1
        
        sol_entry = solutions_data[task_id]
        test_entry = tests_data[task_id]
        gt_entry = ground_truth_data[task_id]
        
        # Extract function name from ground truth (it's in the code usually, but we can parse it or guess)
        # MBPP sanitized usually has "def func_name("
        code_snippet = gt_entry['code']
        func_name = None
        for line in code_snippet.split('\n'):
            if line.strip().startswith('def '):
                func_name = line.strip().split(' ')[1].split('(')[0]
                break
        
        if not func_name:
            print(f"Could not find function name for task {task_id}, skipping.")
            continue

        generated_solutions = sol_entry['samples']
        generated_tests = test_entry['samples']
        
        # 1. Execute Generated Code vs Generated Tests
        # Matrix: solutions x tests
        # We want to find the solution that passes the most generated tests.
        
        solution_scores = []
        
        for i, sol_code in enumerate(generated_solutions):
            pass_count = 0
            for j, test_code in enumerate(generated_tests):
                # Clean test code
                cleaned_test_code = clean_generated_test(test_code, func_name)
                
                # We need to tell execute_code the test function name.
                # The generated tests are usually "def test_func_name(): ..."
                # So we pass func_name, and execute_code appends "test_" + func_name + "()"
                
                # However, the generated test function name might vary. 
                # Let's assume standard "test_" + func_name convention from the prompt.
                # If the model generated something else, execution might fail to call it.
                # But looking at samples, it seems consistent.
                
                passed, _ = execute_code(sol_code, cleaned_test_code, func_name=func_name, timeout=1.0)
                if passed:
                    pass_count += 1
            
            solution_scores.append((pass_count, sol_code))
        
        # 2. Select Best Solution
        # Sort by pass_count descending
        solution_scores.sort(key=lambda x: x[0], reverse=True)
        best_solution = solution_scores[0][1]
        best_score = solution_scores[0][0]
        
        # 3. Evaluate Best Solution against Ground Truth
        gt_test_list = gt_entry['test_list']
        gt_test_code = create_ground_truth_test_code(gt_test_list)
        
        # For ground truth, we created a function 'check_solution', so we pass that as func_name?
        # No, execute_code appends "test_" + func_name.
        # We should adjust execute_code usage or wrap our GT test in "def test_func_name():"
        
        # Let's wrap GT test in the expected format
        gt_wrapper_code = f"def test_{func_name}():\n"
        for test in gt_test_list:
            gt_wrapper_code += f"    {test}\n"
            
        passed_gt, msg = execute_code(best_solution, gt_wrapper_code, func_name=func_name, timeout=2.0)
        
        is_correct = passed_gt
        if is_correct:
            passed_tasks += 1
            
        results.append({
            "task_id": task_id,
            "func_name": func_name,
            "selected_solution_score": best_score,
            "total_generated_tests": len(generated_tests),
            "passed_ground_truth": is_correct,
            "error_message": msg if not is_correct else None
        })
        
    # Calculate Accuracy
    accuracy = passed_tasks / total_tasks if total_tasks > 0 else 0.0
    print(f"\nResults:")
    print(f"Total Tasks: {total_tasks}")
    print(f"Passed Tasks: {passed_tasks}")
    print(f"Pass@1 Accuracy: {accuracy:.2%}")
    
    # Save results
    with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
    print(f"Detailed results saved to {RESULTS_PATH}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Simplified CodeT")
    parser.add_argument("--input_dir", type=str, default=os.path.join(BASE_DIR, "codet_output"), help="Path to CodeT input directory")
    
    args = parser.parse_args()
    
    SOLUTIONS_PATH = os.path.join(args.input_dir, "solutions.jsonl")
    TESTS_PATH = os.path.join(args.input_dir, "tests.jsonl")
    
    # Update results path based on input dir to avoid overwriting
    dir_name = os.path.basename(os.path.normpath(args.input_dir))
    RESULTS_PATH = os.path.join(BASE_DIR, f"simple_codet_results_{dir_name}.json")
    
    main()

