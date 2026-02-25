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
import numpy as np
from typing import Protocol

from search.domain.goal_description import GoalDescription
from search.domain.state import State
from search.domain.level import Level, Position

from collections import deque


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
        USE_BOX_GOALS = True   # <-- Toggle here (True = boxes, False = agents)

        count = 0

        if USE_BOX_GOALS:
            # Count unsatisfied BOX goal literals
            for pos, char, is_positive in goal_description.box_goals:
                _, obj = state.object_at(pos)

                if is_positive:
                    if obj != char:
                        count += 1
                else:
                    if obj == char:
                        count += 1
        else:
            # Count unsatisfied AGENT goal literals (original version)
            for pos, char, is_positive in goal_description.agent_goals:
                _, obj = state.object_at(pos)

                if is_positive:
                    if obj != char:
                        count += 1
                else:
                    if obj == char:
                        count += 1

        return count


class AdvancedHeuristic:
    def __init__(self, mode: str = "manhattan"):
        self.distance_map : dict[str, dict[Position, int]] = {}
        self._rows : int
        self._cols : int
        self.mode : str = mode
        self.legal_positions : set[Position] = set()
        self.goal_positions : dict[str, Position] = {}
        self._preprocess_strategies = {
            "manhattan": self._preprocess_manhattan,
            "bfs": self._preprocess_bfs
        }

        if self.mode not in self._preprocess_strategies:
            raise ValueError(f"Unsupported heuristic mode: {mode}. Supported modes are: {list(self._preprocess_strategies.keys())}")

    def preprocess(self, level: Level):
        """This function will be called a single time prior to the search allowing us to preprocess the level such as
        pre-computing lookup tables or other acceleration structures"""

        self.legal_positions = self._get_legal_positions(level.walls)
        self.goal_positions = self._get_goal_positions(level.agent_goals)
        preprocess_function = self._preprocess_strategies.get(self.mode)
        preprocess_function(self.goal_positions)


    def h(self, state: State, goal_description: GoalDescription) -> int:
        agent_positions : dict[str, Position] = {}
        for position, agent in state.agent_positions:
            agent_positions[agent] = position
        
        total_distance = 0
        for agent, position in agent_positions.items():
            if agent not in self.distance_map:
                continue
            total_distance += self.distance_map[agent].get(position, 10**9)
        
        return total_distance
    

    def _preprocess_manhattan(self, goal_positions: dict[str, Position]):
        for agent, goal_pos in goal_positions.items():
            self.distance_map[agent] = {}
            for position in self.legal_positions:
                distance = self._manhattan_distance(position, goal_pos)
                self.distance_map[agent][position] = distance


    def _preprocess_bfs(self, goal_positions: dict[str, Position]):
        for agent, goal_position in goal_positions.items():
            self.distance_map[agent] = self._bfs_distance(goal_position)


    def _manhattan_distance(self, agent_position: Position, goal_position: Position) -> int:
        """Computes the Manhattan distance between the agent and the goal."""
        return abs(agent_position[0] - goal_position[0]) + abs(agent_position[1] - goal_position[1])
    

    def _bfs_distance(self, goal_position: Position) -> dict[Position, int]:
        """Compute shortest path distances from goal position using BFS."""
        queue = deque([goal_position])
        position_distances_from_goal : dict[Position, int] = {goal_position: 0}

        while queue:
            row, column = queue.popleft()
            position_distance = position_distances_from_goal[(row, column)]
            
            up, down, right, left = (row+1, column), (row-1, column), (row, column+1), (row, column-1)
            for next_row, next_column in (up, down, right, left):
                if (next_row, next_column) not in self.legal_positions:
                    continue
                if (next_row, next_column) in position_distances_from_goal:
                    continue
            
                position_distances_from_goal[(next_row, next_column)] = position_distance + 1
                queue.append((next_row, next_column))
                
        return position_distances_from_goal
    
    
    def _get_goal_positions(self, goal_description: GoalDescription) -> dict[str, Position]:
        goal_positions = {}
        for position, agent, _ in goal_description:
            goal_positions[agent] = position

        return goal_positions
    
    def _get_legal_positions(self, walls: list[list[bool]]) -> set[Position]:
        """"
        level.walls returns a 2D list of booleans indicating where the walls are.
        Example:
                [True, True,  True,  True,  True],
                [True, False, False, False, True],
                [True, False, True,  False, True],
                [True, False, False, False, True],
                [True, True,  True,  True,  True]
        
        Iterating through all cells and appending the row and column indices gives us a set of legal positions. 
        """
        
        legal_positions = set()
        for row_index, row in enumerate(walls):
            for col_index, cell in enumerate(row):
                if cell == False:
                    legal_positions.add(Position(row_index, col_index))

        return legal_positions