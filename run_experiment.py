import subprocess
from typing import Dict
import json

def run_uninformed_search(level:str, strategy:str, timeout : int = 310, max_memory: str = "48g") -> tuple[str, str]:
    cmd = [
        "java", "-jar", "server.jar",
        "-t", str(timeout),
        "-c", f"python3 client.py --max-memory {max_memory} classic --strategy {strategy}",
        "-l", f"levels/{level}.lvl"
    ]
    
    print(cmd)

<<<<<<< HEAD
    # try:
    #     result = subprocess.run(
    #         cmd,
    #         capture_output=True,
    #         text=True,
    #         timeout=timeout+15,
    #         cwd="/workspaces/mavis_client"
    #     )
    # except subprocess.TimeoutExpired:
    #     print(f"Timeout expired for level {level} with strategy {strategy}")
    #     return "Timeout", "Timeout  expired"
=======
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout+15,
            cwd="/workspaces/mavis_client"
        )
    except subprocess.TimeoutExpired:
        print(f"Timeout expired for level {level} with strategy {strategy}")
        return "Timeout", "Timeout  expired"
>>>>>>> 842a3cc (New stuff)
    
    # return result.stdout, result.stderr

run_uninformed_search("BFSfriendly", "bfs")

# def run_informed_search(level:str, strategy : str, heuristic : str, timeout : int=310, max_memory: str = "48g"):
    
#     cmd = [
#         "java", "-jar", "server.jar",
#         "-t", str(timeout),
#         "-c", f"python3 client.py --max-memory {max_memory} classic --strategy {strategy} --heuristic {heuristic}",
#         "-l", f"levels/{level}.lvl"
#     ]
    
#     try:
#         result = subprocess.run(
#             cmd,
#             capture_output=True,
#             text=True,
#             timeout=timeout+15,
#             cwd="/workspaces/mavis_client"
#         )
#     except subprocess.TimeoutExpired:
#         print(f"Timeout expired for level {level} with strategy {strategy} and heuristic {heuristic}")
#         return "Timeout", "Timeout expired"

#     output = result.stdout, result.stderr
#     return output


# # Exercise 2: BFS for Multi-Agent Pathfinding
# exercise2_levels = [
#     "MAPF00",
#     "MAPF01",
#     "MAPF02",
#     "MAPF02C",
#     "MAPF03",
#     "MAPF03C",
#     "MAPFslidingpuzzle",
#     "MAPFreorder2"
# ]

# # Exercise 3: DFS for Multi-Agent Pathfinding (same levels + BFSfriendly)
# exercise3_levels = [
#     "MAPF00",
#     "MAPF01",
#     "MAPF02",
#     "MAPF02C",
#     "MAPF03",
#     "MAPF03C",
#     "MAPFslidingpuzzle",
#     "MAPFreorder2",
#     "BFSfriendly"
# ]

# # Exercise 4: Informed Search on MAPF levels
# exercise4_levels = [
#     "MAPF00",
#     "MAPF01",
#     "MAPF02",
#     "MAPF02C",
#     "MAPF03",
#     "MAPF03C",
#     "BFSfriendly",
#     "MAPFslidingpuzzle",
#     "MAPFreorder2"
# ]

# # Exercise 5: Single-Agent with Boxes
# exercise5_levels = [
#     "SAD1",
#     "SAD2",
#     "SAD3",
#     "SAfriendofBFS",
#     "SAFirefly",
#     "SACrunch"
# ]

# exercise5_soko_levels = [
#     "SAsoko1_04", "SAsoko1_08", "SAsoko1_16", "SAsoko1_32", "SAsoko1_64", "SAsoko1_128",
#     "SAsoko2_04", "SAsoko2_08", "SAsoko2_16", "SAsoko2_32", "SAsoko2_64", "SAsoko2_128",
#     "SAsoko3_04", "SAsoko3_05", "SAsoko3_06", "SAsoko3_07", "SAsoko3_08",
#     "SAsoko3_16", "SAsoko3_32", "SAsoko3_64", "SAsoko3_128"
# ]


