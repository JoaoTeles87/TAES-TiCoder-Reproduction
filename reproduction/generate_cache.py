#!/usr/bin/env python3
"""
Generates candidates for a dataset using OpenAI API and saves to TiCoder cache.
Usage: python generate_cache.py --dataset <path> --output <path> --limit <n>
"""
import sys
import os
import argparse
# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

# Add current directory and src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'ticoder', 'src')
sys.path.insert(0, current_dir)
sys.path.insert(0, src_dir)

from openai import OpenAI
from cache_parser import CacheParser
from data_parser import DataParser
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

def generate_and_cache(dataset_path: str, output_path: str, limit: int = None, model: str = "gpt-3.5-turbo", max_tokens: int = 150):
    if not client:
        print("Error: OPENAI_API_KEY not found in environment.")
        return

    parser = CacheParser(output_path)
    
    # Load dataset
    print(f"Loading dataset from {dataset_path}...")
    # We use preload_random_samples to get raw lines/samples
    # If limit is None, it loads all.
    samples, indices = DataParser.preload_random_samples(dataset_path, n=limit if limit else 999999)
    
    print(f"Generating candidates for {len(samples)} problems using {model} (max_tokens={max_tokens})...")
    
    for i, sample in enumerate(samples):
        # Parse to get prompt
        # Assuming MBPP format for now, but DataParser handles it if it's standard
        prog_data = DataParser.parse_mbpp_data(sample)
        # ProgramData doesn't have 'prompt', it has 'sig' which includes the docstring/prompt
        prompt_text = prog_data.sig
        
        print(f"[{i+1}/{len(samples)}] Generating for {prog_data.func_name}...")
        
        try:
            # Call OpenAI
            # We want 5 candidates
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a Python coding assistant. Complete the function provided. Return only the code completion."},
                    {"role": "user", "content": prompt_text}
                ],
                n=5,
                temperature=0.8,
                max_tokens=max_tokens # Use the limit for generation too
            )
            
            # Add to cache
            # CacheParser expects the full choice object list
            # We need to convert the Pydantic objects to dicts or let CacheParser handle it
            # CacheParser._normalize_response handles objects if they have attributes
            
            parser.add_response(
                choices=completion.choices,
                prompt=prompt_text,
                model=model,
                temperature=0.8,
                max_tokens=max_tokens # Use the fixed limit for the key, NOT actual usage
            )
            
        except Exception as e:
            print(f"Error generating for {prog_data.func_name}: {e}")
            continue
            
    # Save final cache
    parser.to_json(output_path)
    print(f"Done. Cache saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate TiCoder Cache")
    parser.add_argument("--dataset", required=True, help="Path to dataset JSONL")
    parser.add_argument("--output", required=True, help="Path to output JSON cache")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of problems")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="OpenAI model to use")
    parser.add_argument("--max_tokens", type=int, default=150, help="Max tokens for generation and cache key")
    
    args = parser.parse_args()
    
    generate_and_cache(args.dataset, args.output, args.limit, args.model, args.max_tokens)
