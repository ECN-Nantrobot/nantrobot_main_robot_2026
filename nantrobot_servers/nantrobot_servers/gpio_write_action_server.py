#!/usr/bin/env python3

import rclpy
from rclpy.action import ActionServer
from rclpy.action.server import ServerGoalHandle
from rclpy.node import Node
import gpiozero

from nantrobot_interfaces.action import GpioWrite


class GpioWriteActionServer(Node):

    def __init__(self):
        super().__init__('gpio_write_action_server')
        self._action_server = ActionServer(
            self,
            GpioWrite,
            'gpio_write',
            self.execute_callback)

    def execute_callback(self, goal_handle: ServerGoalHandle):
        self.get_logger().info('Executing goal...')
        pin = goal_handle.request.pin
        state = goal_handle.request.state
        self.get_logger().info(f'Writing GPIO pin: {pin}')
        led = gpiozero.LED(pin)

        if state:
            led.on()
        else:
            led.off()

        result = GpioWrite.Result()

        result.value = led.is_lit
        goal_handle.succeed()
        return result


def main(args=None):
    rclpy.init(args=args)

    gpio_write_action_server = GpioWriteActionServer()

    rclpy.spin(gpio_write_action_server)


if __name__ == '__main__':
    main()