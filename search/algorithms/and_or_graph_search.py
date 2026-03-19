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
 
    def or_search(state, path, depth_limit):
        if goal_test(state):
            return SUCCESS
        if state in path:
            return FAILURE
        if depth_limit is not None and depth_limit == 0:
            return CUTOFF
 
        new_path = path + [state]
        any_cutoff = False
 
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
                any_cutoff = True
 
        return CUTOFF if any_cutoff else FAILURE
 
    def and_search(states, path, depth_limit):
        any_cutoff = False
 
        for outcome_state in states:
            status = or_search(outcome_state, path, depth_limit)
            if status == FAILURE:
                return FAILURE
            elif status == CUTOFF:
                any_cutoff = True
 
        return CUTOFF if any_cutoff else SUCCESS
 
    if not iterative_deepening:
        status = or_search(initial_state, [], None)
        return (0, policy) if status == SUCCESS else (None, None)
 
    for d in range(MAX_RECURSION + 1):
        policy.clear()
        status = or_search(initial_state, [], d)
 
        if status == SUCCESS:
            print_debug(f"AND-OR search found plan at depth {d}")
            return d, policy
        elif status == FAILURE:
            print_debug("AND-OR search: problem is unsolvable.")
            return None, None
 
        print_debug(f"AND-OR search: cutoff at depth {d}, trying deeper...")
 
    print_debug("AND-OR search exceeded maximum recursion depth.")
    return None, None
