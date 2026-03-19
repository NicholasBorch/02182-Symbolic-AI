# coding: utf-8
import random

from search import print_debug
from search.domain import Level, State
from search.domain.actions import Action, JointAction, Push, Move, NoOp
from search.algorithms.and_or_graph_search import and_or_graph_search
from search.agents.server_communication import send_joint_action, joint_action_to_string


ORTHOGONAL = {
    "N": ["E", "W"],
    "S": ["E", "W"],
    "E": ["N", "S"],
    "W": ["N", "S"],
}


def _get_agent_direction(action: Action) -> str:
    """Extract agent direction from a Push action name, e.g. Push(N,E) -> 'N'."""
    return action.name.split("(")[1].split(",")[0]


def _get_box_direction(action: Action) -> str:
    """Extract box direction from a Push action name, e.g. Push(N,E) -> 'E'."""
    return action.name.split(",")[1].strip(")")


def _get_push_variants(action: Push) -> list[Push]:
    """Given Push(agent_dir, box_dir), return [original, orthogonal1, orthogonal2]."""
    agent_dir = _get_agent_direction(action)
    box_dir = _get_box_direction(action)
    variants = [action]
    for orth_dir in ORTHOGONAL[box_dir]:
        variants.append(Push(agent_dir, orth_dir))
    return variants


def slippery_results(state: State, joint_action: JointAction) -> list[State]:
    """
    Slippery floor nondeterminism:
    For Push actions, the box might slip orthogonally.
    Results(s, Push(A,B)) = { Result(s,a) | a in {Push(A,B), Push(A,orth1), Push(A,orth2)}
                              and a is applicable in s }
    All other actions (Move, Pull, NoOp) are deterministic.
    """
    action = joint_action[0]  # single agent

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


results_functions = {
    "slippery": slippery_results,
}


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

        if isinstance(action, Push):
            # Simulate slippery floor: randomly pick among applicable variants
            variants = _get_push_variants(action)
            applicable_variants = [
                v for v in variants
                if state_applicable(current_state, (v,))
            ]
            chosen = random.choice(applicable_variants)
            chosen_joint = (chosen,)

            print_debug(f"Intended: {joint_action_to_string(joint_action)}, "
                        f"Actual: {joint_action_to_string(chosen_joint)}")
            _ = send_joint_action(chosen_joint)
            current_state = current_state.result(chosen_joint)
        else:
            # Move, Pull, NoOp are deterministic
            print_debug(joint_action_to_string(joint_action))
            _ = send_joint_action(joint_action)
            current_state = current_state.result(joint_action)


def state_applicable(state: State, joint_action: JointAction) -> bool:
    """Helper to check applicability of a joint action."""
    return state.is_applicable(joint_action)