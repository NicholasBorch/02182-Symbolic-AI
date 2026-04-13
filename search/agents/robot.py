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
import re
import sys
import time

from faster_whisper import WhisperModel
from search.algorithms.graph_search import graph_search
from search.domain import Level, ActionLibrary
from search.domain.goal_description import GoalDescription
from search.frontiers import Frontier
from robot.robot_client import RobotClient
from search.domain.actions import ROBOT_ACTION_LIBRARY

HUMAN = False

whisper_model = WhisperModel(
    "distil-small.en",
    device="cpu",
    compute_type="int8",
    download_root="tmp/whisper_models",
)

SOLVE_PATTERNS = [
    (re.compile(r"\bfirst\b", re.IGNORECASE), 'A'),
    (re.compile(r"\bsecond\b", re.IGNORECASE), 'B'),
]

DIRECTION_PATTERNS = [
    (re.compile(r"\b(go\s+)?(north|up|forward)\b", re.IGNORECASE),    "Move(N)"),
    (re.compile(r"\b(go\s+)?(south|down|backward|back)\b", re.IGNORECASE), "Move(S)"),
    (re.compile(r"\b(go\s+)?(east|right)\b", re.IGNORECASE),          "Move(E)"),
    (re.compile(r"\b(go\s+)?(west|left)\b", re.IGNORECASE),           "Move(W)"),
    (re.compile(r"\bpush\s+(north|up)\b", re.IGNORECASE),    "Push(N,N)"),
    (re.compile(r"\bpush\s+(south|down)\b", re.IGNORECASE),  "Push(S,S)"),
    (re.compile(r"\bpush\s+(east|right)\b", re.IGNORECASE),  "Push(E,E)"),
    (re.compile(r"\bpush\s+(west|left)\b", re.IGNORECASE),   "Push(W,W)"),
]

def parse_solve_command(text: str) -> str | None:
    """Return box character ('A' or 'B') or None."""
    for pattern, box_char in SOLVE_PATTERNS:
        if pattern.search(text):
            return box_char
    return None


def parse_command(text: str) -> tuple[str, str] | None:
    """Return (action_name, matched_text) or None from transcribed text."""
    for pattern, action in DIRECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return (action, match.group(0))
    return None


def execute_action(robot: RobotClient, action_name: str, current_angle: int) -> int:
    """Turn Pepper to face the correct direction and move forward. Returns the new angle."""
    if action_name.startswith("Pull"):
        raise ValueError("The robot physically cannot perform a Pull action.")

    robot.declare_direction(action_name)
    target_angle = robot.direction_mapping[action_name]
    angle_difference = (target_angle - current_angle) % 360

    if angle_difference != 0:
        if angle_difference <= 180:
            robot.turn_counter_clockwise(math.radians(angle_difference))
        else:
            robot.turn_clockwise(math.radians(360 - angle_difference))

    if action_name.startswith("Push"):
        robot.forward(0.75)
        robot.backward(0.2)
    else:
        robot.forward(0.55)
    return target_angle


def listen_and_transcribe(robot: RobotClient, duration: int = 2) -> str:
    time.sleep(0.5)
    robot.listen(duration=duration)

    audio_file = "tmp/test.wav"
    segments, info = whisper_model.transcribe(audio_file, beam_size=5)

    text = " ".join(segment.text.strip() for segment in segments)
    print(f"[whisper] lang={info.language} text={repr(text)}", file=sys.stderr)
    return text

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
    if not HUMAN:
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
    
    # Initialize the robot client
    robot = RobotClient(robot_ip, vision=True)
    current_angle = 0
    current_state = initial_state

    if HUMAN:
        while True:
            robot.say("What do you want me to do?")
            robot.say("I am listening")
            transcribed_text = listen_and_transcribe(robot, duration=5)

            # Check for "solve A" / "solve B" commands
            box_char = parse_solve_command(transcribed_text)
            print(f"[parse] heard={repr(transcribed_text)} solve={box_char}", file=sys.stderr)
            if box_char is not None:
                box_goals = [g for g in goal_description.goals if g[1] == box_char]
                box_goal_description = GoalDescription(level, box_goals)
                robot.say(f"Solving for box {box_char}")
                success, plan = graph_search(current_state, action_set, box_goal_description, frontier)
                if not success:
                    robot.say(f"Could not find a solution for box {box_char}.")
                else:
                    for joint_action in plan:
                        action_name = joint_action[0].name
                        if action_name == "NoOp":
                            continue
                        current_angle = execute_action(robot, action_name, current_angle)
                    current_state = current_state.result_of_plan(plan)
                    robot.say("Done")
                continue

            # Check for manual direction commands
            command = parse_command(transcribed_text)
            if command is None:
                robot.say("Sorry, I did not understand that.")
            else:
                action_name, matched = command
                print(f"[cmd] {action_name} (matched: '{matched}')", file=sys.stderr)
                robot.say(f"Okay, I will go {matched}")
                current_angle = execute_action(robot, action_name, current_angle)

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
    
