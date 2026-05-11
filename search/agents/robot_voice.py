# coding: utf-8
#
# Copyright 2021 The Technical University of Denmark
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
"""
Shared voice / motion primitives for robot-driven agents.

The Whisper model, the action regex parsers, and the small Pepper-motion
helper used to be tangled together inside `search/agents/robot.py`. They
belong to anything that drives Pepper from speech, so they live here and
are imported by both `robot.py` (planning agent) and
`robot_goal_recognition.py` (Exercise 3).
"""
import math
import re
import sys
import time

from faster_whisper import WhisperModel

from search.domain.actions import Action, NoOp, Move, Push, ROBOT_ACTION_LIBRARY
from robot.robot_client import RobotClient


whisper_model = WhisperModel(
    "distil-small.en",
    device="cpu",
    compute_type="int8",
    download_root="tmp/whisper_models",
)


DIRECTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(go\s+)?(north|up|forward)\b", re.IGNORECASE),         "Move(N)"),
    (re.compile(r"\b(go\s+)?(south|down|backward|back)\b", re.IGNORECASE), "Move(S)"),
    (re.compile(r"\b(go\s+)?(east|right)\b", re.IGNORECASE),               "Move(E)"),
    (re.compile(r"\b(go\s+)?(west|left)\b", re.IGNORECASE),                "Move(W)"),
    (re.compile(r"\bpush\s+(north|up)\b", re.IGNORECASE),                  "Push(N,N)"),
    (re.compile(r"\bpush\s+(south|down)\b", re.IGNORECASE),                "Push(S,S)"),
    (re.compile(r"\bpush\s+(east|right)\b", re.IGNORECASE),                "Push(E,E)"),
    (re.compile(r"\bpush\s+(west|left)\b", re.IGNORECASE),                 "Push(W,W)"),
]


ACTION_NAME_TO_ACTION: dict[str, Action] = {
    action.name: action for action in ROBOT_ACTION_LIBRARY
}


def parse_command(text: str) -> tuple[str, str] | None:
    """Return (action_name, matched_text) or None from transcribed text."""
    for pattern, action in DIRECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            return (action, match.group(0))
    return None


def listen_and_transcribe(robot: RobotClient, duration: int = 5) -> str:
    """Have the robot listen for `duration` seconds and return the transcript."""
    time.sleep(0.5)
    robot.listen(duration=duration)

    audio_file = "tmp/test.wav"
    segments, info = whisper_model.transcribe(audio_file, beam_size=5)

    text = " ".join(segment.text.strip() for segment in segments)
    print(f"[whisper] lang={info.language} text={repr(text)}", file=sys.stderr)
    return text


def execute_action(robot: RobotClient, action_name: str, current_angle: int) -> int:
    """Turn Pepper to face the right direction and step forward. Returns the new angle."""
    if action_name.startswith("Pull"):
        raise ValueError("The robot physically cannot perform a Pull action.")
    if action_name == "NoOp":
        return current_angle

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


def listen_for_action(robot: RobotClient, max_retries: int = 3) -> Action:
    """
    Ask the human what they did, transcribe with Whisper, parse to an Action.
    Returns NoOp() if we can't understand them after `max_retries` attempts.
    """
    for attempt in range(max_retries):
        text = listen_and_transcribe(robot, duration=5)
        parsed = parse_command(text)
        if parsed is not None:
            action_name, matched = parsed
            print(f"[cmd] {action_name} (matched: '{matched}')", file=sys.stderr)
            action = ACTION_NAME_TO_ACTION.get(action_name)
            if action is not None:
                return action
        if attempt < max_retries - 1:
            robot.say("Sorry, I did not catch that. Please repeat.")
    robot.say("I will assume you stayed put.")
    return NoOp()
