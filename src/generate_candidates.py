import os
import json
import gzip
import urllib.request
import random
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

DATA_DIR = "data"
HUMAN_EVAL_URL = "https://github.com/openai/human-eval/raw/master/data/HumanEval.jsonl.gz"
HUMAN_EVAL_PATH = os.path.join(DATA_DIR, "HumanEval.jsonl.gz")
OUTPUT_PATH = os.path.join(DATA_DIR, "candidates_cache.json")

# Initialize OpenAI Client
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

def download_human_eval():
    if not os.path.exists(HUMAN_EVAL_PATH):
        print(f"Downloading HumanEval dataset to {HUMAN_EVAL_PATH}...")
        urllib.request.urlretrieve(HUMAN_EVAL_URL, HUMAN_EVAL_PATH)
        print("Download complete.")
    else:
        print("HumanEval dataset already exists.")

def load_human_eval(limit=20):
    problems = []
    with gzip.open(HUMAN_EVAL_PATH, 'rb') as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            problems.append(json.loads(line))
    return problems

def generate_candidates(prompt_code, n=5):
    """
    Generates n candidates using OpenAI API.
    """
    if not client:
        print("Warning: OpenAI API key not found. Returning empty candidates.")
        return []

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo", # Using 3.5 for cost/speed in this reproduction
            messages=[
                {"role": "system", "content": "You are a Python coding assistant. Complete the function provided. Return only the code completion, no markdown, no explanations."},
                {"role": "user", "content": prompt_code},
            ],
            n=n,
            temperature=0.8 # Some variance
        )
        
        candidates = []
        for choice in completion.choices:
            # The model usually returns the body. We need to append it to the prompt to make it full code.
            # However, sometimes it might repeat the signature.
            # For simplicity in this reproduction, we assume it continues the code.
            generated_body = choice.message.content
            
            # Clean up markdown code blocks if present
            generated_body = generated_body.replace("```python", "").replace("```", "")
            
            full_code = prompt_code + "\n" + generated_body
            candidates.append(full_code)
            
        return candidates
    except Exception as e:
        print(f"Error generating candidates: {e}")
        return []

def main():
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    download_human_eval()
    
    problems = load_human_eval(limit=5) # Reduced limit for testing to save tokens/time
    print(f"Loaded {len(problems)} problems.")
    
    output_data = {}
    
    for i, problem in enumerate(problems):
        task_id = problem['task_id']
        print(f"Generating candidates for {task_id} ({i+1}/{len(problems)})...")
        
        prompt = problem['prompt']
        canonical_sol = prompt + problem['canonical_solution']
        
        candidates = generate_candidates(prompt, n=5)
        
        if not candidates:
            print(f"Skipping {task_id} due to generation failure.")
            continue

        output_data[task_id] = {
            'task_id': task_id,
            'candidates': candidates,
            'canonical': canonical_sol
        }
        
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    print(f"Generated candidates for {len(output_data)} problems. Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

