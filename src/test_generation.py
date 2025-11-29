import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Check if API key is set
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not found in .env file.")
    print("Please add your API key to the .env file.")
    exit(1)

client = OpenAI(api_key=api_key)

prompt = "import re\n"\
"def text_lowercase_underscore(text):\n"\
"\"\"\" Write a function that returns True if the input string contains only lowercase letters joined with an underscore, and False otherwise. \"\"\"\n"

print(f"Prompt sent to model:\n{prompt}")
print("-" * 20)

try:
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo", # Changed from gpt-5.1 to a valid model for testing. Change to gpt-4o if needed.
        messages=[
            {"role": "user", "content": prompt}, # Changed role to user for standard generation
        ]
    )
    print("Response:")
    print(completion.choices[0].message.content)
except Exception as e:
    print(f"An error occurred: {e}")
