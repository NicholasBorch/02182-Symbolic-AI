# coding: utf-8
#
# Copyright 2021 The Technical University of Denmark
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

import random
from typing import Callable, TYPE_CHECKING

from search import print_debug
from search.domain import Level, State, GoalDescription
from search.domain.actions import Action, JointAction, ActionSet, NoOp, ActionLibrary

from search.algorithms.all_optimal_plans import MultiParentNode, all_optimal_plans
from search.algorithms.and_or_graph_search import and_or_graph_search
from search.frontiers.frontier import Frontier
from search.agents.server_communication import send_joint_action

if TYPE_CHECKING:
    from typing import TypeAlias
    HelperPolicy: TypeAlias = dict[State, JointAction]
    ResultsFunction: TypeAlias = Callable


ACTOR_AGENT_INDEX = 0
HELPER_AGENT_INDEX = 1


class DisjunctiveGoalDescription:
    """
    DisjunctiveGoalDescription is a wrapper class which allow for the representation of multiple possible
    goal descriptions. It has the same 'is_goal' method as a GoalDescription object and can therefore be
    used in the same places, but in contrast to the regular GoalDescription object, it returns True when
    one of its give goals are satisfied, thus allowing for a logical 'OR' to be expressed.
    """

    def __init__(self, possible_goal_descriptions: list[GoalDescription]) -> None:
        # possible_goal_descriptions should be a list of goals
        self.possible_goals = possible_goal_descriptions

    def is_goal(self, belief_node: GoalRecognitionNode) -> bool:
        for possible_goal in self.possible_goals:
            if possible_goal.is_goal(belief_node.state):
                return True
        return False


class GoalRecognitionNode:
    """
    GoalRecognitionNode is a wrapper class which can be used for implementing
    AND-OR based graph search. It allows a hospital state object and a solution
    graph object to be integrated into a single object, which the methods
    'get_applicable_actions' and 'result' as required by the AND-OR graph
    search. Note that the usage of this class is completely optional and you
    are free to implement your goal recognition in a different manner,
    if you so desire.
    """

    def __init__(self, state: State, solution_graph: MultiParentNode) -> None:
        self.state = state
        self.solution_graph = solution_graph

    def is_applicable(self, joint_action: JointAction) -> bool:
        return self.state.is_applicable(joint_action)

    def get_applicable_actions(self, action_set: ActionSet) -> list[Action]:
        # Here we are only interested in the actions of the helper, but state.get_applicable_actions will return a list
        # of joint actions, where the actor action is always NoOp().
        # Note there is lots of room for improvement here, e.g. using the optimal actions from the solution graph for the
        # actor agent instead of the full action set. This is just a simple example.
        applicable_joint_actions = self.state.get_applicable_actions(action_set)
        applicable_actions = [
            joint_action[HELPER_AGENT_INDEX] for joint_action in applicable_joint_actions
        ]
        return applicable_actions

    def result(self, joint_action: JointAction) -> GoalRecognitionNode:
        actor_action = joint_action[ACTOR_AGENT_INDEX]

        conflicting = self.state.is_conflicting(joint_action)
        actor_applicable = self.state.is_applicable(joint_action)
        actor_in_sg = actor_action in self.solution_graph.optimal_actions_and_results

        if conflicting:
            effective_ja = tuple(NoOp() for _ in range(len(joint_action)))
            new_solution_graph = self.solution_graph
        elif actor_in_sg and actor_applicable:
            effective_ja = joint_action
            new_solution_graph = self.solution_graph.optimal_actions_and_results[actor_action]
        else:
            effective_ja = tuple(
                NoOp() if i == ACTOR_AGENT_INDEX else joint_action[i]
                for i in range(len(joint_action))
            )
            new_solution_graph = self.solution_graph

        new_state = self.state.result(effective_ja)
        return GoalRecognitionNode(new_state, new_solution_graph)

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return (
                self.state == other.state
                and self.solution_graph == other.solution_graph
            )
        else:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self.state, self.solution_graph))


class HelperNGoalRecognitionNode:
    """
    State for Helper N (N >= 2) planning.
    State = (physical_state, node_in_helper_(N-1)_plan)

    Helper N branches on the actor's nondeterminism (from solution_graph),
    and for each actor percept, looks up Helper (N-1)'s action and advances
    the Helper (N-1) plan node accordingly.
    """

    def __init__(self, state: State, helper_prev_node: GoalRecognitionNode | HelperNGoalRecognitionNode) -> None:
        self.state = state
        self.helper_prev_node = helper_prev_node

    def is_applicable(self, joint_action: JointAction) -> bool:
        return self.state.is_applicable(joint_action)

    def get_applicable_actions(self, helper_index: int, action_set: ActionSet) -> list[Action]:
        applicable_joint_actions = self.state.get_applicable_actions(action_set)
        applicable_actions = [
            joint_action[helper_index] for joint_action in applicable_joint_actions
        ]
        return applicable_actions

    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return self.state == other.state and self.helper_prev_node == other.helper_prev_node
        else:
            return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self.state, self.helper_prev_node))


