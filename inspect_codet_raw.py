import json
import os

DATA_DIR = r"d:\Projetos\TAES-TiCoder-Reproduction\codet\CodeT\data\generated_data"
TEST_CASE_FILE = os.path.join(DATA_DIR, "HumanEval_incoder6B_temp0.8_topp0.95_num100_max300_test_case.jsonl")
CODE_SOLUTION_FILE = os.path.join(DATA_DIR, "HumanEval_incoder6B_temp0.8_topp0.95_num100_max300_code_solution.jsonl")

def inspect_raw():
    print("Reading first line of test case file...")
    with open(TEST_CASE_FILE, 'r', encoding='utf-8') as f:
        tc_line = f.readline()
        tc_data = json.loads(tc_line)
        
    print("Reading first line of code solution file...")
    with open(CODE_SOLUTION_FILE, 'r', encoding='utf-8') as f:
        cs_line = f.readline()
        cs_data = json.loads(cs_line)
        
    print("\n--- RAW DATA INSPECTION ---")
    print(f"TC Prompt (repr): {repr(tc_data['prompt'])}")
    print(f"CS Prompt (repr): {repr(cs_data['prompt'])}")
    
    print(f"\nTC Sample [0] (repr): {repr(tc_data['samples'][0])}")
    print(f"CS Sample [0] (repr): {repr(cs_data['samples'][0])}")
    
    print("\n--- END INSPECTION ---")

if __name__ == "__main__":
    inspect_raw()
