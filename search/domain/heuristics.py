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
from typing import Protocol

from search.domain.goal_description import GoalDescription
from search.domain.state import State
from search.domain.level import Level, Position


# Used for typing
class Heuristic(Protocol):
    def preprocess(self, level: Level) -> None:
        ...

    def h(self, state: State, goal_description: GoalDescription) -> int:
        ...


class GoalCountHeuristic:
    def __init__(self):
        pass

    def preprocess(self, level: Level):
        # This function will be called a single time prior to the search allowing us to preprocess the level such as
        # pre-computing lookup tables or other acceleration structures
        pass

    def h(self, state: State, goal_description: GoalDescription) -> int:
        # Your code goes here...
        # Count unsatisfied agent goal literals
        #import sys
        #print("State:", state.agent_positions, file=sys.stderr, flush=True)
        
        count = 0
        for pos, char, is_positive in goal_description.agent_goals:
            _, obj = state.object_at(pos)
            if is_positive:
                if obj != char:
                    count += 1
            else:
                if obj == char:
                    count += 1
        #print("Count:", count, file=sys.stderr, flush=True)
        return count


class AdvancedHeuristic:
    def __init__(self):
        raise NotImplementedError("Implement initialization")

    def preprocess(self, level: Level):
        # This function will be called a single time prior to the search allowing us to preprocess the level such as
        # pre-computing lookup tables or other acceleration structures
        raise NotImplementedError("Implement preprocessing logic")


    def h(self, state: State, goal_description: GoalDescription) -> int:
        # Your heuristic goes here...
        raise NotImplementedError("Implement heuristic")
