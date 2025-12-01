from models import GPT5Nano
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../ticode/src')))
from data_parser import DataParser
import prompt

TOY_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../datasets/mbpp/toy.jsonl"))
data = DataParser.read_json_or_jsonl_to_list(TOY_DATA_PATH)
task = data[0]
if 'prompt' not in task and 'text' in task:
    task['prompt'] = task['text']
prog_data = DataParser.parse_sanitized_mbpp_data(task)

print("--- Testing Code Prompt ---")
code_prompt = prompt.code_prompt(prog_data)
model = GPT5Nano()
try:
    choices = model.create_completion(messages=code_prompt, n=1)
    print(f"Code Content: {choices[0].message.content}")
except Exception as e:
    print(f"Code Error: {e}")

print("\n--- Testing Test Prompt ---")
test_prompt = prompt.test_prompt(prog_data)
try:
    choices = model.create_completion(messages=test_prompt, n=1)
    print(f"Test Content: {choices[0].message.content}")
except Exception as e:
    print(f"Test Error: {e}")
