import os
import sys

# Add necessary paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ticode/src')))

from run_experiment import setup_directories, generate_common_data, run_codet_execution

if __name__ == "__main__":
    print("=== Testing CodeT Execution ===")
    
    # 1. Setup directories
    setup_directories()
    
    # 2. Generate common data (codes and tests)
    print("\nGenerating common data...")
    sol_file, test_file = generate_common_data()
    
    print(f"\nSolutions file: {sol_file}")
    print(f"Tests file: {test_file}")
    
    # 3. Run CodeT execution
    print("\n" + "="*50)
    run_codet_execution(sol_file, test_file)
    print("="*50)
    
    print("\n=== Test Complete ===")
