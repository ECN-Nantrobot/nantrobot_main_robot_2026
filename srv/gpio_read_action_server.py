#!/usr/bin/env python3

import rclpy
from rclpy.action import ActionServer
from rclpy.action.server import ServerGoalHandle
from rclpy.node import Node
import gpiozero

from nantrobot_interfaces.action import GpioRead


class GpioReadActionServer(Node):

    def __init__(self):
        super().__init__('gpio_read_action_server')
        self._action_server = ActionServer(
            self,
            GpioRead,
            'gpio_read',
            self.execute_callback)

    def execute_callback(self, goal_handle: ServerGoalHandle):
        self.get_logger().info('Executing goal...')
        pin = goal_handle.request.pin
        button = gpiozero.Button(pin)
        self.get_logger().info(f'Reading GPIO pin: {pin} \t|value: {button.is_pressed}')

        result = GpioRead.Result()

        result.value = button.is_pressed
        goal_handle.succeed()
        return result


def main(args=None):
    rclpy.init(args=args)

    gpio_read_action_server = GpioReadActionServer()

    rclpy.spin(gpio_read_action_server)


if __name__ == '__main__':
    main()