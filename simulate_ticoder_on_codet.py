import json
import os
import sys
import threading
import time
import textwrap

# Add ticode to sys.path to allow importing src (if needed later)
TICODE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ticode")
sys.path.append(TICODE_DIR)

DATA_DIR = r"d:\Projetos\TAES-TiCoder-Reproduction\codet\CodeT\data\generated_data"
# TEST_CASE_FILE = os.path.join(DATA_DIR, "HumanEval_incoder6B_temp0.8_topp0.95_num100_max300_test_case.jsonl")
# CODE_SOLUTION_FILE = os.path.join(DATA_DIR, "HumanEval_incoder6B_temp0.8_topp0.95_num100_max300_code_solution.jsonl")
TEST_CASE_FILE = os.path.join(DATA_DIR, "HumanEval_davinci002_temp0.8_topp0.95_num100_max300_test_case.jsonl")
CODE_SOLUTION_FILE = os.path.join(DATA_DIR, "HumanEval_davinci002_temp0.8_topp0.95_num100_max300_code_solution.jsonl")
HUMAN_EVAL_FILE = r"d:\Projetos\TAES-TiCoder-Reproduction\datasets\human-eval\HumanEval.jsonl"


def read_problems(eval_file=HUMAN_EVAL_FILE):
    problems = {}
    with open(eval_file, "r") as f:
        for line in f:
            task = json.loads(line)
            problems[task["task_id"]] = task
    return problems

def load_jsonl(filepath):
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def map_to_humaneval(codet_prompt, problems):
    codet_prompt_stripped = codet_prompt.strip()
    for task_id, problem in problems.items():
        he_prompt = problem['prompt'].strip()
        if codet_prompt_stripped == he_prompt:
            return task_id
        if codet_prompt_stripped.startswith(he_prompt) or he_prompt.startswith(codet_prompt_stripped):
             return task_id
    return None

def run_test(candidate_code, test_code, result_container):
    try:
        # Debug print for the very first execution
        if not hasattr(run_test, "debug_printed"):
            print("\n--- DEBUG: Test Case Inspection ---")
            print(f"Type of test_code: {type(test_code)}")
            print(f"Repr of test_code: {repr(test_code)}")
            print(f"Repr of candidate_code (first 100 chars): {repr(candidate_code[:100])}")
            print(f"Repr of test_code (last 50 chars): {repr(test_code[-50:])}")
            print("--- END DEBUG ---\n")
            run_test.debug_printed = True
            
        # Combine candidate and test
        # Use dedent to handle multi-line indentation correctly
        full_code = candidate_code + "\n" + textwrap.dedent(test_code)
        
        exec_globals = {}
        exec(full_code, exec_globals)
        result_container['success'] = True
    except Exception as e:
        result_container['success'] = False
        result_container['error'] = str(e)



def check_correctness_custom(candidate_code, test_code, timeout=1.0):
    result = {'success': False, 'error': 'Timeout'}
    t = threading.Thread(target=run_test, args=(candidate_code, test_code, result))
    t.start()
    t.join(timeout)
    if t.is_alive():
        return False, "Timeout"
    return result['success'], result.get('error')

import ast

def is_valid_syntax(code_str):
    try:
        ast.parse(code_str)
        return True
    except SyntaxError:
        return False

