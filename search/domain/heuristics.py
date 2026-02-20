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
    MODE = "manhattan" # toggle between "manhattan" and "bfs" distance

    def __init__(self):
        self.distance_map : dict[str, dict[Position, int]] = {}
        self._walkable: dict[Position, bool] = {}
        self._rows = 0
        self._cols = 0
        # raise NotImplementedError("Implement initialization")

    def preprocess(self, level: Level):
        self.distance_map = {}
        self._walkable = {}
        # This function will be called a single time prior to the search allowing us to preprocess the level such as
        # pre-computing l$ookup tables or other acceleration structures
        """
        level.walls is a 2D list of walls and open spaces. Coordinates are in (row, column), and not counting the walls
        Grid example:
        (Wall) (Wall) (Wall) (Wall) (Wall)
        (Wall) (1, 1) (1, 2) (1, 3) (Wall)
        (Wall) (2, 1) (2, 2) (2, 3) (Wall)
        (Wall) (3, 1) (3, 2) (3, 3) (Wall)
        (Wall) (Wall) (Wall) (Wall) (Wall)
        """
        # Create grid and remove the walls
        grid = np.array(level.walls) 
        borderless_rows, border_less_columns = grid[1:-1, 1:-1].shape
        self._rows = borderless_rows
        self._cols = border_less_columns
        
        game_grid = {}
        for row in range(1, borderless_rows+1):
            for columns in range(1, border_less_columns+1):
                game_grid[(row, columns)] = "wall"
                                
        goal_positions = {}
        for position, agent, _ in level.agent_goals:
            goal_positions[agent] = position
            self.distance_map[agent] = {}

        if self.MODE == "manhattan":
            for agent in goal_positions.keys():   
                for coordinate in game_grid.keys():
                    distance = self._manhatten_distance(coordinate, goal_positions[agent])
                    self.distance_map[agent][coordinate] = distance

        elif self.MODE == "bfs":

            interior_grid = grid[1:-1, 1:-1]
            for row in range(1, borderless_rows+1):
                for columns in range(1, border_less_columns+1):
                    cell = interior_grid[row-1, columns-1]
                    self._walkable[(row, columns)] = (cell != '+')

            for agent, goal_position in goal_positions.items():
                self.distance_map[agent] = self._bfs_distance(goal_position)


    def h(self, state: State, goal_description: GoalDescription) -> int:
        agent_positions : dict[str, Position] = {}
        for position, agent in state.agent_positions:
            agent_positions[agent] = position
        
        total_distance = 0
        for agent, position in agent_positions.items():
            if agent not in self.distance_map:
                continue
            if self.MODE == "bfs":
                total_distance += self.distance_map[agent].get(position, 10**9)
            else:
                total_distance += self.distance_map[agent][position]
        
        return total_distance


    def _manhatten_distance(self, agent_position: Position, goal_position: Position) -> int:
        """Computes the manhatten distance between the agent and the goal"""
        return abs(agent_position[0] - goal_position[0]) + abs(agent_position[1] - goal_position[1])
    

    def _bfs_distance(self, goal_position: Position) -> dict[Position, int]:
        qeue = deque([goal_position])
        distance = {goal_position: 0}

        while qeue:
            row, column = qeue.popleft()
            d = distance[(row, column)]

            for next_row, next_column in ((row+1, column), (row-1, column), (row, column+1), (row, column-1)):
                if (next_row, next_column) in distance:
                    continue
                if next_row < 1 or next_row > self._rows or next_column < 1 or next_column > self._cols:
                    continue
                if not self._walkable.get((next_row, next_column), False):
                    continue

                distance[(next_row, next_column)] = d + 1
                qeue.append((next_row, next_column))

        return distance