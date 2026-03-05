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

    # Mark timeouts explicitly
    if stdout == "Timeout":
        states_generated = "Timeout"
        time_s = "Timeout"
        solution_length = "Timeout"

    heuristic = entry.get("heuristic", "-").upper() if entry.get("heuristic") else "-"

    return {
        "Level": entry["level"],
        "Strategy": entry["strategy"].upper(),
        "Heuristic": heuristic,
        "States Generated": states_generated,
        "Time/s": time_s,
        "Solution length": solution_length,
    }


def load_results(filepath: str) -> pd.DataFrame:
    with open(filepath) as f:
        data = json.load(f)

    rows = [parse_result(entry) for entry in data.values()]
    df = pd.DataFrame(rows, columns=["Level", "Strategy", "Heuristic", "States Generated", "Time/s", "Solution length"])
    return df


if __name__ == "__main__":
    # for index in [2,3,4]:
        # df = load_results(f"exercise{index}_results.json")
        # print(f"Results for exercise {index}:")
        # print(df.to_string(index=False))
        # print("\n")
    
    # df = load_results("exercise4_results.json")
    # print(df[df['Heuristic'] == "ADVANCED"]) 
    df_ex2 = load_results("exercise2_results.json")
    df_ex3 = load_results("exercise3_results.json")
    df_ex4 = load_results("exercise4_results.json")
    df_ex5 = load_results("exercise5_results.json")
    
    
    pd.concat([df_ex2, df_ex3]).drop(columns=['Heuristic'])