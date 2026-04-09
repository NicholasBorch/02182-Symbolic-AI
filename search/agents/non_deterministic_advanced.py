# coding: utf-8
import random

from search import print_debug
from search.domain import Level, State
from search.domain.actions import Action, JointAction, Push, Pull, Move, NoOp
from search.algorithms.and_or_graph_search import and_or_graph_search
from search.agents.server_communication import send_joint_action, joint_action_to_string


# ============================================================
# Helpers
# ============================================================

ORTHOGONAL = {
    "N": ["E", "W"],
    "S": ["E", "W"],
    "E": ["N", "S"],
    "W": ["N", "S"],
}

ALL_DIRECTIONS = ["N", "S", "E", "W"]


def _get_agent_direction(action: Action) -> str:
    return action.name.split("(")[1].split(",")[0]


def _get_box_direction(action: Action) -> str:
    return action.name.split(",")[1].strip(")")


def _get_move_direction(action: Move) -> str:
    return action.name.split("(")[1].strip(")")


def _get_push_variants(action: Push) -> list[Push]:
    agent_dir = _get_agent_direction(action)
    box_dir = _get_box_direction(action)
    variants = [action]
    for orth_dir in ORTHOGONAL[box_dir]:
        variants.append(Push(agent_dir, orth_dir))
    return variants


def _get_pull_variants(action: Move) -> list[Pull]:
    """Given Move(D), return all Pull(D, B) for every box direction B."""
    move_dir = _get_move_direction(action)
    return [Pull(move_dir, box_dir) for box_dir in ALL_DIRECTIONS]


# ============================================================
# Results functions
# ============================================================

def slippery_results(state: State, joint_action: JointAction) -> list[State]:
    """
    Slippery floor: box might slip orthogonally when pushed.
    Results(s, Push(A,B)) = { Result(s,a) | a in {Push(A,B), Push(A,orth1), Push(A,orth2)}
                              and a is applicable in s }
    """
    action = joint_action[0]

    if not isinstance(action, Push):
        return [state.result(joint_action)]

    variants = _get_push_variants(action)

    outcomes = []
    seen = set()
    for variant in variants:
        variant_joint = (variant,)
        if state.is_applicable(variant_joint):
            result_state = state.result(variant_joint)
            if result_state not in seen:
                seen.add(result_state)
                outcomes.append(result_state)

    return outcomes


def fumble_results(state: State, joint_action: JointAction) -> list[State]:
    """
    Fumble / all-or-nothing: push might fail entirely.
    Results(s, Push(A,B)) = { Result(s, Push(A,B)), s }
    """
    action = joint_action[0]

    if not isinstance(action, Push):
        return [state.result(joint_action)]

    standard_case = state.result(joint_action)
    fumble_case = state  # nothing happens

    if standard_case == fumble_case:
        return [standard_case]
    return [standard_case, fumble_case]


def clumsy_results(state: State, joint_action: JointAction) -> list[State]:
    """
    Clumsy agent: moving away from a box might accidentally drag it along.
    Results(s, Move(D)) = { Result(s, Move(D)) }
                          ∪ { Result(s, Pull(D,B)) | Pull(D,B) is applicable in s }
    Push and Pull actions are deterministic.
    """
    action = joint_action[0]

    if not isinstance(action, Move):
        return [state.result(joint_action)]

    standard_case = state.result(joint_action)
    outcomes = [standard_case]
    seen = {standard_case}

    # Check all possible accidental pulls in the move direction
    pull_variants = _get_pull_variants(action)
    for pull in pull_variants:
        pull_joint = (pull,)
        if state.is_applicable(pull_joint):
            result_state = state.result(pull_joint)
            if result_state not in seen:
                seen.add(result_state)
                outcomes.append(result_state)

    return outcomes


results_functions = {
    "slippery": slippery_results,
    "fumble": fumble_results,
    "clumsy": clumsy_results,
}

CHANCE_OF_FUMBLE = 0.5
CHANCE_OF_DRAG = 0.5


# ============================================================
# Agent
# ============================================================

def non_deterministic_advanced_agent(
    level: Level,
    action_library: list[Action],
    iterative_deepening: bool = True,
    allow_cyclic: bool = False,
    results_function_key: str = "slippery",
):
    initial_state = level.initial_state()
    goal_description = level.goal_description()
    action_set = [action_library]

    if results_function_key not in results_functions:
        raise ValueError(f"Invalid results function: {results_function_key}")
    results_function = results_functions[results_function_key]

    worst_case_length, plan = and_or_graph_search(
        initial_state, action_set, goal_description.is_goal,
        results_function, iterative_deepening, allow_cyclic
    )

    if worst_case_length is None or plan is None:
        print_debug("Failed to find strong plan!")
        return

    current_state = initial_state

    while True:
        if goal_description.is_goal(current_state):
            break

        if current_state not in plan:
            print_debug(f"Reached state not covered by plan!\n{current_state}")
            break

        joint_action = plan[current_state]
        action = joint_action[0]

        # --- Slippery execution ---
        if isinstance(action, Push) and results_function == slippery_results:
            variants = _get_push_variants(action)
            applicable_variants = [
                (v,) for v in variants
                if current_state.is_applicable((v,))
            ]
            chosen_joint = random.choice(applicable_variants)

            if chosen_joint != joint_action:
                print_debug(f"SLIP! Intended: {joint_action_to_string(joint_action)}, "
                            f"Actual: {joint_action_to_string(chosen_joint)}")
            else:
                print_debug(joint_action_to_string(joint_action))

            _ = send_joint_action(chosen_joint)
            current_state = current_state.result(chosen_joint)

        # --- Fumble execution ---
        elif isinstance(action, Push) and results_function == fumble_results:
            if random.random() < CHANCE_OF_FUMBLE:
                print_debug(f"FUMBLE! Intended: {joint_action_to_string(joint_action)}, "
                            f"Actual: [NoOp]")
                noop_joint = (NoOp(),)
                _ = send_joint_action(noop_joint)
                # State doesn't change

            else:
                print_debug(joint_action_to_string(joint_action))
                _ = send_joint_action(joint_action)
                current_state = current_state.result(joint_action)

        # --- Clumsy execution ---
        elif isinstance(action, Move) and results_function == clumsy_results:
            # Check for applicable accidental pulls
            pull_variants = _get_pull_variants(action)
            applicable_pulls = [
                (p,) for p in pull_variants
                if current_state.is_applicable((p,))
            ]

            if applicable_pulls and random.random() < CHANCE_OF_DRAG:
                chosen_joint = random.choice(applicable_pulls)
                print_debug(f"DRAG! Intended: {joint_action_to_string(joint_action)}, "
                            f"Actual: {joint_action_to_string(chosen_joint)}")
                _ = send_joint_action(chosen_joint)
                current_state = current_state.result(chosen_joint)
            else:
                print_debug(joint_action_to_string(joint_action))
                _ = send_joint_action(joint_action)
                current_state = current_state.result(joint_action)

        # --- Deterministic execution (Push, Pull, NoOp in non-matching mode) ---
        else:
            print_debug(joint_action_to_string(joint_action))
            _ = send_joint_action(joint_action)
            current_state = current_state.result(joint_action)