<<<<<<< HEAD
# def run_exercise2(timeout=310, max_memory="48g") -> Dict[str, Dict[str, str]]:
#     """Exercise 2: BFS on MAPF levels"""
#     print("\n=== EXERCISE 2: BFS for Multi-Agent Pathfinding ===\n")
#     results: Dict[str, Dict[str, str]] = {}
=======
def run_exercise2(timeout=310, max_memory="48g") -> Dict[str, Dict[str, str]]:
    """Exercise 2: BFS on MAPF levels"""
    print("\n=== EXERCISE 2: BFS for Multi-Agent Pathfinding ===\n")
    results: Dict[str, Dict[str, str]] = {}
>>>>>>> 842a3cc (New stuff)
    
#     for level in exercise2_levels:
#         print(f"Running BFS on level {level}")
#         stdout, stderr = run_uninformed_search(level, "bfs", timeout, max_memory)
#         results[f"{level}_bfs"] = {
#             "level": level,
#             "strategy": "bfs",
#             "stdout": stdout,
#             "stderr": stderr
#         }
#         print(f"Completed {level}\n")
    
#     with open("exercise2_results.json", "w") as f:
#         json.dump(results, f, indent=4)
#     print("Exercise 2 results saved to exercise2_results.json\n")
#     return results


# def run_exercise3(timeout=310, max_memory="48g"):
#     """Exercise 3: DFS on MAPF levels + BFS and DFS on BFSfriendly"""
#     print("\n=== EXERCISE 3: DFS for Multi-Agent Pathfinding ===\n")
#     results: Dict[str, Dict[str, str]] = {}
    
#     for level in exercise3_levels:
#         print(f"Running DFS on level {level}")
#         stdout, stderr = run_uninformed_search(level, "dfs", timeout, max_memory)
#         results[f"{level}_dfs"] = {
#             "level": level,
#             "strategy": "dfs",
#             "stdout": stdout,
#             "stderr": stderr
#         }
#         print(f"Completed {level}\n")
    
#     # Also run BFS on BFSfriendly for comparison
#     print("Running BFS on BFSfriendly for comparison")
#     stdout, stderr = run_uninformed_search("BFSfriendly", "bfs", timeout, max_memory)
#     results["BFSfriendly_bfs"] = {
#         "level": "BFSfriendly",
#         "strategy": "bfs",
#         "stdout": stdout,
#         "stderr": stderr
#     }
    
#     with open("exercise3_results.json", "w") as f:
#         json.dump(results, f, indent=4)
#     print("Exercise 3 results saved to exercise3_results.json\n")
#     return results


# def run_exercise4(timeout=310, max_memory="48g"):
#     """Exercise 4: Informed Search (A* and Greedy with goalcount and advanced heuristics)"""
#     print("\n=== EXERCISE 4: Informed Search on MAPF levels ===\n")
#     results: Dict[str, Dict[str, str]] = {}
    
#     for level in exercise4_levels:
#         for strategy in ["astar", "greedy"]:
#             for heuristic in ["goalcount", "advanced"]:
#                 print(f"Running {strategy} with {heuristic} heuristic on level {level}")
#                 stdout, stderr = run_informed_search(level, strategy, heuristic, timeout, max_memory)
#                 results[f"{level}_{strategy}_{heuristic}"] = {
#                     "level": level,
#                     "strategy": strategy,
#                     "heuristic": heuristic,
#                     "stdout": stdout,
#                     "stderr": stderr
#                 }
#                 print(f"Completed {level} with {strategy}/{heuristic}\n")
    
#     with open("exercise4_results.json", "w") as f:
#         json.dump(results, f, indent=4)
#     print("Exercise 4 results saved to exercise4_results.json\n")
#     return results


# def run_exercise5(timeout=310, max_memory="48g"):
#     """Exercise 5: Single-Agent with Boxes"""
#     print("\n=== EXERCISE 5: Single-Agent with Boxes ===\n")
#     results: Dict[str, Dict[str, str]] = {}
    
#     # BFS on SAD and SAFirefly/SACrunch levels
#     for level in ["SAD1", "SAD2", "SAD3", "SAfriendofBFS", "SAFirefly", "SACrunch"]:
#         print(f"Running BFS on level {level}")
#         stdout, stderr = run_uninformed_search(level, "bfs", timeout, max_memory)
#         results[f"{level}_bfs"] = {
#             "level": level,
#             "strategy": "bfs",
#             "stdout": stdout,
#             "stderr": stderr
#         }
#         print(f"Completed {level}\n")
    
