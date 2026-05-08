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

from search import print_debug
from search.domain import Level, State, GoalDescription
from search.domain.actions import Action, JointAction, ActionSet, NoOp, ActionLibrary

from search.algorithms.all_optimal_plans import MultiParentNode, all_optimal_plans
from search.algorithms.and_or_graph_search import and_or_graph_search
from search.frontiers.frontier import Frontier
from search.agents.server_communication import send_joint_action


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


def goal_recognition_agent(
    level: Level,
    action_library: ActionLibrary,
    frontier: Frontier[GoalRecognitionNode],
    iterative_deepening: bool = True,
    allow_cyclic: bool = False,
):
    """

    """
    initial_state = level.initial_state()
    goal_description = level.goal_description()

    actor_char = level.initial_agent_positions[ACTOR_AGENT_INDEX][1]
    actor_color = level.colors[actor_char]
    actor_goal = goal_description.color_filter(actor_color)

    current_state = initial_state
    pending_indices = list(range(actor_goal.num_sub_goals()))

    action_set: ActionSet = [[NoOp()] for _ in range(level.num_agents)]
    action_set[HELPER_AGENT_INDEX] = action_library

    while pending_indices:
        pending_subgoals = [actor_goal.get_sub_goal(i) for i in pending_indices]
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

        disjunctive = DisjunctiveGoalDescription(pending_subgoals)
        gr_root = GoalRecognitionNode(current_state, root_sg)

        _, policy = and_or_graph_search(
            gr_root,
            action_set,
            disjunctive.is_goal,
            solution_graph_results,
            iterative_deepening,
            allow_cyclic,
        )
        if policy is None:
            print_debug("Helper failed to find a contingent plan")
            return

        gr_current = gr_root
        while not actor_chosen.is_goal(current_state):
            if gr_current not in policy:
                _, policy = and_or_graph_search(
                    gr_current,
                    action_set,
                    disjunctive.is_goal,
                    solution_graph_results,
                    iterative_deepening,
                    allow_cyclic,
                )
                if policy is None or gr_current not in policy:
                    print_debug("Helper lost coverage of current state")
                    return

            helper_joint = policy[gr_current]
            helper_action = helper_joint[HELPER_AGENT_INDEX]

            choices = gr_current.solution_graph.get_actions_and_results_consistent_with_goal(
                actor_chosen
            )
            if choices:
                actor_action, next_sg = random.choice(choices)
            else:
                actor_action, next_sg = NoOp(), gr_current.solution_graph

            joint_action = tuple(
                actor_action if i == ACTOR_AGENT_INDEX
                else helper_action if i == HELPER_AGENT_INDEX
                else NoOp()
                for i in range(level.num_agents)
            )

            successes = send_joint_action(joint_action)
            effective_ja = tuple(
                joint_action[i] if successes[i] else NoOp()
                for i in range(level.num_agents)
            )
            current_state = current_state.result(effective_ja)

            if successes[ACTOR_AGENT_INDEX]:
                gr_current = GoalRecognitionNode(current_state, next_sg)
            else:
                gr_current = GoalRecognitionNode(current_state, gr_current.solution_graph)

        pending_indices.remove(chosen_idx)
