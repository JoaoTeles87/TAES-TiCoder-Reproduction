import json
import os
from core.oracle import Oracle
from core.slm_manager import generate_discriminating_test
from utils.execution import run_code

DATA_FILE = "data/candidates_cache.json"

def main():
    print("Starting TiCoder-SLM Main Loop...")
    
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found. Please run src/generate_candidates.py first.")
        return

    with open(DATA_FILE, 'r') as f:
        data = json.load(f)

    total_problems = len(data)
    print(f"Loaded {total_problems} problems.")

    total_candidates_processed = 0
    total_candidates_kept = 0

    for task_id, problem_data in data.items():
        print(f"\nProcessing {task_id}...")
        
        candidates = problem_data['candidates']
        canonical_solution = problem_data['canonical']

        # INJECTION: Add Canonical Solution to Candidates for Validation (Strategy A)
        # This ensures that at least one candidate is correct. If this gets pruned, our logic is wrong.
        candidates.append(canonical_solution)
        
        initial_count = len(candidates)
        total_candidates_processed += initial_count
        
        # 1. Ask SLM for discriminating tests (Generate 5)
        # In a real loop, we might do this iteratively. Here we do one pass as per instructions.
        from core.ranking import rank_tests_by_simple_distinguishing_power
        
        generated_tests = generate_discriminating_test(candidates, n=5)
        print(f"  SLM Generated {len(generated_tests)} Tests: {generated_tests}")
        
        # 2. Rank Tests and Select Best
        ranked_tests = rank_tests_by_simple_distinguishing_power(generated_tests, candidates)
        best_test_input, score = ranked_tests[0]
        print(f"  Ranking Results: {ranked_tests}")
        print(f"  Selected Best Test: {best_test_input} (Score: {score:.2f})")
        
        test_input = best_test_input
        
        # 3. Get Ground Truth from Oracle
        oracle = Oracle(canonical_solution)
        expected_output = oracle.evaluate(test_input)
        print(f"  Oracle Expected Output: {expected_output}")
        
        if expected_output == "UNDEFINED":
            print("  Warning: Oracle returned UNDEFINED. Skipping pruning for this test.")
            # If we skip pruning, we technically "keep" all candidates for this round.
            total_candidates_kept += initial_count
            continue

        # 3. Run Test on Candidates and Prune
        remaining_candidates = []
        for i, code in enumerate(candidates):
            actual_output = run_code(code, test_input)
            
            # [Validação 2] Lógica de Comparação
            # A comparação deve ser estrita. Se o candidato der erro (UNDEFINED) numa entrada válida,
            # ele DEVE ser podado, pois a solução correta (Oráculo) não deu erro.
            if actual_output == expected_output:
                remaining_candidates.append(code)
            else:
                # Log para debug (essencial para saber se a lógica está certa)
                # Only print detailed logs if it's the canonical solution being pruned (Critical Error)
                # or if we want verbose output. Let's print for all for now as per request.
                is_canonical = (code == canonical_solution)
                status = "[CRITICAL ERROR] Canonical Pruned!" if is_canonical else "Pruned"
                print(f"    Candidate {i} {status}. Expected: {expected_output} | Got: {actual_output}")
                
                if "UNDEFINED" in actual_output:
                    print(f"    --> Code Snippet (First 200 chars):\n{code[:200]}...")
                    print(f"    --> Full Error: {actual_output}")
                
        final_count = len(remaining_candidates)
        total_candidates_kept += final_count
        
        print(f"  Iniciou com {initial_count}, restaram {final_count} candidatos.")
        
        # Validation Check: Did we prune the canonical solution?
        if canonical_solution not in remaining_candidates:
             print("  [FAILURE] Canonical solution was pruned! Check execution environment or comparison logic.")
        else:
             print("  [SUCCESS] Canonical solution survived.")

        # Update the list for next iteration (if we were looping)
        # problem_data['candidates'] = remaining_candidates

    print("\n" + "="*40)
    print("       TICODER-SLM EXECUTION SUMMARY       ")
    print("="*40)
    print(f"Total Problems Processed: {total_problems}")
    print(f"Total Candidates (Initial): {total_candidates_processed}")
    print(f"Total Candidates (Kept):    {total_candidates_kept}")
    
    reduction_rate = 0
    if total_candidates_processed > 0:
        reduction_rate = ((total_candidates_processed - total_candidates_kept) / total_candidates_processed) * 100
        
    print(f"Reduction Rate:             {reduction_rate:.2f}%")
    print("="*40)
    print("\nMain Loop Completed.")

if __name__ == "__main__":
    main()
