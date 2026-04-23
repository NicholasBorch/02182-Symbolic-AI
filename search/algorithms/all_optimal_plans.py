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

import itertools
from collections import deque

from search.domain.goal_description import GoalDescription
from search.domain import State
from search.domain.actions import Action, ActionLibrary, ActionSet
from search.frontiers.frontier import Frontier
from search.algorithms.monitoring import memory_tracker, search_timer, print_search_status


try:
    import graphviz
except ImportError:
    pass


class MultiParentNode:
    """
    In order to represent the nodes of a solution graph, we need to track
    additional information beyond that contained in the State class.
    For this reason, we here provide a wrapper class you can use for your
    ALL_OPTIMAL_PLANS search.

    More precisely, it provides the following additional members:
    - parent_action_pairs: A list of Node-Action pairs containing pairs of
    parent nodes and the action taken to reach this node from the given parent node.
    - optimal_actions_and_results: A map of actions into their resulting
    MultiParentNode. Note that these actions should be the subset of all
    possible actions, which occurs on some optimal plan.
    - consistent_goals: A set of GoalDescriptions which can contain the goal
    labelling.

    The implemented methods assume that the state only contains a single agent,
    but feel free to extend this to also support the multi-agent case if you
    so desire.
    """

    id_generator = itertools.count()

    def __init__(self, state: State):
        self.state = state
        self.path_cost = state.path_cost
        self.parent_action_pairs: list[tuple[MultiParentNode, Action]] = []
        self.optimal_actions_and_results: dict[Action, MultiParentNode] = {}
        self.consistent_goals = set()
        # Only used for visualization
        self.id = next(MultiParentNode.id_generator)

    def get_applicable_actions(self, action_set: ActionSet) -> list[Action]:
        # Find all joint actions and then pick out the action of the first agent
        joint_actions = self.state.get_applicable_actions(action_set)
        actions = [joint_action[0] for joint_action in joint_actions]
        return actions

    def result(self, action: Action) -> State:
        # Pack the action into a joint action
        joint_action = [action]
        return self.state.result(joint_action)

    def get_actions_and_results_consistent_with_goal(self, goal: GoalDescription):
        # Returns a list of actions and their corresponding resulting states, which would be consistent with an
        # optimal plan to solve the specified goal.
        consistent_actions_and_results = []
        for action, node in self.optimal_actions_and_results.items():
            if goal in node.consistent_goals:
                consistent_actions_and_results.append((action, node))

        return consistent_actions_and_results

    def __eq__(self, other: MultiParentNode) -> bool:
        if isinstance(other, self.__class__):
            return self.state == other.state
        else:
            return False

    def __ne__(self, other: MultiParentNode) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.state)


def visualize_solution_graph(solution_graph: MultiParentNode, filename: str = "all_optimal_paths", output_dir: str = "tmp/all_optimal_paths") -> None:
    """
    The function allow you to visualize the found solution graph as a picture.

    Use of this function is completely optional, but some of you might find it helpful for debugging your code or
    to to gain a better understanding of the found solution.
    Given a solution graph it will create a file 'all_optimal_paths.svg' on your current path.
    Note:
        This function requires graphviz to be installed on your machine. You will need to install both the Graphviz
        engine (see https://graphviz.org/download/) and the graphviz python package (pip install graphviz).
    """

    graph = graphviz.Digraph()
    graph.format = "svg"

    visited = set()

    def visitor(subgraph: MultiParentNode):
        # Ensure we only visit each node a single time
        if subgraph in visited:
            return subgraph.id
        visited.add(subgraph)

        # Draw the node itself
        graph.node(f"{subgraph.id}", f"{subgraph.id} -> {subgraph.consistent_goals}")

        # Now recurse down into all the optimal children of the node and draw edges along the way
        for action, resulting_state in subgraph.optimal_actions_and_results.items():
            child_id = visitor(resulting_state)
            graph.edge(f"{subgraph.id}", f"{child_id}", label=f"{action}")
        return subgraph.id

    visitor(solution_graph)
    graph.render(filename , directory=output_dir)

