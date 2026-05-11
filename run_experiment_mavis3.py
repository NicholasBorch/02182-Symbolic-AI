import subprocess
from typing import Dict
import json


def run_goalrecognition(level: str, timeout: int = 180, max_memory: str = "48g") -> tuple[str, str]:
    cmd = [
        "java", "-jar", "server.jar",
        "-s", "300",
        "-t", str(timeout),
        "-c", f"python3 client.py --max-memory {max_memory} goalrecognition",
        "-l", f"levels/{level}",
    ]
    print(cmd)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)
    except subprocess.TimeoutExpired:
        print(f"Timeout expired for level {level} (goalrecognition)")
        return "Timeout", "Timeout expired"
    return result.stdout, result.stderr


exercise2_levels = [
    "MAaroundthecircle.lvl",
    "MAhelperCustom.lvl",
    "MAsimplegoalrecognition.lvl",
    "goal_plan.lvl",
    "goal_rec2.lvl",
    "plan_recognition.lvl",
    "moving_completed_boxes.lvl",
]


def exercise2(timeout: int = 180, max_memory: str = "48g") -> Dict[str, Dict[str, str]]:
    """Exercise 2: Goal recognition agent benchmarked on multiple levels."""
    print("\n=== EXERCISE 2 (MAvis3): Goal Recognition Agent ===\n")
    results: Dict[str, Dict[str, str]] = {}

    for level in exercise2_levels:
        print(f"Running goalrecognition on level {level}")
        stdout, stderr = run_goalrecognition(level, timeout, max_memory)
        results[f"{level}_goalrecognition"] = {
            "level": level,
            "strategy": "goalrecognition",
            "stdout": stdout,
            "stderr": stderr,
        }
        print(f"Completed {level} (goalrecognition)\n")

    with open("data/exercise2_results_mavis3.json", "w") as f:
        json.dump(results, f, indent=4)
    print("Exercise 2 results saved to data/exercise2_results_mavis3.json\n")
    return results


if __name__ == "__main__":
    exercise2()
