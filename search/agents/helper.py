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
from search import print_debug

from search.domain import Level, Action
from search.domain.actions import Action, NoOp
from search.frontiers.frontier import Frontier
from search.algorithms.graph_search import graph_search
from search.agents.server_communication import send_joint_action




def helper_agent(
    level: Level,
    action_library: list[Action],
    frontier: Frontier,
):
    """

    """
    # Get the initial state and goal description from the level
    initial_state = level.initial_state()
    goal_description = level.goal_description()

    # Here you should implement the HELPER-AGENT algorithm.
    # Some tips are:
    # - From goal_description, you should look into color_filter and get_sub_goal to create monochrome and subgoal problems.
    # - You should handle communication with the server yourself and check successes of joint actions.
    #   Look into classic.py to see how this is done.
    # - You can create an action set where only a specific agent is allowed to move as follows:
    #   action_set = [[NoOp()]] * level.num_agents
    #   action_set[agent_index] = action_library
    # - You probably want to create a helper function for creating the set of negative obstacle subgoals.
    #   You can then create a new goal description using 'goal_description.create_new_goal_description_of_same_type'
    #   which takes a list of subgoals.
    actor_char = level.initial_agent_positions[0][1]
    actor_color = level.colors[actor_char]
    actor_goal = goal_description.color_filter(actor_color)
    
    # Initialize state
    current_state = initial_state
    
    # Process subgoals one at a time
    for i in range(actor_goal.num_sub_goals()):
        subgoal = actor_goal.get_sub_goal(i)
        
        while not subgoal.is_goal(current_state):
            # Actor plans color-blind on filtered state
            monochrome_state = current_state.color_filter(actor_color)
            success, plan = graph_search(monochrome_state, [action_library], subgoal, frontier)
            # See if success
            assert success, "Actor could not find a plan for subgoal" 
            
            # Execute plan step by step
            replanning_needed = False
            for step in plan:
                # Expand 1-agent action into joint action
                actor_action = step[0]
                joint_action = tuple(
                    actor_action if i == 0 else NoOp()
                    for i in range(level.num_agents)
                )
                
                successes = send_joint_action(joint_action)
                
                if successes[0]:
                    # Update current state
                    current_state = current_state.result(joint_action)
                else:
                    current_monochrome = current_state.color_filter(actor_color)
                    remaining_plan = plan[plan.index(step):]
                    path_positions = get_path_positions(current_monochrome, remaining_plan)
                    
                    blocking_pos, obstacle_char = find_obstacle(current_state, path_positions, actor_color, level)
                    
                    assert obstacle_char is not None, "Could not find obstacle"
                    
                    helper_index = find_helper_index(obstacle_char, level, current_state)
                    helper_char = current_state.agent_positions[helper_index][1]
                    
                    obstacle_goals = create_obstacle_goals(current_state, path_positions, actor_color, level)
                    assert len(obstacle_goals) > 0, "No obstacles found in path"
                                        
                    helper_goal = goal_description.create_new_goal_description_of_same_type(obstacle_goals)
                    
                    helper_action_set = [[NoOp()] for _ in range(level.num_agents)]
                    helper_action_set[helper_index] = action_library
                    
                    help_success, helper_plan = graph_search(current_state, helper_action_set, helper_goal, frontier)
                    assert help_success, "Helper could not clear path"
                    
                    for helper_joint_action in helper_plan:
                        send_joint_action(helper_joint_action)
                        current_state = current_state.result(helper_joint_action)
                    
                    replanning_needed = True
                    break  # Replan from new state
                
                if not replanning_needed:
                    break  # Subgoal achieved, move to next



# Helper functions
def get_path_positions(monochrome_state, remaining_plan):
    """Collect all positions the actor AND pushed boxes need to pass through"""
    positions = set()
    sim_state = monochrome_state
    for joint_action in remaining_plan:
        new_state = sim_state.result(joint_action)
        # Actor positions
        for pos, _ in new_state.agent_positions:
            positions.add(pos)
        # Box destinations - these also need to be free
        for pos, _ in new_state.box_positions:
            positions.add(pos)
        sim_state = new_state
    return positions


def find_obstacle(current_state, path_positions, actor_color, level):
    """Find the first non-actor-color object occupying a required-free position"""
    for pos in path_positions:
        _, char = current_state.object_at(pos)
        if char != '' and level.colors.get(char) != actor_color:
            return pos, char
    return None, None

def find_helper_index(obstacle_char, level, current_state):
    """Find the agent index whose color matches the obstacle"""
    obstacle_color = level.colors[obstacle_char]
    for i, (_, agent_char) in enumerate(current_state.agent_positions):
        if level.colors.get(agent_char) == obstacle_color:
            return i
    return -1

def create_obstacle_goals(current_state, path_positions, actor_color, level):
    """Only create negative goals for path positions actually occupied by helper objects"""
    obstacle_goals = []
    for pos in path_positions:
        _, char = current_state.object_at(pos)
        # Only add a goal if something non-actor-colored is actually there
        if char != '' and level.colors.get(char) != actor_color:
            obstacle_goals.append((pos, char, False))
    return obstacle_goals