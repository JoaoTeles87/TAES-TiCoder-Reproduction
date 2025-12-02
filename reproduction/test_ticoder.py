import os
import sys
import json
from unittest.mock import MagicMock
from openai import OpenAI

# Add paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ticode/src')))

import config as ticode_config
import query_chat_model
import main as ticode_main

# Configuration
TOY_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../datasets/mbpp/sanitized-mbpp.json"))
TICODER_CACHE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "ticoder_cache.json"))
TICODER_OUTPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "ticoder_output.txt"))
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

def run_ticoder_experiment():
    """Run TiCoder experiment with cached data"""
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
    data_list = dio.read_json_or_jsonl_to_list(TOY_DATA_PATH)[:10]
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
    import argparse
    parser = argparse.ArgumentParser(description="Run TiCoder experiment")
    parser.add_argument("--cache_file", type=str, default=TICODER_CACHE_FILE, help="Path to TiCoder cache file")
    
    args = parser.parse_args()
    
    TICODER_CACHE_FILE = os.path.abspath(args.cache_file)
    
    # Update output file name based on cache file to avoid overwriting
    base_name = os.path.basename(TICODER_CACHE_FILE)
    name_without_ext = os.path.splitext(base_name)[0]
    TICODER_OUTPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), f"{name_without_ext}_results.txt"))
    
    run_ticoder_experiment()

    print("\n=== TiCoder Execution Complete ===")
