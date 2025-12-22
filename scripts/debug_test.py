
import subprocess
import sys

def run_pytest():
    try:
        # Run pytest on the specific file and capture stdout/stderr
        result = subprocess.run(
            ["pytest", "feasibility_app/tests/test_usability.py", "-vv"],
            capture_output=True,
            text=True,
            shell=True 
        )
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
    except Exception as e:
        print(f"Error running pytest: {e}")

if __name__ == "__main__":
    run_pytest()
