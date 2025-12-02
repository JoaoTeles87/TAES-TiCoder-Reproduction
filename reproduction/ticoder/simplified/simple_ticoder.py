import json
import os
import sys
from collections import Counter
from tqdm import tqdm

# Add shared utils directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'utils'))
from execution import execute_code

# Configuration
BASE_DIR = os.path.dirname(__file__)
CACHE_DIR = os.path.join(BASE_DIR, "..", "cache")
RESULTS_DIR = os.path.join(BASE_DIR, "..", "results")
CACHE_PATH = os.path.join(CACHE_DIR, "ticoder_cache.json")
GROUND_TRUTH_PATH = os.path.join(BASE_DIR, "..", "..", "..", "datasets", "mbpp", "sanitized-mbpp.json")
RESULTS_PATH = os.path.join(RESULTS_DIR, "simple_ticoder_results.json")

def load_cache(path):
    """Load TiCoder cache file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_ground_truth(path):
    """Load ground truth dataset."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Convert list to dict keyed by task_id
    return {item['task_id']: item for item in data}

def extract_code_from_response(content):
    """Extract code from <code></code> tags."""
    if '<code>' in content and '</code>' in content:
        start = content.find('<code>') + len('<code>')
        end = content.find('</code>')
        return content[start:end].strip()
    return content.strip()

def parse_cache_for_task(cache, task_data):
    """
    Parse cache to extract code and test suggestions for a specific task.
    
    The cache is structured as:
    {
        str(query_tuple): [query_tuple, response_dict, timestamp],
        ...
    }
    
    where query_tuple contains (messages, n, temperature, echo, max_tokens, model, n)
    and response_dict contains choices with generated code/tests.
    """
    func_name = None
    code_snippet = task_data['code']
    for line in code_snippet.split('\n'):
        if line.strip().startswith('def '):
            func_name = line.strip().split(' ')[1].split('(')[0]
            break
    
    if not func_name:
        return None, None, func_name
    
    code_suggestions = []
    test_suggestions = []
    
    # Iterate through cache entries
    for key_str, entry in cache.items():
        if not isinstance(entry, list) or len(entry) < 2:
            continue
        
        query_tuple, response_dict = entry[0], entry[1]
        
        # Check if this query is for our function
        if not isinstance(query_tuple, list) or len(query_tuple) == 0:
            continue
        
        messages = query_tuple[0]
        if not isinstance(messages, list):
            continue
        
        # Check if any message mentions our function
        is_relevant = False
        is_test_gen = False
        
        for msg in messages:
            if not isinstance(msg, dict):
                continue
            content = msg.get('content', '')
            if func_name in content:
                is_relevant = True
                if 'test' in content.lower() and 'generate' in content.lower():
                    is_test_gen = True
                break
        
        if not is_relevant:
            continue
        
        # Extract choices from response
        choices = response_dict.get('choices', [])
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            
            message = choice.get('message', {})
            content = message.get('content', '')
            
            if not content:
                continue
            
            code = extract_code_from_response(content)
            
            if is_test_gen:
                test_suggestions.append(code)
            else:
                code_suggestions.append(code)
    
    return code_suggestions, test_suggestions, func_name

def clean_test_code(test_code, func_name):
    """Clean generated test code to remove problematic lines."""
    lines = test_code.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Remove lines that are just the function name call
        if stripped == f"{func_name}()":
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def prune_codes_with_tests(code_suggestions, test_suggestions, func_name):
    """
    Prune code suggestions using generated tests (TiCoder approach).
    
    For each test, we check which codes pass it.
    We keep codes that pass the most tests (consensus-based ranking).
    """
    if not test_suggestions:
        # No tests to prune with, return all codes
        return code_suggestions
    
    # Score each code by how many tests it passes
    code_scores = []
    
    for code in code_suggestions:
        pass_count = 0
        for test in test_suggestions:
            cleaned_test = clean_test_code(test, func_name)
            passed, _ = execute_code(code, cleaned_test, func_name=func_name, timeout=1.0)
            if passed:
                pass_count += 1
        code_scores.append((pass_count, code))
    
    # Sort by pass count (descending)
    code_scores.sort(key=lambda x: x[0], reverse=True)
    
    # Return codes that pass at least one test, or all if none pass any
    pruned_codes = [code for score, code in code_scores if score > 0]
    
    if not pruned_codes:
        # If no code passes any test, return all (fallback)
        return code_suggestions
    
    return pruned_codes

def main():
    print("Loading data...")
    cache = load_cache(CACHE_PATH)
    ground_truth_data = load_ground_truth(GROUND_TRUTH_PATH)
    
    results = []
    total_tasks = 0
    passed_tasks = 0
    
    # Process first 10 tasks (matching the experiment setup)
    task_ids = sorted(list(ground_truth_data.keys()))[:10]
    
    print(f"Processing {len(task_ids)} tasks...")
    
    for task_id in tqdm(task_ids):
        total_tasks += 1
        
        gt_entry = ground_truth_data[task_id]
        
        # Parse cache for this task
        code_suggestions, test_suggestions, func_name = parse_cache_for_task(cache, gt_entry)
        
        if not func_name:
            print(f"Could not find function name for task {task_id}, skipping.")
            continue
        
        if not code_suggestions:
            print(f"No code suggestions found for task {task_id}, skipping.")
            results.append({
                "task_id": task_id,
                "func_name": func_name,
                "num_code_suggestions": 0,
                "num_test_suggestions": 0,
                "num_pruned_codes": 0,
                "passed_ground_truth": False,
                "error_message": "No code suggestions found in cache"
            })
            continue
        
        # Apply TiCoder's test-based pruning
        pruned_codes = prune_codes_with_tests(code_suggestions, test_suggestions, func_name)
        
        # Select best code (first one after pruning, as they're sorted by consensus)
        best_solution = pruned_codes[0] if pruned_codes else code_suggestions[0]
        
        # Evaluate against ground truth
        gt_test_list = gt_entry['test_list']
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
            "num_code_suggestions": len(code_suggestions),
            "num_test_suggestions": len(test_suggestions),
            "num_pruned_codes": len(pruned_codes),
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
    parser = argparse.ArgumentParser(description="Run Simplified TiCoder")
    parser.add_argument("--cache_file", type=str, default=CACHE_PATH, help="Path to TiCoder cache file")
    
    args = parser.parse_args()
    
    CACHE_PATH = os.path.abspath(args.cache_file)
    
    # Update results path based on cache file to avoid overwriting
    cache_name = os.path.basename(CACHE_PATH)
    name_without_ext = os.path.splitext(cache_name)[0]
    RESULTS_PATH = os.path.join(RESULTS_DIR, f"simple_ticoder_results_{name_without_ext}.json")
    
    main()
