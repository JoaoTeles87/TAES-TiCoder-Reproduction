from typing import List, Dict, Any
from utils.execution import run_code
from collections import Counter

def rank_tests_by_simple_distinguishing_power(tests: List[str], candidates: List[str]) -> List[tuple]:
    """
    Ranks tests based on their ability to distinguish between candidates.
    Adapted from 'Simple Distinguishing' strategy for Output-Based TiCoder.
    
    Returns a list of (test_input, score) sorted by score descending.
    """
    test_scores = []
    
    for test_input in tests:
        outputs = []
        for code in candidates:
            output = run_code(code, test_input)
            outputs.append(output)
            
        # Group outputs to find consensus vs dissidents
        # We treat the most common output as "Pass" (consensus) and others as "Fail" (dissidents)
        # This is a heuristic for unsupervised ranking.
        counts = Counter(outputs)
        
        if len(counts) <= 1:
            # All candidates agree -> No distinguishing power
            score = 0.0
        else:
            # Calculate score based on split balance
            # Ideally we want a 50/50 split for max information gain (binary search style)
            # Formula: min(group_A, group_B) / max(group_A, group_B)
            
            # Strategy: Partition into "Largest Group" vs "Rest"
            most_common_count = counts.most_common(1)[0][1]
            total = len(candidates)
            rest_count = total - most_common_count
            
            # Avoid division by zero if somehow rest is 0 (should be covered by len(counts) <= 1)
            if rest_count == 0:
                score = 0.0
            else:
                score = min(most_common_count, rest_count) / max(most_common_count, rest_count)
                
        test_scores.append((test_input, score))
        
    # Sort by score descending
    test_scores.sort(key=lambda x: x[1], reverse=True)
    return test_scores
