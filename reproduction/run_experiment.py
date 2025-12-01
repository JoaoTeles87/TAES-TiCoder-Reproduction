import os
import sys
import json
import subprocess
from unittest.mock import MagicMock
import time
import datetime
import re

# Add paths
# Insert ticode/src at the beginning to ensure TiCoder imports its own modules (like execution.py)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ticode/src')))

import models
from data_parser import DataParser
import config as ticode_config
import query_chat_model
import main as ticode_main
from openai import OpenAI

# Configuration
TOY_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../datasets/mbpp/toy.jsonl"))
TICODER_CACHE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "ticoder_cache.json"))
TICODER_OUTPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "ticoder_output.txt"))
CODET_OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "codet_output"))
MODEL_NAME = "gpt-5-nano"
NUM_SAMPLES = 8

# Wrapper to handle gpt-5-nano quirks for TiCoder
class SafeClient:
    def __init__(self, real_client):
        self.chat = SafeChat(real_client.chat)

class SafeChat:
    def __init__(self, real_chat):
        self.completions = SafeCompletions(real_chat.completions)

class SafeCompletions:
    def __init__(self, real_completions):
        self.create = self._create_wrapper(real_completions.create)
        self.real_create = real_completions.create

    def _create_wrapper(self, create_func):
        def wrapper(**kwargs):
            if kwargs.get('model') == 'gpt-5-nano':
                kwargs.pop('temperature', None)
                if 'max_tokens' in kwargs:
                    kwargs['max_completion_tokens'] = kwargs.pop('max_tokens')
                
                # Ensure reasoning_effort is set if needed, or just let it be if the model handles it.
                kwargs['reasoning_effort'] = "low"
                
            return create_func(**kwargs)
        return wrapper

def setup_directories():
    os.makedirs(CODET_OUTPUT_DIR, exist_ok=True)
    # Do not delete caches, we want to reuse them!

def generate_common_data():
    print(f"--- Generating Common Data (n={NUM_SAMPLES}) ---", flush=True)
    
    # Setup TiCoder config to get prompts and cache keys
    ticode_config.MODEL = MODEL_NAME
    ticode_config.MAX_TOKENS = 512 # Match args.max_tokens
    ticode_config.MAX_NUM_CODEX_CODE_SUGGESTIONS = NUM_SAMPLES
    ticode_config.MAX_NUM_CODEX_TEST_SUGGESTIONS = NUM_SAMPLES
    ticode_config.sampling_temperature = 0.8
    
    # Load data
    import dataset_io as dio
    data_list = dio.read_json_or_jsonl_to_list(TOY_DATA_PATH)
    
    # Prepare caches
    ticoder_cache = {}
    if os.path.exists(TICODER_CACHE_FILE):
        with open(TICODER_CACHE_FILE, 'r') as f:
            ticoder_cache = json.load(f)
            
    codet_solutions = []
    codet_tests = []
    
    model = models.GPT5Nano()
    
    for i, data in enumerate(data_list):
        # Parse data using TiCoder's parser
        if "sanitized-mbpp" in TOY_DATA_PATH:
             prog_data = dio.parse_sanitized_mbpp_data(data)
        else:
             prog_data = dio.parse_mbpp_data(data)
             
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
                codes.append(content.strip())
            
            codet_solutions.append({
                "task_id": prog_data['func_name'],
                "prompt": "", 
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
                "task_id": prog_data['func_name'],
                "prompt": "",
                "samples": tests
            })
            print(f"Added {len(tests)} tests for {prog_data['func_name']}")
        else:
            print(f"No response object for tests of {prog_data['func_name']}")

    # Write Caches
    print(f"Saving TiCoder cache to {TICODER_CACHE_FILE}")
    with open(TICODER_CACHE_FILE, 'w') as f:
        json.dump(ticoder_cache, f)

    print(f"Writing {len(codet_solutions)} solutions to {os.path.join(CODET_OUTPUT_DIR, 'solutions.jsonl')}")
    with open(os.path.join(CODET_OUTPUT_DIR, 'solutions.jsonl'), 'w') as f:
        for entry in codet_solutions:
            f.write(json.dumps(entry) + "\n")
            
    print(f"Writing {len(codet_tests)} tests to {os.path.join(CODET_OUTPUT_DIR, 'tests.jsonl')}")
    with open(os.path.join(CODET_OUTPUT_DIR, 'tests.jsonl'), 'w') as f:
        for entry in codet_tests:
            f.write(json.dumps(entry) + "\n")
            
    return os.path.join(CODET_OUTPUT_DIR, 'solutions.jsonl'), os.path.join(CODET_OUTPUT_DIR, 'tests.jsonl')

