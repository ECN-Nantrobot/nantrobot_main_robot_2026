#!/usr/bin/env python3

import rclpy
from rclpy.action import ActionServer
from rclpy.action.server import ServerGoalHandle
from rclpy.node import Node

from nantrobot_interfaces.action import GpioRead
from . import gpio_emulator_backend as backend


class GpioReadActionServerEmulator(Node):

    def __init__(self):
        super().__init__('gpio_read_action_server_emulator')
        backend.initialize_state()
        self._action_server = ActionServer(
            self,
            GpioRead,
            'gpio_read',
            self.execute_callback,
        )

    def execute_callback(self, goal_handle: ServerGoalHandle):
        pin = int(goal_handle.request.pin)
        pin_state = backend.get_pin_state(pin)

        self.get_logger().info(
            f'Reading emulated GPIO pin {pin} | mode={pin_state["mode"]} | value={pin_state["state"]}'
        )

        result = GpioRead.Result()
        result.value = bool(pin_state['state'])
        goal_handle.succeed()
        return result


def main(args=None):
    rclpy.init(args=args)
    node = GpioReadActionServerEmulator()
    rclpy.spin(node)


if __name__ == '__main__':
    main()
