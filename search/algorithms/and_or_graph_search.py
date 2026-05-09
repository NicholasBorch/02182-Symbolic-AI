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
from typing import Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from search.agents.goal_recognition import GoalRecognitionNode

from search.domain import State
from search.domain.actions import ActionSet, JointAction
from search import print_debug

from itertools import product


type Policy = dict[State, JointAction]

type ResultsFunction[S] = Callable[[S, JointAction], list[S]]

MAX_RECURSION = 496

SUCCESS = "SUCCESS"
FAILURE = "FAILURE"
CUTOFF  = "CUTOFF"
LOOP = "LOOP" # Cyclic solutions

def and_or_graph_search(
    initial_state: State|GoalRecognitionNode,
    action_set: ActionSet,
    goal_test: Callable[[State], bool],
    results: ResultsFunction,
    iterative_deepening: bool = True,
    allow_cyclic: bool = False,
) -> tuple[int, Policy] | tuple[None, None]:
    # Here you should implement AND-OR-GRAPH-SEARCH. We are going to use a policy format, mapping from states to actions.
    # The algorithm should return a pair (worst_case_length, or_plan)
    # where the or_plan is a dictionary with states as keys and actions as values
    policy: Policy = {}

    if not iterative_deepening:
        # Memoised DFS (graph search, not tree search).
        #
        # success_memo: states proven SUCCESS regardless of path — safe to cache
        #   because a winning strategy is path-independent.
        # failure_memo: states proven FAILURE by exhausting all actions where none
        #   of those failures was caused by ancestor-cycle detection.  Cycle-induced
        #   failures are path-dependent (a state blocked because an ancestor is on the
        #   path might succeed on a different path), so we track them separately with
        #   the `any_path_induced` return flag and skip memoisation in that case.
        # path_set:  O(1) set version of the current ancestor chain for cycle detection.
        success_memo: set = set()
        failure_memo: set = set()
        path_set: set = set()
        explored_count = [0]

        def or_search_memo(state):
            # Returns (status, any_path_induced) where any_path_induced is True if
            # any FAILURE in this subtree came from ancestor-cycle detection.
            explored_count[0] += 1
            if explored_count[0] % 10000 == 0:
                print_debug(f"[AND-OR memo] explored={explored_count[0]}, success={len(success_memo)}, failure={len(failure_memo)}, path_depth={len(path_set)}")
            if goal_test(state):
                return SUCCESS, False
            if state in path_set:
                return (LOOP if allow_cyclic else FAILURE), True
            if state in success_memo:
                return SUCCESS, False
            if state in failure_memo:
                return FAILURE, False

            path_set.add(state)
            best_status = FAILURE
            any_path_induced = False

            for joint_action in product(*action_set):
                if not state.is_applicable(joint_action):
                    continue

                outcome_states = results(state, joint_action)
                status, has_pi = and_search_memo(outcome_states)

                if status == SUCCESS:
                    policy[state] = joint_action
                    success_memo.add(state)
                    path_set.discard(state)
                    return SUCCESS, False
                elif status == CUTOFF:
                    best_status = CUTOFF
                elif status == LOOP and best_status == FAILURE:
                    best_status = LOOP

                any_path_induced = any_path_induced or has_pi

            path_set.discard(state)
            # Memoize genuine failures/loops.
            # If allow_cyclic=False, LOOP is also a dead end and safe to cache.
            # Only skip memoization when a descendant failed *solely* because an
            # ancestor is on the current path — that failure may not hold on a
            # different path without that ancestor.
            is_dead_end = best_status == FAILURE or (best_status == LOOP and not allow_cyclic)
            if is_dead_end and not any_path_induced:
                failure_memo.add(state)
            return best_status, any_path_induced

        def and_search_memo(states):
            # Empty outcome set = dead end (action led nowhere).
            if not states:
                return FAILURE, False

            any_cutoff = False
            has_success = False
            any_path_induced = False

            for outcome_state in states:
                status, has_pi = or_search_memo(outcome_state)
                any_path_induced = any_path_induced or has_pi
                if status == FAILURE:
                    return FAILURE, any_path_induced
                elif status == CUTOFF:
                    any_cutoff = True
                elif status == SUCCESS:
                    has_success = True

            if any_cutoff:
                return CUTOFF, any_path_induced
            if has_success:
                return SUCCESS, any_path_induced
            return LOOP, any_path_induced

        status, _ = or_search_memo(initial_state)
        return (0, policy) if status == SUCCESS else (None, None)

    # ------------------------------------------------------------------ #
    # Original iterative-deepening implementation (unchanged).            #
    # ------------------------------------------------------------------ #
    def or_search(state, path, depth_limit):
        if goal_test(state):
            return SUCCESS
        if state in path:
            return LOOP if allow_cyclic else FAILURE
        if depth_limit is not None and depth_limit == 0:
            return CUTOFF

        new_path = path + [state]
        best_status = FAILURE

        for joint_action in product(*action_set):
            if not state.is_applicable(joint_action):
                continue

            outcome_states = results(state, joint_action)
            next_depth = None if depth_limit is None else depth_limit - 1
            status = and_search(outcome_states, new_path, next_depth)

            if status == SUCCESS:
                policy[state] = joint_action
                return SUCCESS
            elif status == CUTOFF:
                best_status = CUTOFF
            elif status == LOOP and best_status == FAILURE:
                best_status = LOOP

        return best_status

    def and_search(states, path, depth_limit):
        any_cutoff = False
        has_success = False

        for outcome_state in states:
            status = or_search(outcome_state, path, depth_limit)
            if status == FAILURE:
                return FAILURE
            elif status == CUTOFF:
                any_cutoff = True
            elif status == SUCCESS:
                has_success = True

        if any_cutoff:
            return CUTOFF
        if has_success:
            return SUCCESS
        return LOOP

    for d in range(MAX_RECURSION + 1):
        policy.clear()
        status = or_search(initial_state, [], d)

        if status == SUCCESS:
            print_debug(f"AND-OR search: Search has found plan at depth {d}!")
            return d, policy
        elif status == FAILURE:
            print_debug("AND-OR search: Search problem is not to be solved!")
            return None, None

        print_debug(f"AND-OR search: Search was cutoff at depth {d}, We will try to go deeper")

    print_debug("AND-OR search: Search has exceeded the maximum recursion depth!")
    return None, None
