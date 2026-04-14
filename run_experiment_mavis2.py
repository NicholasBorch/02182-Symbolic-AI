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

    with open("data/exercise1_results_mavis2.json", "w") as f:
        json.dump(results, f, indent=4)
    print("Exercise 1 results saved to data/exercise1_results_mavis2.json\n")
    return results


exercise2_levels = [
    "MAhelper.lvl",
    "MAhelper3.lvl",
    "MAhelperCustom.lvl",
    "MAhelperCustom2.lvl",
    "MAhelperCustom3.lvl",
    "MAhelperCustom4.lvl",
    "MAExample.lvl",
]


def run_helper(level: str, timeout: int = 180, max_memory: str = "48g") -> tuple[str, str]:
    cmd = [
        "java", "-jar", "server.jar",
        "-s", "300",
        "-t", str(timeout),
        "-c", f"python3 client.py --max-memory {max_memory} helper",
        "-l", f"levels/{level}"
    ]
    print(cmd)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)
    except subprocess.TimeoutExpired:
        print(f"Timeout expired for level {level} (helper)")
        return "Timeout", "Timeout expired"
    return result.stdout, result.stderr


def exercise2(timeout: int = 180, max_memory: str = "48g") -> Dict[str, Dict[str, str]]:
    """Exercise 2: Helper agent on custom levels"""
    print("\n=== EXERCISE 2: Helper Agent ===\n")
    results: Dict[str, Dict[str, str]] = {}

    for level in exercise2_levels:
        print(f"Running helper on level {level}")
        stdout, stderr = run_helper(level, timeout, max_memory)
        results[f"{level}_helper"] = {
            "level": level,
            "strategy": "helper",
            "stdout": stdout,
            "stderr": stderr,
        }
        print(f"Completed {level} (helper)\n")

    with open("data/exercise2_results_mavis2.json", "w") as f:
        json.dump(results, f, indent=4)
    print("Exercise 2 results saved to data/exercise2_results_mavis2.json\n")
    return results


exercise3_levels = [
    "SAsoko1_08.lvl",
    "ex3_clearlevel.lvl",
    "ex3_clutteredlevel.lvl",
]


def run_nondeterministic(level: str, timeout: int = 180, max_memory: str = "48g") -> tuple[str, str]:
    cmd = [
        "java", "-jar", "server.jar",
        "-s", "300",
        "-t", str(timeout),
        "-c", f"python3 client.py --max-memory {max_memory} nondeterministic",
        "-l", f"levels/{level}"
    ]
    print(cmd)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)
    except subprocess.TimeoutExpired:
        print(f"Timeout expired for level {level} (nondeterministic)")
        return "Timeout", "Timeout expired"
    return result.stdout, result.stderr


def exercise3(timeout: int = 180, max_memory: str = "48g") -> Dict[str, Dict[str, str]]:
    """Exercise 3: Nondeterministic agent on custom levels"""
    print("\n=== EXERCISE 3: Nondeterministic Agent ===\n")
    results: Dict[str, Dict[str, str]] = {}

    for level in exercise3_levels:
        print(f"Running nondeterministic on level {level}")
        stdout, stderr = run_nondeterministic(level, timeout, max_memory)
        results[f"{level}_nondeterministic"] = {
            "level": level,
            "strategy": "nondeterministic",
            "stdout": stdout,
            "stderr": stderr,
        }
        print(f"Completed {level} (nondeterministic)\n")

    with open("data/exercise3_results_mavis2.json", "w") as f:
        json.dump(results, f, indent=4)
    print("Exercise 3 results saved to data/exercise3_results_mavis2.json\n")
    return results


exercise4_levels = [
    "SAsoko1_08.lvl",
    "Non_det_Slippery1.lvl",
    "Non_det_Slippery2.lvl",
    "Non_det_slippery.lvl",
    "Non_det_Fumble1.lvl",
    "Non_det_Fumble2.lvl",
    "Non_det_Clumsy1.lvl",
    "Non_det_Clumsy2.lvl",
    "non_det_slippery3.lvl",
]


def run_nondeterministic_cyclic(level: str, timeout: int = 180, max_memory: str = "48g") -> tuple[str, str]:
    cmd = [
        "java", "-jar", "server.jar",
        "-s", "300",
        "-t", str(timeout),
        "-c", f"python3 client.py --max-memory {max_memory} nondeterministic --cyclic",
        "-l", f"levels/{level}"
    ]
    print(cmd)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)
    except subprocess.TimeoutExpired:
        print(f"Timeout expired for level {level} (nondeterministic --cyclic)")
        return "Timeout", "Timeout expired"
    return result.stdout, result.stderr


def exercise4(timeout: int = 180, max_memory: str = "48g") -> Dict[str, Dict[str, str]]:
    """Exercise 4: Advanced nondeterministic agent with --cyclic on custom levels"""
    print("\n=== EXERCISE 4: Nondeterministic Advanced (--cyclic) ===\n")
    results: Dict[str, Dict[str, str]] = {}

    for level in exercise4_levels:
        print(f"Running nondeterministic --cyclic on level {level}")
        stdout, stderr = run_nondeterministic_cyclic(level, timeout, max_memory)
        results[f"{level}_nondeterministic_cyclic"] = {
            "level": level,
            "strategy": "nondeterministic_cyclic",
            "stdout": stdout,
            "stderr": stderr,
        }
        print(f"Completed {level} (nondeterministic --cyclic)\n")

    with open("data/exercise4_results_mavis2.json", "w") as f:
        json.dump(results, f, indent=4)
    print("Exercise 4 results saved to data/exercise4_results_mavis2.json\n")
    return results


if __name__ == "__main__":
    # exercise1()
    exercise2()
    exercise3()
    exercise4()