def solution_graph_results(
    recognition_node: GoalRecognitionNode, joint_action: JointAction
) -> list[GoalRecognitionNode]:
    helper_action = joint_action[HELPER_AGENT_INDEX]
    num_agents = len(joint_action)

    percepts = [
        action
        for action, child in recognition_node.solution_graph.optimal_actions_and_results.items()
        if child.consistent_goals
    ]
    if not percepts:
        percepts = [NoOp()]

    outcomes = []
    for actor_action in percepts:
        ja = tuple(
            actor_action if i == ACTOR_AGENT_INDEX
            else helper_action if i == HELPER_AGENT_INDEX
            else NoOp()
            for i in range(num_agents)
        )
        outcomes.append(recognition_node.result(ja))
    return outcomes


def make_helper_n_results(
    helper_level: int,
    prev_helper_policy: HelperPolicy,
    prev_helper_results_fn: ResultsFunction | None = None,
) -> ResultsFunction:
    """
    Factory for creating a results function for Helper N (N >= 2).

    Args:
        helper_level: Which helper (2, 3, ...)
        prev_helper_policy: The AND-OR policy for Helper (N-1)
        prev_helper_results_fn: The results function for Helper (N-1) (None if Helper (N-1) is Helper 1)

    Returns:
        A results function for Helper N that branches on actor percepts and advances the previous helper's plan
    """
    def helper_n_results(state: HelperNGoalRecognitionNode, joint_action: JointAction) -> list[HelperNGoalRecognitionNode]:
        prev_node = state.helper_prev_node

        if prev_node not in prev_helper_policy:
            # prev_node is a goal state for helper k-1 (not stored in policy since
            # AND-OR search only maps non-goal states). This is a dead-end branch
            # where the filtered world finished early but the full world hasn't yet.
            return []

        prev_joint = prev_helper_policy[prev_node]
        num_agents = len(joint_action)

        solution_graph = (
            prev_node.solution_graph if isinstance(prev_node, GoalRecognitionNode)
            else prev_node.helper_prev_node.solution_graph
        )

        percepts = [
            action
            for action, child in solution_graph.optimal_actions_and_results.items()
            if child.consistent_goals
        ]
        if not percepts:
            percepts = [NoOp()]

        if prev_helper_results_fn is None:
            prev_outcomes = solution_graph_results(prev_node, prev_joint)
        else:
            prev_outcomes = prev_helper_results_fn(prev_node, prev_joint)

        if not prev_outcomes:
            return []

        outcomes = []
        for idx, actor_action in enumerate(percepts):
            ja = tuple(
                actor_action if i == ACTOR_AGENT_INDEX
                else prev_joint[i] if i < helper_level
                else joint_action[i] if i == helper_level
                else NoOp()
                for i in range(num_agents)
            )

            new_physical_state = state.state.result(ja)
            prev_next_node = prev_outcomes[idx] if idx < len(prev_outcomes) else prev_outcomes[-1]

            new_state = HelperNGoalRecognitionNode(new_physical_state, prev_next_node)
            outcomes.append(new_state)

        return outcomes

    return helper_n_results


def extract_agent_roles(level: Level) -> tuple[str, list[str]]:
    """
    Extract actor color and helper colors from agent positions.
    Actor is at index 0, helpers are at indices 1, 2, ...

    Returns:
        (actor_color, helper_colors)
    """
    actor_char = level.initial_agent_positions[ACTOR_AGENT_INDEX][1]
    actor_color = level.colors[actor_char]

    helper_colors = []
    for helper_idx in range(1, level.num_agents):
        if helper_idx < len(level.initial_agent_positions):
            helper_char = level.initial_agent_positions[helper_idx][1]
            helper_color = level.colors[helper_char]
            helper_colors.append(helper_color)

    return actor_color, helper_colors


