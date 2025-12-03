#!/usr/bin/env python3
"""
Converts CodeT-style JSONL files (prompt + samples) into TiCoder cache format.
Usage: python codet_to_ticoder.py <input_codet.jsonl> <output_cache.json>
"""
import sys
import json
import os
from pathlib import Path

# Add current directory to path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache_parser import CacheParser

def convert_codet_to_ticoder(input_file: str, output_file: str):
    parser = CacheParser()
    
    print(f"Reading CodeT file: {input_file}")
    count = 0
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
                
            try:
                record = json.loads(line)
                prompt = record.get("prompt", "")
                samples = record.get("samples", [])
                
                if not samples:
                    continue
                    
                # Reconstruct "choices" format expected by CacheParser
                # CodeT samples are just strings. TiCoder expects OpenAI-like choice objects.
                choices = []
                for i, sample in enumerate(samples):
                    choices.append({
                        "index": i,
                        "message": {
                            "role": "assistant",
                            "content": sample
                        },
                        "finish_reason": "stop"
                    })
                
                # Add to parser
                # We use dummy values for metadata since CodeT doesn't provide them
                parser.add_response(
                    choices=choices,
                    prompt=prompt,
                    model="codet-converted",
                    temperature=0.8, # Assumption
                    max_tokens=len(samples[0]) if samples else 0
                )
                count += 1
                
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line")
                continue
                
    print(f"Converted {count} records.")
    parser.to_json(output_file)
    print(f"Saved TiCoder cache to: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python codet_to_ticoder.py <input_codet.jsonl> <output_cache.json>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    convert_codet_to_ticoder(input_path, output_path)
