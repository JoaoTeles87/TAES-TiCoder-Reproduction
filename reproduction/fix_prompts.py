import json
import os

# Paths
TOY_DATA_PATH = "../datasets/mbpp/toy.jsonl"
CODET_OUTPUT_DIR = "codet_output"
SOLUTIONS_FILE = os.path.join(CODET_OUTPUT_DIR, "solutions.jsonl")
TESTS_FILE = os.path.join(CODET_OUTPUT_DIR, "tests.jsonl")

# Load original dataset to get the text field
with open(TOY_DATA_PATH, 'r') as f:
    dataset = [json.loads(line.strip()) for line in f if line.strip()]

# Create a mapping from task_id (numeric) to text
id_to_text = {}
for entry in dataset:
    # Create mapping for both numeric ID and function name
    task_id = entry.get("task_id")
    text = entry.get("text", "")
    id_to_text[task_id] = text
    
    # Also try to extract function name
    if "def " in entry.get("code", ""):
        try:
            code_lines = entry["code"].split("\n")
            for line in code_lines:
                if line.strip().startswith("def "):
                    func_name = line.strip().split("(")[0].replace("def ", "").strip()
                    id_to_text[func_name] = text
                    break
        except:
            pass

print(f"Loaded {len(dataset)} entries from dataset")
print(f"ID to text mappings: {id_to_text}")

# Fix solutions file
if os.path.exists(SOLUTIONS_FILE):
    with open(SOLUTIONS_FILE, 'r') as f:
        solutions = [json.loads(line.strip()) for line in f if line.strip()]
    
    fixed_solutions = []
    for sol in solutions:
        task_id = sol["task_id"]
        prompt = id_to_text.get(task_id, "")
        sol["prompt"] = prompt
        fixed_solutions.append(sol)
        print(f"Fixed solution for {task_id}: prompt = '{prompt[:50]}...'")
    
    with open(SOLUTIONS_FILE, 'w') as f:
        for sol in fixed_solutions:
            f.write(json.dumps(sol) + "\n")
    
    print(f"Fixed {len(fixed_solutions)} solutions")

# Fix tests file
if os.path.exists(TESTS_FILE):
    with open(TESTS_FILE, 'r') as f:
        tests = [json.loads(line.strip()) for line in f if line.strip()]
    
    fixed_tests = []
    for test in tests:
        task_id = test["task_id"]
        prompt = id_to_text.get(task_id, "")
        test["prompt"] = prompt
        fixed_tests.append(test)
        print(f"Fixed test for {task_id}: prompt = '{prompt[:50]}...'")
    
    with open(TESTS_FILE, 'w') as f:
        for test in fixed_tests:
            f.write(json.dumps(test) + "\n")
    
    print(f"Fixed {len(fixed_tests)} tests")

print("\nDone! Files have been fixed.")
