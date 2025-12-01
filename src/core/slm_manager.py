import random
import ast
import os
import re
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize Model Client
BASE_URL = os.getenv("SLM_BASE_URL")
API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")
MODEL_NAME = os.getenv("SLM_MODEL")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY) if API_KEY else None


# In-Context Learning
ICL_EXAMPLES = """
Example 1:
Problem: Return the maximum of two numbers.
Candidate A: return a if a > b else b
Candidate B: return a if a < b else b
Reasoning: 
- Candidate A calculates maximum. 
- Candidate B calculates minimum (buggy).
- If input is [10, 5]: Candidate A -> 10. Candidate B -> 5.
- Results are different (10 != 5). Valid test.
Test Inputs: [10, 5]

Example 2:
Problem: Check if a list is empty.
Candidate A: return len(lst) == 0
Candidate B: return lst is None
Reasoning: 
- Candidate A checks length (correct).
- Candidate B checks if object is None.
- If input is [[]]: Candidate A -> True. Candidate B -> False.
- Results are different. Valid test.
Test Inputs: [[]]

Example 3:
Problem: Sum elements of a list.
Candidate A: return sum(lst)
Candidate B: return sum(lst) + 1
Reasoning:
- Candidate B has an off-by-one error.
- If input is [[1, 2]]: Candidate A -> 3. Candidate B -> 4.
- Results are different. Valid test.
Test Inputs: [[1, 2]]

Example 4:
Problem: Remove vowels from string.
Candidate A: return "".join([c for c in s if c not in 'aeiou'])
Candidate B: return s.replace('a', '').replace('e', '')
Reasoning:
- Candidate B only removes 'a' and 'e', misses 'i', 'o', 'u'.
- If input is ["union"]: Candidate A -> "nn". Candidate B -> "union" (fails to remove 'u', 'i', 'o').
- Results are different.
Test Inputs: ["union"]
"""

def parse_slm_output(content: str) -> list:
    clean_content = content.replace("```json", "").replace("```", "").strip()
    match = re.search(r"(\[.*\])", content, re.DOTALL)

    if match:
        try:
            found_list = json.loads(match.group(1))
            return [str(x) for x in found_list]
        except:
            pass

    # Fallback
    return [clean_content]

def generate_discriminating_test(
    problem_docstring: str, candidates_list: list, n: int = 5
) -> list:
    """
    Uses an SLM (Small Language Model) to generate a test case that discriminates
    between the provided candidate solutions.
    """
    if not candidates_list:
        return ["0"]

    if not client:
        print("Warning: OpenAI API key not found. Returning mock inputs.")
        return ["0", "1", "-1"]

    # Construct prompt
    # We want the model to see the candidates and generate an input.
    # To save tokens, we might not send all candidates if they are long.
    # But for HumanEval they are short.
    
    candidates_text = ""
    for i, code in enumerate(candidates_list[:5]): # Limit to 5 candidates
        candidates_text += f"--- Candidate {i+1} ---\n{code}\n\n"

    prompt = f"""
[Role]
You are an expert software tester.

[Examples]
{ICL_EXAMPLES}

[Current Task]
Problem Description:
{problem_docstring}

Candidates to Compare:
{candidates_text}

[Instruction]
Analyze the logic differences between the candidates.
Generate a JSON list containing EXACTLY {n} DISTINCT test input arguments.
The inputs must vary (e.g., negative numbers, edge cases, large numbers, empty structures) to maximize the chance of distinguishing the codes.

IMPORTANT FORMAT Rules:
- Return ONLY a raw JSON list of strings.
- If the function takes multiple arguments (e.g., a, b), the string should contain them separated by commas: "1, 2"
- If the argument is a list, brackets must be inside the string: "[1, 2, 3]"

Output format: ["arg_case_1", "arg_case_2", ..., "arg_case_n"]
"""

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that outputs JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        
        raw_content = completion.choices[0].message.content.strip()
        
        return parse_slm_output(raw_content)
        
    except Exception as e:
        print(f"Error generating test input: {e}")
        return ["0"]
