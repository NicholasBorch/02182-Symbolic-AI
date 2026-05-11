# coding: utf-8
#
# Copyright 2021 The Technical University of Denmark
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
"""
Exercise 3 of MAvis3: Goal recognition with the Pepper robot as helper and a
human as actor. The helper plan is computed exactly as in `goal_recognition.py`
(All-Optimal-Plans + iterative-deepening AND-OR search), but at execution time
the human announces each move via Whisper instead of being driven by an
in-process simulator.
"""
from __future__ import annotations

from search import print_debug
from search.domain import Level
from search.domain.actions import NoOp, ROBOT_ACTION_LIBRARY
from search.frontiers.frontier import Frontier

from search.algorithms.all_optimal_plans import all_optimal_plans
from search.algorithms.and_or_graph_search import and_or_graph_search

from search.agents.goal_recognition import (
    ACTOR_AGENT_INDEX,
    HELPER_AGENT_INDEX,
    DisjunctiveGoalDescription,
    GoalRecognitionNode,
    solution_graph_results,
)
from search.agents.robot_voice import execute_action, listen_for_action

from robot.robot_client import RobotClient


def robot_goal_recognition_agent(
    level: Level,
    frontier: Frontier[GoalRecognitionNode],
    robot_ip: str,
    iterative_deepening: bool = True,
    allow_cyclic: bool = False,
):
    initial_state = level.initial_state()
    goal_description = level.goal_description()

    actor_char = level.initial_agent_positions[ACTOR_AGENT_INDEX][1]
    actor_color = level.colors[actor_char]
    actor_goal = goal_description.color_filter(actor_color)

    # Robot is the helper; restrict its action set to what the physical
    # robot can actually execute (no Pull, axis-aligned Push only).
    action_set = [[NoOp()] for _ in range(level.num_agents)]
    action_set[HELPER_AGENT_INDEX] = ROBOT_ACTION_LIBRARY

    robot = RobotClient(robot_ip, vision=False)
    current_angle = 0
    current_state = initial_state
    pending_indices = list(range(actor_goal.num_sub_goals()))

    try:
        while pending_indices:
            pending_subgoals = [actor_goal.get_sub_goal(i) for i in pending_indices]
            monochrome = current_state.color_filter(actor_color)

            ok, root_sg = all_optimal_plans(
                monochrome, [ROBOT_ACTION_LIBRARY], pending_subgoals, frontier
            )
            if not ok:
                robot.say("I cannot find an optimal plan for you.")
                return

            disjunctive = DisjunctiveGoalDescription(pending_subgoals)
            gr_current = GoalRecognitionNode(current_state, root_sg)

            _, policy = and_or_graph_search(
                gr_current,
                action_set,
                disjunctive.is_goal,
                solution_graph_results,
                iterative_deepening,
                allow_cyclic,
            )
            if policy is None:
                robot.say("I cannot find a way to help.")
                return

            # Inner loop: drive one subgoal to completion.
            # The human picks which goal -- we exit when *any* pending goal is met.
            while not disjunctive.is_goal(gr_current):
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
                        robot.say("I lost track. Stopping.")
                        return

                # 1. Listen to what the human says they did.
                robot.say("Your move?")
                actor_action = listen_for_action(robot)

                # 2. Decide and perform our own move.
                helper_action = policy[gr_current][HELPER_AGENT_INDEX]
                if isinstance(helper_action, NoOp):
                    robot.say("I will wait.")
                else:
                    current_angle = execute_action(
                        robot, helper_action.name, current_angle
                    )

                # 3. Advance local state. GoalRecognitionNode.result handles
                #    inapplicable / conflicting actions per the spec.
                joint_action = tuple(
                    actor_action if i == ACTOR_AGENT_INDEX
                    else helper_action if i == HELPER_AGENT_INDEX
                    else NoOp()
                    for i in range(level.num_agents)
                )
                gr_current = gr_current.result(joint_action)
                current_state = gr_current.state

            # Drop every pending subgoal that just got satisfied.
            for idx in list(pending_indices):
                if actor_goal.get_sub_goal(idx).is_goal(current_state):
                    pending_indices.remove(idx)
                    print_debug(f"Subgoal {idx} satisfied.")

        robot.say("All goals reached. Goodbye.")
    finally:
        robot.shutdown()