def all_optimal_plans(
    initial_state: State,
    action_set: list[ActionLibrary],
    possible_goals: list[GoalDescription],
    frontier: Frontier[MultiParentNode],
    visualize: bool = False,
) -> tuple[bool, MultiParentNode|None]:
    """
    An implementation of the ALL_OPTIMAL_PLANS algorithm as described in the
    MAvis3 assignment description.
    - initial_state: A instance of State representing the initial
    state of the level
    - action_set: A list of possible actions
    - possible_goals: A list of goal descriptions, one of which the agent is
    trying to complete
    - frontier: A frontier
    The function should return a pair (boolean, MultiParentNode) where:
    - if the search found a solution, the boolean should be True and the
    MultiParentNode should be the root of the solution graph
    - if the search did not find a solution, the boolean should be False and
    the MultiParentNode should be None
    """
    search_timer.start()

    iterations = 0

    # Clear the parent pointer and path_cost in order make sure that the initial state is a root node
    initial_state.parent = None
    initial_state.path_cost = 0
    frontier.prepare(possible_goals)

    root = MultiParentNode(initial_state)

    frontier.add(root)

    all_nodes, goal_depths, max_depth = _build_optimal_plan_graph(
        root, action_set, possible_goals, frontier
    )

    if max_depth is None:
        return False, None

    _label_consistent_goals(all_nodes, goal_depths)

    if visualize:
        visualize_solution_graph(root)

    return True, root


def _build_optimal_plan_graph(
    root: MultiParentNode,
    action_set: ActionSet,
    possible_goals: list[GoalDescription],
    frontier: Frontier[MultiParentNode],
) -> tuple[dict[State, MultiParentNode], dict[GoalDescription, int], int | None]:
    """
    Run a modified BFS from ``root``, building a multi-parent DAG in which
    every path from the root to a node satisfying some goal is an optimal
    plan for that goal. Each generated node has its ``parent_action_pairs``
    populated, and every parent's ``optimal_actions_and_results`` is updated
    with the edges that lie on some optimal plan.

    Returns the triple ``(all_nodes, goal_depths, max_depth)`` where
    ``all_nodes`` maps each reached ``State`` to its ``MultiParentNode``,
    ``goal_depths`` maps each satisfied goal to the depth of the shallowest
    node satisfying it, and ``max_depth`` is the maximum over
    ``goal_depths.values()``. ``max_depth`` is ``None`` iff the frontier was
    exhausted before every goal could be satisfied.
    """
    all_nodes: dict[State, MultiParentNode] = {root.state: root}
    goal_depths: dict[GoalDescription, int] = {}
    remaining_goals: set[GoalDescription] = set(possible_goals)
    max_depth: int | None = None
    iterations = 0

    while not frontier.is_empty():
        if iterations % 10000 == 0 and iterations != 0:
            print_search_status(set(all_nodes.keys()), frontier)
        if memory_tracker.is_exceeded():
            raise MemoryError("Maximum memory usage exceeded!")
        iterations += 1

        node = frontier.pop()
        depth = node.path_cost

        # Past the last optimal layer nothing new can be discovered.
        if max_depth is not None and depth > max_depth:
            break

        # The first time a still-pending goal is satisfied by a popped node
        # fixes that goal's optimal depth (BFS guarantees minimality).
        for goal in [g for g in remaining_goals if g.is_goal(node.state)]:
            goal_depths[goal] = depth
            remaining_goals.remove(goal)
        if not remaining_goals and max_depth is None:
            max_depth = max(goal_depths.values()) if goal_depths else depth

        # Children of a depth==max_depth node would be at depth+1 > max_depth
        # and cannot lie on any optimal plan, so skip expansion.
        if max_depth is not None and depth >= max_depth:
            continue

        for action in node.get_applicable_actions(action_set):
            child_state = node.result(action)
            existing = all_nodes.get(child_state)
            if existing is None:
                child = MultiParentNode(child_state)
                child.parent_action_pairs.append((node, action))
                node.optimal_actions_and_results[action] = child
                all_nodes[child_state] = child
                frontier.add(child)
            elif existing.path_cost == depth + 1:
                # A second optimal path of equal length reaches this state.
                existing.parent_action_pairs.append((node, action))
                node.optimal_actions_and_results[action] = existing
            # else: existing was reached at a strictly smaller depth, so this
            # edge is not on any optimal path -- ignore it.

    return all_nodes, goal_depths, max_depth


def _label_consistent_goals(
    all_nodes: dict[State, MultiParentNode],
    goal_depths: dict[GoalDescription, int],
) -> None:
    """
    Seed every node that satisfies goal ``g`` at exactly ``goal_depths[g]``,
    then propagate labels upwards along ``parent_action_pairs`` so that every
    node on some optimal plan to ``g`` ends up with ``g`` in its
    ``consistent_goals``.
    """
    queue: deque[MultiParentNode] = deque()
    for node in all_nodes.values():
        for goal, d in goal_depths.items():
            if node.path_cost == d and goal.is_goal(node.state):
                node.consistent_goals.add(goal)
        if node.consistent_goals:
            queue.append(node)

    while queue:
        node = queue.popleft()
        for parent, _action in node.parent_action_pairs:
            new_goals = node.consistent_goals - parent.consistent_goals
            if new_goals:
                parent.consistent_goals |= new_goals
                queue.append(parent)
