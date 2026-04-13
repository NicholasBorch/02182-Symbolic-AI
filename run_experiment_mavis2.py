import subprocess
from typing import Dict
import json


exercise1_levels = [
    "ex1_dec_bad1.lvl",
    "ex1_dec_bad2.lvl",
    "ex1_dec_good1.lvl",
    "ex1_dec_good2.lvl",
]


def run_decentralised(level: str, timeout: int = 180, max_memory: str = "48g") -> tuple[str, str]:
    cmd = [
        "java", "-jar", "server.jar",
        "-s", "300",
        "-t", str(timeout),
        "-c", f"python3 client.py --max-memory {max_memory} decentralised",
        "-l", f"levels/{level}"
    ]
    print(cmd)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)
    except subprocess.TimeoutExpired:
        print(f"Timeout expired for level {level} (decentralised)")
        return "Timeout", "Timeout expired"
    return result.stdout, result.stderr


def run_bfs(level: str, timeout: int = 180, max_memory: str = "48g") -> tuple[str, str]:
    cmd = [
        "java", "-jar", "server.jar",
        "-s", "300",
        "-t", str(timeout),
        "-c", f"python3 client.py --max-memory {max_memory} classic --strategy bfs",
        "-l", f"levels/{level}"
    ]
    print(cmd)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)
    except subprocess.TimeoutExpired:
        print(f"Timeout expired for level {level} (bfs)")
        return "Timeout", "Timeout expired"
    return result.stdout, result.stderr


def exercise1(timeout: int = 180, max_memory: str = "48g") -> Dict[str, Dict[str, str]]:
    """Exercise 1: Decentralised vs BFS on custom levels"""
    print("\n=== EXERCISE 1: Decentralised Search ===\n")
    results: Dict[str, Dict[str, str]] = {}

    for level in exercise1_levels:
        print(f"Running decentralised on level {level}")
        stdout, stderr = run_decentralised(level, timeout, max_memory)
        results[f"{level}_decentralised"] = {
            "level": level,
            "strategy": "decentralised",
            "stdout": stdout,
            "stderr": stderr,
        }
        print(f"Completed {level} (decentralised)\n")

        print(f"Running bfs on level {level}")
        stdout, stderr = run_bfs(level, timeout, max_memory)
        results[f"{level}_bfs"] = {
            "level": level,
            "strategy": "bfs",
            "stdout": stdout,
            "stderr": stderr,
        }
        print(f"Completed {level} (bfs)\n")

    with open("exercise1_results_mavis2.json", "w") as f:
        json.dump(results, f, indent=4)
    print("Exercise 1 results saved to exercise1_results_mavis2.json\n")
    return results


if __name__ == "__main__":
    exercise1()
