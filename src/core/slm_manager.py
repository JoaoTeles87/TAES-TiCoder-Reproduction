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

def generate_discriminating_test(candidates_list: list) -> str:
    """
    Uses an SLM (Small Language Model) to generate a test case that discriminates
    between the provided candidate solutions.
    """
    if not candidates_list:
        return "0"

    if not client:
        print("Warning: OpenAI API key not found. Returning mock input.")
        return "0"

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

Your task is to generate a SINGLE test input (arguments only) that would likely produce DIFFERENT outputs for these candidates, helping to distinguish the correct one from the buggy ones.
The input should be valid for the function signature.
Return ONLY the input arguments as a string. Do not include function name.
Example: if function is `def add(a, b)`, return `1, 2`.
Example: if function is `def reverse(s)`, return `"hello"`.
"""

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.7
        )
        
        test_input = completion.choices[0].message.content.strip()
        # Clean up if the model adds quotes around the whole thing or code blocks
        test_input = test_input.replace("`", "").strip()
        return test_input
        
    except Exception as e:
        print(f"Error generating test input: {e}")
        return "0"

