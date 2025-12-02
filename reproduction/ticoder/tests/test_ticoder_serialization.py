
import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add ticode/src to path (prepend to ensure it takes precedence over reproduction/)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ticode/src')))

import config
import main as ticode_main
import mock_utils

class TestTiCoderSerialization(unittest.TestCase):
    def setUp(self):
        self.cache_file = "reproduction/ticoder_cache.json"
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        
        # Reset config
        config.codex_cache_file = self.cache_file
        config.codex_query_response_log = {}
        config.mk_codex_query_cnt = 0
        config.skip_codex_query_cnt = 0

    def tearDown(self):
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

    def test_serialization_flow(self):
        print("\nStarting TiCoder serialization test...")

        # Create mock client
        mock_client = MagicMock()

        # Mock the API response
        mock_response = mock_utils.create_mock_openai_response("def solution():\n    return 'mocked'")
        mock_client.chat.completions.create.return_value = mock_response

        # Mock args
        class Args:
            data_file_path = "reproduction/mbpp.json" # Ensure this exists or mock reading it
            codex_cache_file_path = self.cache_file
            update_codex_cache_file = True
            model = "gpt-4"
            max_tokens = 100
            jobs = 1
            verbosity = 1
            # Add other required args with defaults
            sleep_time = 0
            output_tag = "test"
            function_name = ""
            max_num_examples = 1
            min_indx = 0
            max_indx = 0
            query_oracle = False
            sampling_temperature = 0.0
            max_code_suggestions = 1
            fix_num_tests = -1
            test_gen_option = "pass"
            rank_test_option = None
            rank_code_option = None
            use_validation_tests_in_prompt = False
            regen_code_with_tests_in_prompt = False
            use_dynamic_test_pruning = False
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
            test_output = "-"

        args = Args()
        
        # Mock dataset reading to avoid needing actual file
        with patch('dataset_io.read_json_or_jsonl_to_list') as mock_read:
            mock_read.return_value = [{
                "text": "Task description",
                "code": "def solution():\n    pass",
                "test_list": ["assert solution() == 'mocked'"],
                "task_id": 1
            }]
            
            # 1. Run first time - should call API and write to cache
            print("Running Pass 1 (API Call)...")
            # We need to patch parse_command_line_args to return our mock args
            with patch('main.parse_command_line_args', return_value=args):
                # We also need to patch sys.stdout to suppress output or capture it
                # But we want to see debug prints, so maybe not.
                
                # Run main logic (simulated)
                # We can't call main.main() directly easily because it parses args inside.
                # But we can call the logic inside main.
                
                # Setup config from args (mimic main.py)
                config.codex_cache_file = args.codex_cache_file_path
                config.MODEL = args.model
                config.MAX_TOKENS = args.max_tokens
                config.baseline_test_gen_codex = args.baseline_test_gen_codex
                config.split_asserts = args.split_asserts
                config.dynamic_test_pruning = args.use_dynamic_test_pruning
                config.optimistic_code_pruning = args.use_optimistic_code_pruning
                config.gen_regression_tests_from_code_suggestions = args.gen_regression_tests
                config.cluster_regression_tests = args.cluster_regression_tests
                config.use_rare_assert_rewrites = args.use_rare_assert_rewrites
                config.use_validation_tests_in_context = args.use_validation_tests_in_prompt
                config.regenerate_code_with_tests_in_prompt = args.regen_code_with_tests_in_prompt
                config.single_assert_per_test = args.single_assert_per_test
                config.multiple_asserts_choice = args.multiple_asserts_choice
                config.query_oracle_opt = args.query_oracle
                config.test_gen_option = args.test_gen_option
                config.rank_test_option = args.rank_test_option
                config.rank_code_option = args.rank_code_option
                config.max_user_queries = args.max_user_queries
                config.count_accepted_queries_only = args.count_accepted_queries_only
                config.use_oracle_as_code_suggestion = args.oracle_as_code_suggestion
                config.sampling_temperature = args.sampling_temperature
                config.MAX_NUM_CODEX_CODE_SUGGESTIONS = args.max_code_suggestions
                config.token_per_minute_limit = args.token_per_minute_limit
                config.user_fixes_tests = args.user_fixes_tests
                config.dataset_prefix = "mbpp" # Default for test

                # Manually trigger processing
                # We need to initialize qm and client in main
                import query_chat_model
                ticode_main.qm = query_chat_model
                ticode_main.client = mock_client
                ticode_main.update_codex_cache_file = True
                
                # Process one sample
                ticode_main.args = args
                ticode_main.data_list = mock_read.return_value
                ticode_main.process_data_sample((0, mock_read.return_value[0]))

        # Verify cache file exists
        self.assertTrue(os.path.exists(self.cache_file), "Cache file was not created")
        
        # Verify cache content
        with open(self.cache_file, 'r') as f:
            cache_data = json.load(f)
            print(f"Cache keys: {list(cache_data.keys())}")
            self.assertTrue(len(cache_data) > 0, "Cache is empty")
            # Check if value is a list/tuple as expected (k, v, time)
            first_val = list(cache_data.values())[0]
            self.assertTrue(isinstance(first_val, list), "Cache value should be a list/tuple")
            self.assertTrue(isinstance(first_val[1], dict), "Response in cache should be a dict")

        # 2. Run second time - should read from cache
        print("Running Pass 2 (Cache Read)...")
        
        # Reset mock to ensure it's not called
        mock_client.chat.completions.create.reset_mock()
        
        # Load cache into config (mimic main.py loading)
        with open(self.cache_file, 'r') as f:
            config.codex_query_response_log = json.load(f)
            
        with patch('dataset_io.read_json_or_jsonl_to_list') as mock_read:
            mock_read.return_value = [{
                "text": "Task description",
                "code": "def solution():\n    pass",
                "test_list": ["assert solution() == 'mocked'"],
                "task_id": 1
            }]
            
            ticode_main.args = args
            ticode_main.data_list = mock_read.return_value
            ticode_main.process_data_sample((0, mock_read.return_value[0]))
            
        # Verify API was NOT called
        mock_client.chat.completions.create.assert_not_called()
        print("Success: API was not called in Pass 2")

if __name__ == '__main__':
    unittest.main()
