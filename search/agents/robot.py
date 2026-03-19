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
"""
Using the robot agent type differs from previous agent types.
  - First, you need to have the server running: `python2 robot_server.py`
  - Secondly, you don't need the Java server for the robot. So, the command
    to start the search client in the terminal is different, for example:
        'python client.py --level levels/SAsoko1_04.lvl robot --ip 192.168.1.103'
    runs the searchclient with the 'robot' agent type on the robot at IP 192.168.0.102.

  - To connect to the robots, connect to the Pepper hotspot.
"""
import math
import time

from search.algorithms.graph_search import graph_search
from search.domain import Level, ActionLibrary
from search.frontiers import Frontier
from robot.robot_client import RobotClient
from domain.actions import ROBOT_ACTION_LIBRARY

HUMAN = None

def robot_agent(
    level: Level,
    action_library: ActionLibrary,
    frontier: Frontier,
    robot_ip: str,
):
    # Get the initial state and goal description from the level
    initial_state = level.initial_state()
    goal_description = level.goal_description()
    
    # Create an action set where all agents can perform all actions
    action_library = ROBOT_ACTION_LIBRARY
    action_set = [action_library] * level.num_agents
    
    # Run the graph search algorithm to find a plan for the robot to execute
    success, plan = graph_search(
            initial_state, 
            action_set, 
            goal_description, 
            frontier
        )
    
    print(plan)
    if not success:
        print("Failed to find a solution to the level.")
        return None
    
    # You can delete the following line (it is used to silence the type checker)
    _ = initial_state, goal_description
    
    # Write your robot agent type here
    # What follows is a small example of how to interact with the robot.
    # You should browse through 'robot/robot_client.py' to get a full overview of all the available functionality
    
    # Initialize the robot client
    robot = RobotClient(robot_ip, vision=True)
    if HUMAN:
        # Communicate using its speech synthesis
        robot.say("Hello I am Pepper!")

        # Drive 0.2 meters forward and backwards
        robot.forward(0.2)
        robot.backward(0.2)
        
        # Turn around 30 degrees back and forth
        theta = math.radians(30)
        robot.turn_counter_clockwise(theta)
        robot.turn_clockwise(theta)
    
    try:
        current_angle = 0
        
        for joint_action in plan:
            action = joint_action[0]
            action_name = action.name
            
            if action_name == "NoOp":
                robot.stand()
                continue
            
            robot.declare_direction(action_name)
            target_angle = robot.direction_mapping[action_name]
            angle_difference = (target_angle - current_angle) % 360
            
            if angle_difference != 0:
                if angle_difference <= 180:
                    robot.turn_counter_clockwise(math.radians(angle_difference))
                else:
                    robot.turn_clockwise(math.radians(360 - angle_difference))
                current_angle = target_angle
                
            if action_name.startswith("Pull"):
                print("Can't pull")
                raise ValueError("The robot physically cannot perform a Pull action.")
            else:
                robot.forward(0.55)
                
            robot.stand()
            time.sleep(1)

    except Exception as e:
        print("Robot agent terminated with error", e)
        robot.shutdown()
        raise
    
    robot.shutdown()