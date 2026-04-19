#!/usr/bin/env python3

import importlib.util
from typing import Any

from launch import LaunchDescription
from launch.action import Action
from launch.actions import LogInfo, OpaqueFunction
from launch.launch_context import LaunchContext
from launch_ros.actions import Node


def _launch_gpio_stack(_context: LaunchContext, *_args: Any, **_kwargs: Any) -> list[Action]:
    gpiozero_available = importlib.util.find_spec('gpiozero') is not None

    if gpiozero_available:
        return [
            LogInfo(msg='gpiozero detected: launching standard GPIO action servers.'),
            Node(
                package='nantrobot_gpio',
                executable='gpio_read_action_server',
                name='gpio_read_action_server',
                output='screen',
            ),
            Node(
                package='nantrobot_gpio',
                executable='gpio_write_action_server',
                name='gpio_write_action_server',
                output='screen',
            ),
        ]

    return [
        LogInfo(msg='gpiozero not available: launching GPIO emulator stack.'),
        Node(
            package='nantrobot_gpio',
            executable='gpio_read_action_server_emulator',
            name='gpio_read_action_server_emulator',
            output='screen',
        ),
        Node(
            package='nantrobot_gpio',
            executable='gpio_write_action_server_emulator',
            name='gpio_write_action_server_emulator',
            output='screen',
        ),
        Node(
            package='nantrobot_gpio',
            executable='gpio_emulator_ui',
            name='gpio_emulator_ui',
            output='screen',
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        OpaqueFunction(function=_launch_gpio_stack),
    ])
