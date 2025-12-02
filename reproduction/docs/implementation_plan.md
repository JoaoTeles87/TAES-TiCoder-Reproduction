# Implementation Plan - Simplified CodeT

The goal is to create a simplified version of CodeT (`simple_codet.py`) that runs on the generated cache (`solutions.jsonl` and `tests.jsonl`) to evaluate the performance of the CodeT approach (generating tests to verify code) on the MBPP dataset.

## Proposed Changes

### [NEW] `reproduction/simple_codet.py`
This script will:
1.  **Load Data**:
    -   Read `reproduction/codet_output/solutions.jsonl` (generated code samples).
    -   Read `reproduction/codet_output/tests.jsonl` (generated test cases).
    -   Read `datasets/mbpp/sanitized-mbpp.json` (ground truth/oracle).
2.  **Execution Loop**:
    -   Iterate through each task (problem).
    -   For each task, execute every generated code sample against every generated test case using `reproduction/execution.py`.
    -   Matrix: `num_samples` (code) x `num_samples` (tests).
3.  **Scoring & Selection**:
    -   Count how many generated tests pass for each code sample.
    -   Select the code sample with the highest number of passing tests.
    -   Tie-breaking: First one found or random (will use first one for stability).
4.  **Evaluation**:
    -   Test the *selected* code sample against the *ground truth* tests (from `sanitized-mbpp.json`).
    -   Calculate Pass@1 accuracy.
5.  **Reporting**:
    -   Print results to console.
    -   Save detailed results to `reproduction/simple_codet_results.json`.

## Verification Plan

### Automated Tests
-   **Run the script**: `conda run -n ticode python reproduction/simple_codet.py`
-   **Check Output**: Verify that it processes the 10 tasks and outputs a Pass@1 score.
-   **Check Artifacts**: Verify `reproduction/simple_codet_results.json` is created and contains reasonable data.