def simulate():
    print("Loading HumanEval problems...")
    problems = read_problems()
    print(f"Loaded {len(problems)} HumanEval problems.")
    
    print("Loading CodeT data...")
    test_cases_data = load_jsonl(TEST_CASE_FILE)
    code_solutions_data = load_jsonl(CODE_SOLUTION_FILE)
    
    limit = 5 # Run on first 5 problems
    print(f"Running simulation on first {limit} problems...")
    
    for i in range(limit):
        tc_entry = test_cases_data[i]
        cs_entry = code_solutions_data[i]
        
        task_id = map_to_humaneval(cs_entry['prompt'], problems)
        if not task_id:
            print(f"Could not map index {i} to HumanEval task. Skipping.")
            continue
            
        print(f"\nProcessing {task_id} (Index {i})")
        
        candidates = cs_entry['samples']
        generated_tests = tc_entry['samples']
        
        print(f"  Candidates: {len(candidates)}")
        print(f"  Generated Tests: {len(generated_tests)}")
        
        # Filter valid tests
        tc_prompt = tc_entry['prompt']
        valid_tests = []
        for t in generated_tests:
            if is_valid_syntax(tc_prompt + t):
                valid_tests.append(t)
        
        # print(f"  Valid Tests: {len(valid_tests)}/{len(generated_tests)}")
        
        if not valid_tests:
            print("  No valid tests found. Skipping.")
            continue

        # Optimization: Use subset of candidates for all metrics to be fast
        eval_candidates = candidates[:20]
        eval_tests = valid_tests[:20]
        
        print(f"  Evaluating first {len(eval_candidates)} candidates...")

        # 1. Evaluate candidates against Ground Truth (HumanEval)
        he_problem = problems[task_id]
        entry_point = he_problem['entry_point']
        canonical_tests = he_problem['test']
        
        def check_canonical(code):
            full_code = code + "\n" + canonical_tests + f"\ncheck({entry_point})"
            result = {'success': False}
            t = threading.Thread(target=run_test, args=("", full_code, result))
            t.start()
            t.join(0.5) # Reduced timeout
            return result['success']

        candidate_ground_truth = []
        for cand in eval_candidates:
            full_cand = cs_entry['prompt'] + cand
            is_correct = check_canonical(full_cand)
            candidate_ground_truth.append(is_correct)
            
        num_correct = sum(candidate_ground_truth)
        baseline_acc = num_correct / len(eval_candidates) if eval_candidates else 0
        oracle_acc = 1.0 if num_correct > 0 else 0.0
        
        print(f"  Baseline (Pass@1 of generator): {baseline_acc:.2%}")
        print(f"  Oracle (Perfect Ranking): {oracle_acc:.2%}")

        # 2. Run TiCoder Ranking
        print("  Running TiCoder Ranking...")
        candidate_scores = [0] * len(eval_candidates)
        candidate_signatures = [] # For CodeT Consensus
        
        for c_idx, cand in enumerate(eval_candidates):
            full_cand = cs_entry['prompt'] + cand
            signature = []
            for t in eval_tests:
                full_test = tc_prompt + t
                success, _ = check_correctness_custom(full_cand, full_test, timeout=0.5)
                if success:
                    candidate_scores[c_idx] += 1
                    signature.append(1)
                else:
                    signature.append(0)
            candidate_signatures.append(tuple(signature))
        
        # TiCoder Ranking
        ranked_indices_ticoder = sorted(range(len(eval_candidates)), key=lambda k: candidate_scores[k], reverse=True)
        top_1_idx_ticoder = ranked_indices_ticoder[0]
        top_1_is_correct_ticoder = candidate_ground_truth[top_1_idx_ticoder]
        
        print(f"  TiCoder Top-1 Correct: {top_1_is_correct_ticoder}")

        # 3. Run CodeT Ranking (Consensus)
        print("  Running CodeT Ranking (Consensus)...")
        # Group by signature
        clusters = {}
        for idx, sig in enumerate(candidate_signatures):
            if sig not in clusters:
                clusters[sig] = []
            clusters[sig].append(idx)
            
        # Sort clusters by size (descending)
        sorted_clusters = sorted(clusters.items(), key=lambda item: len(item[1]), reverse=True)
        
        # Pick largest cluster
        # CodeT picks *any* candidate from the largest cluster. Let's pick the first one.
        best_cluster_sig, best_cluster_indices = sorted_clusters[0]
        top_1_idx_codet = best_cluster_indices[0]
        top_1_is_correct_codet = candidate_ground_truth[top_1_idx_codet]
        
        print(f"  CodeT Top-1 Correct: {top_1_is_correct_codet} (Cluster Size: {len(best_cluster_indices)})")
        
        metrics.append({
            "task_id": task_id,
            "baseline_acc": baseline_acc,
            "oracle_acc": oracle_acc,
            "ticoder_success": top_1_is_correct_ticoder,
            "codet_success": top_1_is_correct_codet
        })

    print("\n=== EXPERIMENT SUMMARY ===")
    print(f"Problems Analyzed: {len(metrics)}")
    if not metrics:
        return

    avg_baseline = sum(m['baseline_acc'] for m in metrics) / len(metrics)
    avg_oracle = sum(m['oracle_acc'] for m in metrics) / len(metrics)
    avg_ticoder = sum(1 for m in metrics if m['ticoder_success']) / len(metrics)
    avg_codet = sum(1 for m in metrics if m['codet_success']) / len(metrics)
    
    print(f"Average Baseline Accuracy: {avg_baseline:.2%}")
    print(f"Average Oracle Accuracy:   {avg_oracle:.2%}")
    print(f"Average TiCoder Accuracy:  {avg_ticoder:.2%}")
    print(f"Average CodeT Accuracy:    {avg_codet:.2%}")
    print("==========================")

metrics = []




if __name__ == "__main__":
    simulate()

