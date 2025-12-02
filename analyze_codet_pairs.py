import json
import os

DATA_DIR = r"d:\Projetos\TAES-TiCoder-Reproduction\codet\CodeT\data\generated_data"
TEST_CASE_FILE = os.path.join(DATA_DIR, "HumanEval_incoder6B_temp0.8_topp0.95_num100_max300_test_case.jsonl")
CODE_SOLUTION_FILE = os.path.join(DATA_DIR, "HumanEval_incoder6B_temp0.8_topp0.95_num100_max300_code_solution.jsonl")

def load_jsonl(filepath):
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"Error decoding line {i+1} in {filepath}: {e}")
    return data

def analyze_pairs():
    print(f"Loading test cases from {TEST_CASE_FILE}...")
    test_cases = load_jsonl(TEST_CASE_FILE)
    if not test_cases:
        print("No test cases loaded.")
        return

    print(f"Loading code solutions from {CODE_SOLUTION_FILE}...")
    code_solutions = load_jsonl(CODE_SOLUTION_FILE)
    if not code_solutions:
        print("No code solutions loaded.")
        return

    print(f"Loaded {len(test_cases)} test cases and {len(code_solutions)} code solutions.")

    if len(test_cases) != len(code_solutions):
        print("WARNING: File lengths differ!")

    match_count = 0
    min_len = min(len(test_cases), len(code_solutions))
    
    for i in range(min_len):
        tc_prompt = test_cases[i].get('prompt', '')
        cs_prompt = code_solutions[i].get('prompt', '')
        
        # Check if test case prompt starts with code solution prompt
        # We might need to be careful about whitespace, so let's strip trailing whitespace from CS prompt
        if tc_prompt.startswith(cs_prompt.rstrip()):
            match_count += 1
        else:
            # Debug the first mismatch
            if match_count == i: # This is the first mismatch
                print(f"\nMismatch at index {i}:")
                print(f"TC Prompt start: {repr(tc_prompt[:50])}...")
                print(f"CS Prompt:       {repr(cs_prompt[:50])}...")
    
    print(f"\nNumber of pairs where TC prompt starts with CS prompt: {match_count}/{min_len}")
    
    if match_count == min_len:
        print("SUCCESS: All items are index-aligned and prompts match via 'startswith'.")
    else:
        print("FAILURE: Not all items are aligned.")




if __name__ == "__main__":
    analyze_pairs()