def run_codet_execution(sol_file, test_file):
    print("--- Running CodeT Execution ---")
    # Prepare MBPP JSONL for CodeT
    mbpp_jsonl_file = os.path.join(CODET_OUTPUT_DIR, "mbpp.jsonl")
    with open(TOY_DATA_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open(mbpp_jsonl_file, 'w', encoding='utf-8') as f:
        for line in lines:
            entry = json.loads(line)
            if 'prompt' not in entry and 'text' in entry:
                entry['prompt'] = entry['text']
            if 'entry_point' not in entry:
                try:
                    func_name, _, _ = DataParser.get_func_details(entry)
                    entry['entry_point'] = func_name
                except:
                    pass
            if 'test_list' in entry:
                entry['test'] = entry.pop('test_list')
            f.write(json.dumps(entry) + "\n")

    codet_main = os.path.abspath(os.path.join(os.path.dirname(__file__), "../codet/CodeT/main.py"))
    cmd = (
        f"\"{sys.executable}\" {codet_main} "
        f"--source_path_for_solution {mbpp_jsonl_file} "
        f"--predict_path_for_solution {sol_file} "
        f"--source_path_for_test {mbpp_jsonl_file} "
        f"--predict_path_for_test {test_file} "
        f"--cache_dir {CODET_OUTPUT_DIR} "
        f"--test_case_limit 1 "
        f"--timeout 2.0"
    )
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("CodeT execution finished.")
        # Parse output for accuracy
        for line in result.stdout.splitlines():
            if "pass@1" in line.lower() or "accuracy" in line.lower():
                print(f"CodeT Result: {line.strip()}")
        # Also check output file
        print("STDOUT snippet:", result.stdout[-500:])
        print("STDERR snippet:", result.stderr[-500:])
    except subprocess.CalledProcessError as e:
        print("CodeT execution FAILED")
        print(e.stdout)
        print(e.stderr)

def run_ticoder_experiment():
    print(f"--- Running TiCoder Experiment (n={NUM_SAMPLES}, oracle=True) ---", flush=True)
    
    # Setup args
    class Args:
        data_file_path = TOY_DATA_PATH
        codex_cache_file_path = TICODER_CACHE_FILE
        update_codex_cache_file = True
        model = MODEL_NAME
        max_tokens = 512
        jobs = 1
        verbosity = 1
        sleep_time = 0
        output_tag = "experiment"
        function_name = ""
        max_num_examples = 1000
        min_indx = 0
        max_indx = 1000
        query_oracle = True # ORACLE ON
        sampling_temperature = 0.8 # Will be stripped
        max_code_suggestions = NUM_SAMPLES
        fix_num_tests = NUM_SAMPLES
        test_gen_option = "pass"
        rank_test_option = None
        rank_code_option = None
        use_validation_tests_in_prompt = False
        regen_code_with_tests_in_prompt = False
        use_dynamic_test_pruning = True
        use_rare_assert_rewrites = -1
        use_optimistic_code_pruning = False
        single_assert_per_test = True
        split_asserts = False
        multiple_asserts_choice = "top1"
        baseline_test_gen_codex = False
        user_fixes_tests = False
        max_user_queries = 1
        count_accepted_queries_only = False
        oracle_as_code_suggestion = False
        gen_regression_tests = False
        cluster_regression_tests = False
        get_pruned_stats_in_global = False
        pass_at_one = False
        use_azure = False
        azure_config = ""
        token_per_minute_limit = 10000
        test_output = TICODER_OUTPUT_FILE

    args = Args()
    
    # Patch config.count_tokens to handle gpt-5-nano
    original_count_tokens = ticode_config.count_tokens
    def safe_count_tokens(messages, model="gpt-4-0613"):
        if model == "gpt-5-nano":
            model = "gpt-4-0613"
        return original_count_tokens(messages, model)
    ticode_config.count_tokens = safe_count_tokens
    
    # Patch Client
    real_client = OpenAI()
    safe_client = SafeClient(real_client)
    
    # Setup TiCoder globals
    ticode_main.args = args
    ticode_main.qm = query_chat_model
    ticode_main.client = safe_client # Inject safe client
    ticode_main.update_codex_cache_file = True
    
    # Config setup
    ticode_config.codex_cache_file = TICODER_CACHE_FILE
    ticode_config.MODEL = MODEL_NAME
    ticode_config.MAX_TOKENS = args.max_tokens
    ticode_config.dynamic_test_pruning = True
    ticode_config.query_oracle_opt = True
    ticode_config.codex_query_response_log = {}
    
    # Missing configs
    ticode_config.baseline_test_gen_codex = False
    ticode_config.split_asserts = False
    ticode_config.optimistic_code_pruning = False
    ticode_config.gen_regression_tests_from_code_suggestions = False
    ticode_config.cluster_regression_tests = False
    ticode_config.use_rare_assert_rewrites = -1
    ticode_config.use_validation_tests_in_context = False
    ticode_config.regenerate_code_with_tests_in_prompt = False
    ticode_config.single_assert_per_test = True
    ticode_config.multiple_asserts_choice = "top1"
    ticode_config.user_fixes_tests = False
    ticode_config.dataset_prefix = "mbpp"
    
    # Fix: Set max suggestions to NUM_SAMPLES to avoid requesting more than supported (e.g. 10 vs 8)
    ticode_config.MAX_NUM_CODEX_CODE_SUGGESTIONS = NUM_SAMPLES
    ticode_config.MAX_NUM_CODEX_TEST_SUGGESTIONS = NUM_SAMPLES
    
    # Load data
    import dataset_io as dio
    data_list = dio.read_json_or_jsonl_to_list(TOY_DATA_PATH)
    ticode_main.data_list = data_list
    
    # Patch execution for Windows (disable timeout)
    import execution as ticode_execution
    class DummyTimeout:
        def __init__(self, seconds=1, error_message='Timeout'):
            pass
        def __enter__(self):
            pass
        def __exit__(self, type, value, traceback):
            pass
    ticode_execution.timeout = DummyTimeout
    ticode_execution.signal = MagicMock()
    ticode_execution.signal.SIGALRM = 14
    ticode_execution.signal.signal = MagicMock()
    ticode_execution.signal.alarm = MagicMock()

    # Run
    results = []
    for i, data in enumerate(data_list):
        print(f"Processing task {i}...", flush=True)
        try:
            res = ticode_main.process_data_sample((i, data))
            results.append(res)
        except Exception as e:
            print(f"Error processing task {i}: {e}", flush=True)
            import traceback
            traceback.print_exc()

    # Save TiCoder results
    with open("reproduction/ticoder_results.json", "w") as f:
        json.dump(results, f, indent=4, default=str)
        
    # Report Results
    print("\n--- TiCoder Results ---", flush=True)
    for res in results:
        if not res: continue
        final_count = res['num_code_suggestions']
        print(f"Task: {res['func_name']}")
        print(f"Final Codes: {final_count}")
        
        if final_count > 0 and res['results']:
            local_res = res['results'][0]
            is_correct = local_res['status'][0]
            print(f"Selected Code Correct: {is_correct}")
        else:
            print("Selected Code Correct: False (No codes left)")

if __name__ == "__main__":
    setup_directories()
    
    # 1. Generate Common Data (One Request per type, Save to Both Caches)
    sol, test = generate_common_data()
    
    # 2. Run CodeT Execution
    run_codet_execution(sol, test)
    
    # 3. Run TiCoder Experiment (Will use the cache populated in step 1)
    run_ticoder_experiment()