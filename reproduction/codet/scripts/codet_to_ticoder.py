import json
import os
import sys
import pickle
import ast
from datetime import datetime

# Add ticode to sys.path
# Current file: reproduction/codet/scripts/codet_to_ticoder.py
# Root: ../../../
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TICODE_DIR = os.path.join(PROJECT_ROOT, "ticode")
sys.path.append(TICODE_DIR)

# Set dummy API key to bypass config check
os.environ["OPENAI_API_KEY"] = "dummy"

import src.config as config


DATA_DIR = os.path.join(PROJECT_ROOT, "codet", "CodeT", "data", "generated_data")
TEST_CASE_FILE = os.path.join(DATA_DIR, "HumanEval_incoder6B_temp0.8_topp0.95_num100_max300_test_case.jsonl")
CODE_SOLUTION_FILE = os.path.join(DATA_DIR, "HumanEval_incoder6B_temp0.8_topp0.95_num100_max300_code_solution.jsonl")
OUTPUT_CACHE_DIR = os.path.join(PROJECT_ROOT, "reproduction", "codet", "cache")
OUTPUT_CACHE_FILE = os.path.join(OUTPUT_CACHE_DIR, "codet_cache.pkl")

def load_jsonl(filepath):
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def is_valid_syntax(code_str):
    try:
        ast.parse(code_str)
        return True
    except SyntaxError:
        return False

def create_fake_response(samples):
    choices = []
    for sample in samples:
        choices.append({
            "message": {
                "content": sample,
                "role": "assistant"
            },
            "finish_reason": "stop",
            "index": 0
        })
    
    return {
        "id": "chatcmpl-fake-codet",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": "codet-model",
        "choices": choices,
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }

def convert():
    print("Loading CodeT data...")
    if not os.path.exists(TEST_CASE_FILE):
        print(f"Error: Test case file not found at {TEST_CASE_FILE}")
        return

    test_cases = load_jsonl(TEST_CASE_FILE)
    code_solutions = load_jsonl(CODE_SOLUTION_FILE)
    
    if not os.path.exists(OUTPUT_CACHE_DIR):
        os.makedirs(OUTPUT_CACHE_DIR)
        
    cache = {}
    
    print(f"Converting {len(test_cases)} entries...")
    
    for i in range(len(test_cases)):
        tc_entry = test_cases[i]
        cs_entry = code_solutions[i]
        
        cs_prompt = cs_entry['prompt']
        cs_samples = cs_entry['samples']
        
        cs_response = create_fake_response(cs_samples)
        cs_key = f"CODE_{cs_prompt}"
        cache[cs_key] = (cs_key, cs_response, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # 2. Convert Test Cases
        # Filter invalid syntax
        tc_prompt = tc_entry['prompt']
        tc_samples = tc_entry['samples']
        valid_tests = [t for t in tc_samples if is_valid_syntax(tc_prompt + t)]
        
        if valid_tests:
            tc_response = create_fake_response(valid_tests)
            tc_key = f"TEST_{tc_prompt}" 
            cache[tc_key] = (tc_key, tc_response, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
    print(f"Saving cache with {len(cache)} entries to {OUTPUT_CACHE_FILE}...")
    with open(OUTPUT_CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)
    print("Done.")

if __name__ == "__main__":
    convert()
