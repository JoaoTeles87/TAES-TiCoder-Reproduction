import os
import sys
import json
import datetime

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ticode/src')))

import models
import config as ticode_config
import query_chat_model

# Configuration
TOY_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../datasets/mbpp/sanitized-mbpp.json"))
TICODER_CACHE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "ticoder_cache.json"))
CODET_OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "codet_output"))
MODEL_NAME = "gpt-5-nano"
NUM_SAMPLES = 8

def generate_cache():
    """Generate cache with code and test completions for both CodeT and TiCoder"""
    print(f"--- Generating Cache (n={NUM_SAMPLES}) ---", flush=True)
    
    # Setup TiCoder config
    ticode_config.MODEL = MODEL_NAME
    ticode_config.MAX_TOKENS = 512
    ticode_config.MAX_NUM_CODEX_CODE_SUGGESTIONS = NUM_SAMPLES
    ticode_config.MAX_NUM_CODEX_TEST_SUGGESTIONS = NUM_SAMPLES
    ticode_config.sampling_temperature = 0.8
    
    # Load data
    import dataset_io as dio
    data_list = dio.read_json_or_jsonl_to_list(TOY_DATA_PATH)[:10]
    
    # Prepare caches
    ticoder_cache = {}
    if os.path.exists(TICODER_CACHE_FILE):
        with open(TICODER_CACHE_FILE, 'r') as f:
            ticoder_cache = json.load(f)
            
    codet_solutions = []
    codet_tests = []
    
    # Initialize model
    if MODEL_NAME == "gpt-5-nano":
        model = models.GPT5Nano()
    elif MODEL_NAME == "gpt-4o-mini":
        model = models.GPT4oMini()
    else:
        model = models.Model(MODEL_NAME)
    
    for i, data in enumerate(data_list):
        # Parse data using TiCoder's parser
        if "sanitized-mbpp" in TOY_DATA_PATH:
             prog_data = dio.parse_sanitized_mbpp_data(data)
        else:
             prog_data = dio.parse_mbpp_data(data)
        
        # Keep the original prompt text for CodeT
        original_prompt = data.get('text', data.get('prompt', ''))
             
        print(f"Processing task: {prog_data['func_name']}")
        
        # --- CODE GENERATION ---
        code_prompt_msgs = query_chat_model.get_prompt(prog_data)
        
        key_tuple = (
            code_prompt_msgs, 
            NUM_SAMPLES, 
            ticode_config.sampling_temperature, 
            False, # echo
            ticode_config.MAX_TOKENS, 
            MODEL_NAME, 
            NUM_SAMPLES
        )
        key_str = str(key_tuple)
        
        response_obj = None
        
        if key_str in ticoder_cache:
            print("Code Cache Hit!")
            resp_dict = ticoder_cache[key_str][1]
            response_obj = resp_dict
        else:
            try:
                print("Requesting Code from API...")
                # models.py returns list of choices
                choices = model.create_completion(
                    messages=code_prompt_msgs,
                    n=NUM_SAMPLES,
                    max_tokens=ticode_config.MAX_TOKENS
                )
                
                # Serialize choices for cache
                choices_serialized = []
                for c in choices:
                    if hasattr(c, 'to_dict'):
                        choices_serialized.append(c.to_dict())
                    elif hasattr(c, 'dict'):
                        choices_serialized.append(c.dict())
                    else:
                        choices_serialized.append(c)
                
                response_obj = {'choices': choices_serialized}
                
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ticoder_cache[key_str] = [key_tuple, response_obj, timestamp]
            except Exception as e:
                print(f"Error generating code for {prog_data['func_name']}: {e}")
                import traceback
                traceback.print_exc()

        if response_obj:
            codes = []
            choices = response_obj.get('choices', [])
            print(f"Got {len(choices)} code choices")
            for c in choices:
                # Handle both object and dict access
                if isinstance(c, dict):
                    content = c.get('message', {}).get('content', '')
                else:
                    content = c.message.content
                
                if "<code>" in content: content = content.split("<code>")[1]
                if "</code>" in content: content = content.split("</code>")[0]
                content = "import math\nimport re\nimport sys\nimport collections\nimport itertools\n" + content.strip()
                codes.append(content)
            
            codet_solutions.append({
                "task_id": data.get('task_id', prog_data['func_name']),
                "prompt": original_prompt,  # Include prompt for CodeT
                "samples": codes
            })
            print(f"Added {len(codes)} solutions for {prog_data['func_name']}")
        else:
            print(f"No response object for {prog_data['func_name']}")

        # --- TEST GENERATION ---
        test_prompt_msgs = query_chat_model.mk_test_suggestion_prompt(prog_data, f"{prog_data['sig']}\n\tpass")
        
        key_tuple = (
            test_prompt_msgs, 
            NUM_SAMPLES, 
            ticode_config.sampling_temperature, 
            False, 
            ticode_config.MAX_TOKENS, 
            MODEL_NAME, 
            NUM_SAMPLES
        )
        key_str = str(key_tuple)
        
        response_obj = None
        
        if key_str in ticoder_cache:
            print("Test Cache Hit!")
            response_obj = ticoder_cache[key_str][1]
        else:
            try:
                print("Requesting Tests from API...")
                choices = model.create_completion(
                    messages=test_prompt_msgs,
                    n=NUM_SAMPLES,
                    max_tokens=ticode_config.MAX_TOKENS
                )
                
                choices_serialized = []
                for c in choices:
                    if hasattr(c, 'to_dict'):
                        choices_serialized.append(c.to_dict())
                    elif hasattr(c, 'dict'):
                        choices_serialized.append(c.dict())
                    else:
                        choices_serialized.append(c)
                
                response_obj = {'choices': choices_serialized}
                
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ticoder_cache[key_str] = [key_tuple, response_obj, timestamp]
            except Exception as e:
                print(f"Error generating tests for {prog_data['func_name']}: {e}")
                import traceback
                traceback.print_exc()

        if response_obj:
            tests = []
            choices = response_obj.get('choices', [])
            print(f"Got {len(choices)} test choices")
            for c in choices:
                if isinstance(c, dict):
                    content = c.get('message', {}).get('content', '')
                else:
                    content = c.message.content
                    
                if "<code>" in content: content = content.split("<code>")[1]
                if "</code>" in content: content = content.split("</code>")[0]
                s = content.strip()
                if s.startswith("def ") and "assert " in s:
                     if not s.endswith("()"):
                         s += f"\n{prog_data['func_name']}()"
                tests.append(s)
                
            codet_tests.append({
                "task_id": data.get('task_id', prog_data['func_name']),
                "prompt": original_prompt,  # Include prompt for CodeT
                "samples": tests
            })
            print(f"Added {len(tests)} tests for {prog_data['func_name']}")
        else:
            print(f"No response object for tests of {prog_data['func_name']}")

    # Write Caches
    print(f"Saving TiCoder cache to {TICODER_CACHE_FILE}")
    with open(TICODER_CACHE_FILE, 'w') as f:
        json.dump(ticoder_cache, f)

    # Create output directory if needed
    os.makedirs(CODET_OUTPUT_DIR, exist_ok=True)

    print(f"Writing {len(codet_solutions)} solutions to {os.path.join(CODET_OUTPUT_DIR, 'solutions.jsonl')}")
    with open(os.path.join(CODET_OUTPUT_DIR, 'solutions.jsonl'), 'w') as f:
        for entry in codet_solutions:
            f.write(json.dumps(entry) + "\n")
            
    print(f"Writing {len(codet_tests)} tests to {os.path.join(CODET_OUTPUT_DIR, 'tests.jsonl')}")
    with open(os.path.join(CODET_OUTPUT_DIR, 'tests.jsonl'), 'w') as f:
        for entry in codet_tests:
            f.write(json.dumps(entry) + "\n")
            
    return os.path.join(CODET_OUTPUT_DIR, 'solutions.jsonl'), os.path.join(CODET_OUTPUT_DIR, 'tests.jsonl')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate cache for TiCoder/CodeT")
    parser.add_argument("--model", type=str, default="gpt-5-nano", choices=["gpt-5-nano", "gpt-4o-mini"], help="Model to use")
    parser.add_argument("--cache_file", type=str, default=TICODER_CACHE_FILE, help="Path to TiCoder cache file")
    parser.add_argument("--output_dir", type=str, default=CODET_OUTPUT_DIR, help="Path to CodeT output directory")
    
    args = parser.parse_args()
    
    MODEL_NAME = args.model
    TICODER_CACHE_FILE = os.path.abspath(args.cache_file)
    CODET_OUTPUT_DIR = os.path.abspath(args.output_dir)
    
    # Ensure output directory exists
    os.makedirs(CODET_OUTPUT_DIR, exist_ok=True)
    
    generate_cache()

    print("\n=== Cache Generation Complete ===")
