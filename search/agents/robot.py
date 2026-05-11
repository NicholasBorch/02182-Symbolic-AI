# coding: utf-8
#
# Copyright 2021 The Technical University of Denmark
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
"""
Planning-driven robot agent (MAvis2).

The agent computes a centralised plan offline with `graph_search` and then
forwards each action to the physical Pepper robot. Voice / goal-recognition
flows live in `robot_voice.py` and `robot_goal_recognition.py` respectively.

Usage:
    python client.py --level levels/SAsoko1_04.lvl robot --ip 192.168.1.103
"""
from search.algorithms.graph_search import graph_search
from search.domain import Level, ActionLibrary
from search.frontiers import Frontier
from search.domain.actions import ROBOT_ACTION_LIBRARY

from robot.robot_client import RobotClient
from search.agents.robot_voice import execute_action


def robot_agent(
    level: Level,
    action_library: ActionLibrary,
    frontier: Frontier,
    robot_ip: str,
):
    initial_state = level.initial_state()
    goal_description = level.goal_description()

    action_library = ROBOT_ACTION_LIBRARY
    action_set = [action_library] * level.num_agents

    success, plan = graph_search(
        initial_state, action_set, goal_description, frontier
    )
    print(plan)
    if not success:
        print("Failed to find a solution to the level.")
        return

    robot = RobotClient(robot_ip, vision=True)
    current_angle = 0

    try:
        for joint_action in plan:
            action_name = joint_action[0].name
            if action_name == "NoOp":
                robot.stand()
                continue
            current_angle = execute_action(robot, action_name, current_angle)
    except Exception as e:
        print("Robot agent terminated with error", e)
        robot.shutdown()
        raise

    robot.shutdown()
