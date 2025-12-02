import json
import os
import ast

DATA_DIR = r"d:\Projetos\TAES-TiCoder-Reproduction\codet\CodeT\data\generated_data"
TEST_CASE_FILE = os.path.join(DATA_DIR, "HumanEval_incoder6B_temp0.8_topp0.95_num100_max300_test_case.jsonl")
CODE_SOLUTION_FILE = os.path.join(DATA_DIR, "HumanEval_incoder6B_temp0.8_topp0.95_num100_max300_code_solution.jsonl")

def load_jsonl(filepath):
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def analyze_quality():
    print("Loading data...")
    test_cases = load_jsonl(TEST_CASE_FILE)
    code_solutions = load_jsonl(CODE_SOLUTION_FILE)
    
    total_problems = len(test_cases)
    print(f"Total Problems: {total_problems}")
    
    total_samples = 0
    valid_syntax_samples = 0
    truncated_samples = 0
    
    # We will check the first 10 samples for each problem to get a representative stat
    # checking all 100*164 = 16400 might be slow but acceptable. Let's do all.
    
    print("Analyzing syntax of test cases...")
    
    for i in range(total_problems):
        tc_entry = test_cases[i]
        prompt = tc_entry['prompt'] # "assert "
        
        for sample in tc_entry['samples']:
            total_samples += 1
            
            # Reconstruct full code line
            # The prompt ends with "assert ", so we append the sample.
            full_statement = prompt + sample
            
            try:
                ast.parse(full_statement)
                valid_syntax_samples += 1
            except SyntaxError:
                truncated_samples += 1
                
        if (i + 1) % 20 == 0:
            print(f"Processed {i + 1}/{total_problems} problems...")

    print("\n--- Analysis Results ---")
    print(f"Total Test Case Samples: {total_samples}")
    print(f"Valid Syntax: {valid_syntax_samples} ({valid_syntax_samples/total_samples*100:.2f}%)")
    print(f"Syntax Errors (likely truncated): {truncated_samples} ({truncated_samples/total_samples*100:.2f}%)")

if __name__ == "__main__":
    analyze_quality()
