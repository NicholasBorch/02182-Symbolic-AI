# coding: utf-8
import random

from search import print_debug
from search.domain import Level, State
from search.domain.actions import Action, JointAction, Push, Move, NoOp
from search.algorithms.and_or_graph_search import and_or_graph_search
from search.agents.server_communication import send_joint_action, joint_action_to_string


# ============================================================
# Slippery floor helpers
# ============================================================

ORTHOGONAL = {
    "N": ["E", "W"],
    "S": ["E", "W"],
    "E": ["N", "S"],
    "W": ["N", "S"],
}


def _get_agent_direction(action: Action) -> str:
    return action.name.split("(")[1].split(",")[0]


def _get_box_direction(action: Action) -> str:
    return action.name.split(",")[1].strip(")")


def _get_push_variants(action: Push) -> list[Push]:
    agent_dir = _get_agent_direction(action)
    box_dir = _get_box_direction(action)
    variants = [action]
    for orth_dir in ORTHOGONAL[box_dir]:
        variants.append(Push(agent_dir, orth_dir))
    return variants


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
    Clumsy agent: Move next to a box might accidentally push it.
    Results(s, Move(D)) = { Result(s, Move(D)), Result(s, Push(D,D)) if applicable }
    Push and Pull actions are deterministic.
    """
    action = joint_action[0]

    if not isinstance(action, Move):
        return [state.result(joint_action)]

    direction = action.name.split("(")[1].strip(")")

    standard_case = state.result(joint_action)

    accidental_push = Push(direction, direction)
    push_joint = (accidental_push,)

    if state.is_applicable(push_joint):
        bumped_case = state.result(push_joint)
        if bumped_case != standard_case:
            return [standard_case, bumped_case]

    return [standard_case]


results_functions = {
    "slippery": slippery_results,
    "fumble": fumble_results,
    "clumsy": clumsy_results,
}

CHANCE_OF_FUMBLE = 0.3
CHANCE_OF_BUMP = 0.3


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
                v for v in variants
                if current_state.is_applicable((v,))
            ]
            chosen = random.choice(applicable_variants)
            chosen_joint = (chosen,)

            if chosen != action:
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
            direction = action.name.split("(")[1].strip(")")
            accidental_push = Push(direction, direction)
            push_joint = (accidental_push,)

            if current_state.is_applicable(push_joint) and random.random() < CHANCE_OF_BUMP:
                print_debug(f"BUMP! Intended: {joint_action_to_string(joint_action)}, "
                            f"Actual: {joint_action_to_string(push_joint)}")
                _ = send_joint_action(push_joint)
                current_state = current_state.result(push_joint)
            else:
                print_debug(joint_action_to_string(joint_action))
                _ = send_joint_action(joint_action)
                current_state = current_state.result(joint_action)

        # --- Deterministic execution (Move, Pull, NoOp) ---
        else:
            print_debug(joint_action_to_string(joint_action))
            _ = send_joint_action(joint_action)
            current_state = current_state.result(joint_action)