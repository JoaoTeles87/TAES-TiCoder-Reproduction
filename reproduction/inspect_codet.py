import pickle
import os

pkl_path = "reproduction/codet_output/dual_exec_result.pkl"
if os.path.exists(pkl_path):
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    print(f"Data type: {type(data)}")
    print(f"Data length: {len(data)}")
    if len(data) > 0:
        print(f"Sample entry 0: {data[0]}")
        
    # Calculate pass@1 if possible
    # CodeT logic: for each task, pick code that passes most generated tests.
    # Then check if that code passes reference tests (ground truth).
    # Ground truth results are in ground_truth_exec_result.pkl
    
    gt_path = "reproduction/codet_output/ground_truth_exec_result.pkl"
    if os.path.exists(gt_path):
        with open(gt_path, "rb") as f:
            gt_data = pickle.load(f)
        print(f"GT Data length: {len(gt_data)}")
        
        # Organize by solution
        # dual_exec_result seems to be a list of dicts, each representing an execution of a solution against generated tests?
        # Or maybe it's (solution, test_results)?
        
        # Let's assume data is a list of results for each solution.
        # We need to find the solution with highest pass rate on generated tests.
        
        # Group by solution
        sol_scores = {}
        for entry in data:
            sol = entry.get('solution')
            res = entry.get('result', [])
            # res might be a list of booleans or status codes
            # Let's assume it's a list of results corresponding to test_cases
            score = sum(1 for r in res if r == True or r == 'passed') # Adjust based on actual value
            sol_scores[sol] = score
            
        if not sol_scores:
            print("No solutions found in dual_exec_result")
        else:
            best_sol = max(sol_scores, key=sol_scores.get)
            print(f"Best solution score: {sol_scores[best_sol]}")
            
            # Check against ground truth
            # gt_data should contain results for solutions against real tests
            is_correct = False
            for entry in gt_data:
                if entry.get('solution') == best_sol:
                    # Check if it passed ground truth
                    # result in gt might be a single boolean or list
                    gt_res = entry.get('result')
                    if isinstance(gt_res, list):
                        is_correct = all(r == True or r == 'passed' for r in gt_res)
                    else:
                        is_correct = (gt_res == True or gt_res == 'passed')
                    break
            
            print(f"CodeT Selected Code Correct: {is_correct}")

        
else:
    print("No pickle found")
