import json
import re
import pandas as pd


def parse_result(entry: dict) -> dict:
    stdout = entry.get("stdout", "")
    stderr = entry.get("stderr", "")

    # States generated: from stdout "[client][error] States generated: 48"
    states_match = re.search(r"States generated:\s*(\d+)", stdout)
    states_generated = int(states_match.group(1)) if states_match else None

    # Time to solve: from stdout "[server][info] Time to solve: 0.005 seconds."
    time_match = re.search(r"Time to solve:\s*([\d.]+)\s*seconds", stdout)
    time_s = float(time_match.group(1)) if time_match else None

    # Solution length: from stdout "[server][info] Actions used: 14." or "2,461."
    actions_match = re.search(r"Actions used:\s*([\d,]+)", stdout)
    solution_length = int(actions_match.group(1).replace(",", "")) if actions_match else None

    # AND-OR search depth: from stderr "Search has found plan at depth 6!" or fall back to max cutoff depth
    depth_match = re.search(r"Search has found plan at depth\s*(\d+)", stderr)
    if depth_match:
        depth = int(depth_match.group(1))
    else:
        cutoff_matches = re.findall(r"Search was cutoff at depth\s*(\d+)", stderr)
        depth = max(map(int, cutoff_matches)) if cutoff_matches else None

    # Level solved
    level_solved = re.search(r"(?<=Level solved: )(Yes|No)", stdout)
    if level_solved:
        solved = level_solved.group(0)  # "Yes" or "No"
    else:
        solved = "Unknown"

    # Mark timeouts explicitly
    if stdout == "Timeout":
        states_generated = "Timeout"
        time_s = "Timeout"
        solution_length = "Timeout"
        depth = "Timeout"

    heuristic = entry.get("heuristic", "-").upper() if entry.get("heuristic") else "-"

    return {
        "Level": entry["level"],
        "Strategy": entry["strategy"].upper(),
        "Heuristic": heuristic,
        "Level solved": solved,
        "States Generated": states_generated,
        "Depth": depth,
        "Time/s": time_s,
        "Steps": solution_length,
    }


def load_results(filepath: str) -> pd.DataFrame:
    with open(filepath) as f:
        data = json.load(f)

    rows = [parse_result(entry) for entry in data.values()]
    df = pd.DataFrame(rows, columns=["Level", "Strategy", "Heuristic","Level solved", "States Generated", "Depth", "Time/s", "Steps"])
    df["States Generated"] = pd.to_numeric(df["States Generated"], errors='coerce').astype("Int64")
    df["Depth"] = pd.to_numeric(df["Depth"], errors='coerce').astype("Int64")
    return df


if __name__ == "__main__":
    # for index in [2,3,4]:
        # df = load_results(f"exercise{index}_results.json")
        # print(f"Results for exercise {index}:")
        # print(df.to_string(index=False))
        # print("\n")
    # df = load_results("exercise4_results.json")
    # print(df[df['Heuristic'] == "ADVANCED"]) 
    # df_ex2 = load_results("exercise2_results.json")
    # df_ex3 = load_results("exercise3_results.json")
    # df_ex4 = load_results("exercise4_results.json")
    # df_ex5 = load_results("exercise5_results.json")
    df_ex1_mavis2 = load_results("data/exercise1_results_mavis2.json")
    df_ex2_mavis2 = load_results("data/exercise2_results_mavis2.json")
    df_ez3_mavis2 = load_results("data/exercise3_results_mavis2.json")
    df_ex4_mavis2 = load_results("data/exercise4_results_mavis2.json")

    df_ex1_mavis2.drop(columns='Heuristic')

    
    # pd.concat([df_ex2, df_ex3]).drop(columns=['Heuristic'])
    # pd.concat([df_ex2, df_ex3]).drop(columns=['Heuristic'])
