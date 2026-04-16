#!/usr/bin/env python3

import rclpy
from rclpy.action import ActionServer
from rclpy.action.server import ServerGoalHandle
from rclpy.node import Node

from nantrobot_interfaces.action import GpioWrite
from . import gpio_emulator_backend as backend


class GpioWriteActionServerEmulator(Node):

    def __init__(self):
        super().__init__('gpio_write_action_server_emulator')
        backend.initialize_state()
        self._action_server = ActionServer(
            self,
            GpioWrite,
            'gpio_write',
            self.execute_callback,
        )

    def execute_callback(self, goal_handle: ServerGoalHandle):
        pin = int(goal_handle.request.pin)
        requested_state = bool(goal_handle.request.state)

        # Writing through this action configures the pin as output and applies the value.
        backend.set_pin_mode(pin, 'output')
        backend.set_pin_state(pin, requested_state)
        pin_state = backend.get_pin_state(pin)

        self.get_logger().debug(
            f'Writing emulated GPIO pin {pin} | mode={pin_state["mode"]} | value={pin_state["state"]}'
        )

        result = GpioWrite.Result()
        result.value = bool(pin_state['state'])
        goal_handle.succeed()
        return result


def main(args=None):
    rclpy.init(args=args)
    node = GpioWriteActionServerEmulator()
    rclpy.spin(node)


if __name__ == '__main__':
    main()