def goal_recognition_agent(
    level: Level,
    action_library: ActionLibrary,
    frontier: Frontier[GoalRecognitionNode],
    iterative_deepening: bool = True,
    allow_cyclic: bool = False,
):
    """
    Multi-helper goal recognition agent with recursive planning.

    Supports Actor (color 0) and Helpers (colors 1, 2, ...).
    Each helper plans on top of the previous helper's AND-OR plan.
    """
    print_debug(f"[GR] Starting goal recognition with {level.num_agents} agents")
    initial_state = level.initial_state()
    goal_description = level.goal_description()

    actor_color, helper_colors = extract_agent_roles(level)
    print_debug(f"[GR] Actor color: {actor_color}, Helper colors: {helper_colors}")
    actor_goal = goal_description.color_filter(actor_color)

    current_state = initial_state
    pending_indices = list(range(actor_goal.num_sub_goals()))

    # Per-helper action sets: helper k's search only varies index k.
    # Using a shared action_set with all helpers = action_library makes
    # product(*action_set) grow as |action_library|^(num_agents-1), which is
    # far too large. Each helper's results function only reads joint_action[k],
    # so other slots must be [NoOp()] to avoid exponential blowup.
    action_sets: dict[int, ActionSet] = {}
    for k in range(1, level.num_agents):
        aset: ActionSet = [[NoOp()] for _ in range(level.num_agents)]
        aset[k] = action_library
        action_sets[k] = aset

    while pending_indices:
        pending_subgoals = [actor_goal.get_sub_goal(i) for i in pending_indices]
        print_debug(f"[GR] Planning for subgoals: {pending_indices}")

        chosen_idx = random.choice(pending_indices)
        actor_chosen = actor_goal.get_sub_goal(chosen_idx)

        monochrome_state = current_state.color_filter(actor_color)
        
        # Remove completed boxes from monochrome state so planner cannot move them
        completed_positions = set()
        for i in range(actor_goal.num_sub_goals()):
            if i not in pending_indices:
                for pos, char, _ in actor_goal.get_sub_goal(i).goals:
                    completed_positions.add(pos)
        monochrome_state.box_positions = [
            (pos, char) for pos, char in monochrome_state.box_positions
            if pos not in completed_positions
        ]

        ok, root_sg = all_optimal_plans(
            monochrome_state, [action_library], pending_subgoals, frontier
        )
        assert ok, "All-Optimal-Plans failed to find a solution graph"
        print_debug(f"[GR] All-Optimal-Plans complete")

        disjunctive = DisjunctiveGoalDescription(pending_subgoals)

        # Helper k plans in a state filtered to [actor, helper_1, ..., helper_k].
        # This way helper 1 ignores orange entities it can't control, and helper 2
        # then sees the full picture and makes helper 1's plan actually executable.
        helper1_colors = [actor_color, helper_colors[0]]
        top_colors = [actor_color] + helper_colors  # all helper colors (for top helper)
        gr_root = GoalRecognitionNode(current_state.color_filter_multi(helper1_colors), root_sg)

        policies = {1: None}
        results_fns = {1: solution_graph_results}

        print_debug(f"[GR] Planning Helper 1...")
        _, helper1_policy = and_or_graph_search(
            gr_root,
            action_sets[1],
            disjunctive.is_goal,
            solution_graph_results,
            iterative_deepening,
            allow_cyclic,
        )
        if helper1_policy is None:
            print_debug("Helper 1 failed to find a contingent plan")
            return
        print_debug(f"[GR] Helper 1 planning complete, policy size: {len(helper1_policy)}")

        policies[1] = helper1_policy
        current_root = gr_root

        for helper_idx in range(2, level.num_agents):
            print_debug(f"[GR] Planning Helper {helper_idx}...")
            k_colors = [actor_color] + helper_colors[:helper_idx]
            helper_n_root = HelperNGoalRecognitionNode(
                current_state.color_filter_multi(k_colors), current_root
            )
            helper_n_results_fn = make_helper_n_results(
                helper_idx,
                policies[helper_idx - 1],
                results_fns.get(helper_idx - 1),
            )
            results_fns[helper_idx] = helper_n_results_fn

            _, helper_n_policy = and_or_graph_search(
                helper_n_root,
                action_sets[helper_idx],
                disjunctive.is_goal,
                helper_n_results_fn,
                iterative_deepening,
                allow_cyclic,
            )
            if helper_n_policy is None:
                print_debug(f"Helper {helper_idx} failed to find a contingent plan")
                return
            print_debug(f"[GR] Helper {helper_idx} planning complete, policy size: {len(helper_n_policy)}")

            policies[helper_idx] = helper_n_policy
            current_root = helper_n_root

        print_debug(f"[GR] All helpers planned, starting execution...")

        gr_current = gr_root
        current_helper_n_node = current_root if level.num_agents > 2 else None

        while not actor_chosen.is_goal(current_state):
            # Ensure helper 1 has coverage of current GR node
            if gr_current not in policies[1]:
                _, policies[1] = and_or_graph_search(
                    gr_current,
                    action_sets[1],
                    disjunctive.is_goal,
                    solution_graph_results,
                    iterative_deepening,
                    allow_cyclic,
                )
                if policies[1] is None or gr_current not in policies[1]:
                    print_debug("Helper 1 lost coverage of current state")
                    return
                if level.num_agents > 2:
                    # Reset current_helper_n_node with the fresh gr_current as its
                    # helper_prev_node. The old node's prev pointed to a stale gr_current
                    # that is no longer in the new policies[1], causing every subsequent
                    # helper_n_results call to fail ("not in policy") during replan.
                    current_helper_n_node = HelperNGoalRecognitionNode(
                        current_state.color_filter_multi(top_colors),
                        gr_current,
                    )
                    results_fns[level.num_agents - 1] = make_helper_n_results(
                        level.num_agents - 1,
                        policies[1],
                        solution_graph_results,
                    )

            # Ensure top helper has coverage (3+ agents)
            if level.num_agents > 2 and current_helper_n_node not in policies[level.num_agents - 1]:
                _, policies[level.num_agents - 1] = and_or_graph_search(
                    current_helper_n_node,
                    action_sets[level.num_agents - 1],
                    disjunctive.is_goal,
                    results_fns[level.num_agents - 1],
                    iterative_deepening,
                    allow_cyclic,
                )
                if policies[level.num_agents - 1] is None or current_helper_n_node not in policies[level.num_agents - 1]:
                    print_debug(f"Helper {level.num_agents - 1} lost coverage of current state")
                    return

            choices = gr_current.solution_graph.get_actions_and_results_consistent_with_goal(
                actor_chosen
            )
            if choices:
                actor_action, next_sg = random.choice(choices)
            else:
                actor_action, next_sg = NoOp(), gr_current.solution_graph

            if level.num_agents == 2:
                helper_joint = policies[1][gr_current]
                joint_action = tuple(
                    actor_action if i == ACTOR_AGENT_INDEX
                    else helper_joint[i]
                    for i in range(level.num_agents)
                )
            else:
                # Each helper's action must come from its own policy; policy[k]'s
                # joint_action[1] is arbitrary (ignored during physical-state
                # transitions in make_helper_n_results), so we pull per-helper.
                joint_action_list = [NoOp()] * level.num_agents
                joint_action_list[ACTOR_AGENT_INDEX] = actor_action
                joint_action_list[1] = policies[1][gr_current][1]
                joint_action_list[level.num_agents - 1] = (
                    policies[level.num_agents - 1][current_helper_n_node][level.num_agents - 1]
                )
                joint_action = tuple(joint_action_list)

            successes = send_joint_action(joint_action)
            effective_ja = tuple(
                joint_action[i] if successes[i] else NoOp()
                for i in range(level.num_agents)
            )
            current_state = current_state.result(effective_ja)

            if successes[ACTOR_AGENT_INDEX]:
                gr_current = GoalRecognitionNode(
                    current_state.color_filter_multi(helper1_colors), next_sg
                )
                if current_helper_n_node is not None and level.num_agents > 2:
                    outcomes = results_fns[level.num_agents - 1](current_helper_n_node, joint_action)
                    if outcomes:
                        node = current_helper_n_node.helper_prev_node
                        while isinstance(node, HelperNGoalRecognitionNode):
                            node = node.helper_prev_node
                        solution_graph = node.solution_graph

                        percepts = [
                            action
                            for action, child in solution_graph.optimal_actions_and_results.items()
                            if child.consistent_goals
                        ]
                        if not percepts:
                            percepts = [NoOp()]
                        if actor_action in percepts:
                            idx = percepts.index(actor_action)
                            current_helper_n_node = outcomes[idx] if idx < len(outcomes) else outcomes[-1]
                        else:
                            current_helper_n_node = outcomes[0]
            else:
                gr_current = GoalRecognitionNode(
                    current_state.color_filter_multi(helper1_colors), gr_current.solution_graph
                )
                if current_helper_n_node is not None and level.num_agents > 2:
                    current_helper_n_node = HelperNGoalRecognitionNode(
                        current_state.color_filter_multi(top_colors),
                        current_helper_n_node.helper_prev_node
                    )

        pending_indices.remove(chosen_idx)
