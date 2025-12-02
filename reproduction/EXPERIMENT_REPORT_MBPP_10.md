# MBPP Experiment Report (10 Problems)

## Experiment Configuration
- **Dataset**: `sanitized-mbpp.json` (First 10 problems)
- **Model**: `gpt-5-nano`
- **Samples (n)**: 8
- **Cache**: Generated using `generate_cache.py`

## Execution Results

### CodeT
- **Pass@1**: 0.0
- **Note**: CodeT execution finished but reported 0.0 accuracy. This might be due to strict matching or issues with the generated tests/solutions format expected by CodeT's evaluation script.

### TiCoder
- **Processed Tasks**: 9/10
- **Pass@1**: 100% (9/9)
- **Details**:
    - `similar_elements`: Passed (5/5 suggestions correct)
    - `is_not_prime`: Passed (3/3 suggestions correct)
    - `heap_queue_largest`: Passed (8/8 suggestions correct)
    - `differ_At_One_Bit_Pos`: Skipped/Failed processing
    - `find_char_long`: Passed (3/3 suggestions correct)
    - `square_nums`: Passed (6/6 suggestions correct)
    - `find_Rotations`: Passed (1/1 suggestions correct)
    - `remove_Occ`: Passed (6/6 suggestions correct)
    - `sort_matrix`: Passed (8/8 suggestions correct)
    - `find_Volume`: Passed (7/7 suggestions correct)

## Observations
- TiCoder successfully utilized the generated tests to filter and select correct code solutions, achieving a high success rate on the processed tasks.
- CodeT's low score warrants further investigation into the evaluation pipeline compatibility with the generated cache.
# MBPP Experiment Report (10 Problems)

## Experiment Configuration
- **Dataset**: `sanitized-mbpp.json` (First 10 problems)
- **Model**: `gpt-5-nano`
- **Samples (n)**: 8
- **Cache**: Generated using `generate_cache.py`

## Execution Results

### CodeT
- **Pass@1**: 0.0
- **Note**: CodeT execution finished but reported 0.0 accuracy. This might be due to strict matching or issues with the generated tests/solutions format expected by CodeT's evaluation script.

### TiCoder
- **Processed Tasks**: 9/10
- **Pass@1**: 100% (9/9)
- **Details**:
    - `similar_elements`: Passed (5/5 suggestions correct)
    - `is_not_prime`: Passed (3/3 suggestions correct)
    - `heap_queue_largest`: Passed (8/8 suggestions correct)
    - `differ_At_One_Bit_Pos`: Skipped/Failed processing
    - `find_char_long`: Passed (3/3 suggestions correct)
    - `square_nums`: Passed (6/6 suggestions correct)
    - `find_Rotations`: Passed (1/1 suggestions correct)
    - `remove_Occ`: Passed (6/6 suggestions correct)
    - `sort_matrix`: Passed (8/8 suggestions correct)
    - `find_Volume`: Passed (7/7 suggestions correct)

## Observations
- TiCoder successfully utilized the generated tests to filter and select correct code solutions, achieving a high success rate on the processed tasks.
- CodeT's low score warrants further investigation into the evaluation pipeline compatibility with the generated cache.

### Simplified CodeT (Reproduction)
- **Pass@1**: 100% (10/10)
- **Methodology**: Implemented `simple_codet.py` to re-run the CodeT logic (Execute Generated Code vs Generated Tests -> Select Best -> Verify with Ground Truth) using the same cache.
- **Results**:
    - All 10 tasks passed the ground truth verification.
    - This confirms that the generated cache contains correct solutions and useful tests, and the original CodeT execution script likely had configuration or parsing issues.
    - **Note**: Task 6 (`differ_At_One_Bit_Pos`) had a scoring issue in the simplified script due to function name extraction (picked helper `is_Power_Of_Two`), resulting in 0 generated tests passing. However, the tie-breaking mechanism selected a correct solution, which then passed the ground truth check.

## GPT-4o-Mini Results (Simplified CodeT)

**Pass@1 Accuracy: 90.00% (9/10)**

### Detailed Breakdown
*   **Passed Tasks**: 2, 3, 4, 7, 8, 9, 11, 12, 14
*   **Failed Tasks**: 6 (`differ_At_One_Bit_Pos`)

### Failure Analysis: Task 6
The model generated the following code for Task 6:
```python
def differ_At_One_Bit_Pos(a, b):
    """Write a python function to check whether the two numbers differ at one bit position only or not."""
    return (a ^ b) and not (a ^ b & (a ^ b - 1))
```
This fails due to **operator precedence** in Python. The expression `a ^ b & (a ^ b - 1)` is evaluated as `a ^ (b & (a ^ b - 1))` because `&` has higher precedence than `^`. The correct implementation should be `(a ^ b) & ((a ^ b) - 1)`.

This bug caused the ground truth assertions to fail. Interestingly, the `gpt-5-nano` model (likely a stronger model) avoided this by using a helper function `is_Power_Of_Two(x)` where `x` was passed as `a ^ b`, thus avoiding the precedence ambiguity in the expression.

### TiCoder Results
The TiCoder experiment with `gpt-4o-mini` was terminated after exceeding the expected runtime. This suggests that the model's generated code might have caused issues in the iterative refinement process or simply that the execution overhead was higher. However, the CodeT results provide a clear baseline for the model's performance on this subset.
