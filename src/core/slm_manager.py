import random
import ast
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI Client
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


def generate_discriminating_test(candidates_list: list, n: int = 5) -> list:
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
You are a software testing expert.
Here are {len(candidates_list)} Python function implementations for the same problem.
Some might be correct, some might be buggy.
{candidates_text}
Your task is to generate {n} DISTINCT test inputs (arguments only) that would likely produce DIFFERENT outputs for these candidates, helping to distinguish the correct one from the buggy ones.

IMPORTANT:
- Return the inputs as a JSON list of strings.
- If the input is a STRING, it must be QUOTED inside the JSON string.
  - Example for integer input: "1, 2"
  - Example for string input: "'hello'" (Note the single quotes inside)
  - Example for list input: "[1, 2, 3]"

Return ONLY the JSON list.
"""

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.7
        )
        
        content = completion.choices[0].message.content.strip()
        # Clean potential markdown
        content = content.replace("```json", "").replace("```", "").strip()
        
        import json
        try:
            test_inputs = json.loads(content)
            if isinstance(test_inputs, list):
                return [str(x) for x in test_inputs]
            else:
                return [str(content)]
        except json.JSONDecodeError:
            # Fallback if model didn't return valid JSON
            print(f"Warning: SLM returned invalid JSON: {content}")
            return [content]
        
    except Exception as e:
        print(f"Error generating test input: {e}")
        return ["0"]