#     # DFS on SAFirefly and SACrunch
#     for level in ["SAFirefly", "SACrunch"]:
#         print(f"Running DFS on level {level}")
#         stdout, stderr = run_uninformed_search(level, "dfs", timeout, max_memory)
#         results[f"{level}_dfs"] = {
#             "level": level,
#             "strategy": "dfs",
#             "stdout": stdout,
#             "stderr": stderr
#         }
#         print(f"Completed {level}\n")
    
#     # Greedy with goalcount on SAFirefly and SACrunch
#     for level in ["SAFirefly", "SACrunch"]:
#         print(f"Running Greedy with goalcount on level {level}")
#         stdout, stderr = run_informed_search(level, "greedy", "goalcount", timeout, max_memory)
#         results[f"{level}_greedy_goalcount"] = {
#             "level": level,
#             "strategy": "greedy",
#             "heuristic": "goalcount",
#             "stdout": stdout,
#             "stderr": stderr
#         }
#         print(f"Completed {level}\n")
    
#     # Greedy with advanced heuristic on Sokoban levels
#     for level in exercise5_soko_levels:
#         print(f"Running Greedy with advanced heuristic on level {level}")
#         stdout, stderr = run_informed_search(level, "greedy", "advanced", timeout, max_memory)
#         results[f"{level}_greedy_advanced"] = {
#             "level": level,
#             "strategy": "greedy",
#             "heuristic": "advanced",
#             "stdout": stdout,
#             "stderr": stderr
#         }
#         print(f"Completed {level}\n")
    
#     # Greedy with advancedgoal heuristic on SAFirefly and SACrunch
#     for level in ["SAFirefly", "SACrunch"]:
#         print(f"Running Greedy with advancedgoal on level {level}")
#         stdout, stderr = run_informed_search(level, "greedy", "advancedgoal", timeout, max_memory)
#         results[f"{level}_greedy_advancedgoal"] = {
#             "level": level,
#             "strategy": "greedy",
#             "heuristic": "advancedgoal",
#             "stdout": stdout,
#             "stderr": stderr
#         }
#         print(f"Completed {level}\n")
    
#     # Greedy with advancedgoal heuristic on Sokoban levels
#     for level in exercise5_soko_levels:
#         print(f"Running Greedy with advancedgoal heuristic on level {level}")
#         stdout, stderr = run_informed_search(level, "greedy", "advancedgoal", timeout, max_memory)
#         results[f"{level}_greedy_advancedgoal"] = {
#             "level": level,
#             "strategy": "greedy",
#             "heuristic": "advancedgoal",
#             "stdout": stdout,
#             "stderr": stderr
#         }
#         print(f"Completed {level}\n")
    
#     with open("exercise5_results.json", "w") as f:
#         json.dump(results, f, indent=4)
#     print("Exercise 5 results saved to exercise5_results.json\n")
#     return results


# def run_all_exercises(timeout=300, max_memory="48g"):
#     """Run all exercises"""
#     print("=" * 60)
#     print("RUNNING ALL EXERCISES")
#     print("=" * 60)
    
#     run_exercise2(timeout, max_memory)
#     run_exercise3(timeout, max_memory)
#     run_exercise4(timeout, max_memory)
#     run_exercise5(timeout, max_memory)
    
#     print("=" * 60)
#     print("ALL EXERCISES COMPLETED")
#     print("=" * 60)


# if __name__ == "__main__":
#     # Run all exercises with 3-minute timeout and 48GB memory
#     # run_all_exercises(timeout=300, max_memory="48g")
    
<<<<<<< HEAD
#     # Or run individual exercises:
#     # run_exercise2()
#     # run_exercise3()
#     # run_exercise4()
#     # run_exercise5()
#     run_uninformed_search("BFSfriendly", "bfs")
=======
    # Or run individual exercises:
    run_exercise2()
    run_exercise3()
    run_exercise4()
    # run_exercise5()
>>>>>>> 842a3cc (New stuff)
