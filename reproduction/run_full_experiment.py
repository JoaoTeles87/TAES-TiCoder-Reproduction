#!/usr/bin/env python3
"""
Runs the full TiCoder experiment flow:
1. Generate Cache (Optional)
2. Run TiCoder (src/main.py)
3. Analyze Results (src/compute_metrics.py)
"""
import os
import sys
import subprocess
import argparse
from datetime import datetime

def run_command(cmd):
    print(f"Running: {cmd}")
    ret = subprocess.call(cmd, shell=True)
    if ret != 0:
        print(f"Error running command: {cmd}")
        sys.exit(ret)

def main():
    parser = argparse.ArgumentParser(description="Run Full TiCoder Experiment")
    parser.add_argument("--dataset", default="datasets/mbpp/mbpp.jsonl", help="Path to dataset")
    parser.add_argument("--limit", type=int, default=5, help="Number of examples to run")
    parser.add_argument("--cache_file", default="reproduction/mbpp_cache_experiment.json", help="Path to cache file")
    parser.add_argument("--skip_gen", action="store_true", help="Skip cache generation")
    parser.add_argument("--output_tag", default="experiment", help="Tag for output files")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="Model to use (default: gpt-3.5-turbo)")
    parser.add_argument("--tests", type=int, default=5, help="Number of tests to generate per problem")
    parser.add_argument("--ranking", default=None, help="Ranking strategy (e.g., code_t)")
    parser.add_argument("--max_tokens", type=int, default=150, help="Max tokens for generation (must match between cache and main)")
    
    args = parser.parse_args()
    
    # 1. Generate Cache
    if not args.skip_gen:
        print("=== Step 1: Generating Cache ===")
        cmd = f"{sys.executable} reproduction/generate_cache.py --dataset {args.dataset} --output {args.cache_file} --limit {args.limit} --model {args.model} --max_tokens {args.max_tokens}"
        run_command(cmd)
    else:
        print("=== Step 1: Skipping Cache Generation ===")

    # 2. Run TiCoder
    print("=== Step 2: Running TiCoder ===")
    # Note: src/main.py arguments might differ from what we expect. 
    # Based on README:
    # python3 main.py --data_file_path ... --codex_cache ... --query_oracle ...
    
    # We need to make sure we are using the cache we just generated.
    # And we want to simulate a user (query_oracle).
    
    ranking_arg = ["--rank_code_option", args.ranking] if args.ranking else []

    cmd_args = [
        sys.executable, "ticoder/src/main.py",
        "--data_file_path", args.dataset,
        "--codex_cache_file_path", args.cache_file,
        "--max_num_examples", str(args.limit),
        "--query_oracle",
        "--output_tag", args.output_tag,
        "--max_code_suggestions", "5",
        "--fix_num_tests", str(args.tests),
        "--verbosity", "1",
        "--model", args.model,
        "--max_tokens", str(args.max_tokens)
    ] + ranking_arg
    
    cmd = " ".join(cmd_args)
    run_command(cmd)
    
    # 3. Analyze Results
    print("=== Step 3: Analyzing Results ===")
    # The output file from main.py usually follows pattern: global_results.{tag}.json
    # We need to find it.
    results_file = f"results/global_results.{args.output_tag}.json"
    
    if not os.path.exists(results_file):
        print(f"Error: Results file {results_file} not found.")
        # Try to find any recent result file
        # But for now let's assume standard naming
        sys.exit(1)
        
    cmd = f"{sys.executable} ticoder/src/compute_metrics.py {results_file}"
    run_command(cmd)
    
    print("=== Experiment Completed Successfully ===")

if __name__ == "__main__":
    main()
