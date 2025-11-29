from utils.execution import run_code

class Oracle:
    """
    The Oracle uses the canonical solution to determine the expected output for a given input.
    """
    def __init__(self, canonical_solution: str):
        """
        Args:
            canonical_solution: The correct Python code for the problem.
        """
        self.canonical_solution = canonical_solution

    def evaluate(self, test_input: str) -> str:
        """
        Executes the canonical solution with the given test_input.

        Args:
            test_input: The input arguments for the function (as a string).

        Returns:
            The string representation of the result, or 'UNDEFINED' if execution fails.
        """
        return run_code(self.canonical_solution, test_input)
