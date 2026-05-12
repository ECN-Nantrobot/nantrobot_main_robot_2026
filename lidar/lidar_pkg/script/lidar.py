#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from lidar_pkg.msg import ObstacleStatus
import math
from gpiozero import LED



class LidarNode(Node):
    ranges = []
    min_dist = 0.5      #in meters
    fov = math.pi/2
    LED_GPIO_ = LED(17)
 

    on_duration = 0.5   
    off_duration = 5.0  
    is_led_on = False
    



    def __init__(self):
        super().__init__("lidar")
        self.lidar_subscriber = self.create_subscription(LaserScan, "scan", self.callback_lidar_subscriber, 10)
        self.operation_timer = self.create_timer(1.0, self.main_loop)
        self.velocity_publisher = self.create_publisher(ObstacleStatus, "max_speed", 10)
        self.timer = self.create_timer(0.05, self.blink_led)
        self.last_toggle_time = self.get_clock().now()

    def blink_led(self):

        now = self.get_clock().now()
        elapsed = (now - self.last_toggle_time).nanoseconds / 1e9

        if self.is_led_on:
            if elapsed >= self.on_duration:
                self.LED_GPIO_.off()
                self.is_led_on = False
                self.last_toggle_time = now
        else:
            if elapsed >= self.off_duration:
                self.LED_GPIO_.on()
                self.is_led_on = True
                self.last_toggle_time = now

        self.max_range = 3.0  

    def callback_lidar_subscriber(self, msg:LaserScan):
        self.ranges = list(msg.ranges)

    def main_loop(self):
         # The length of the playing board
        
        if self.ranges == []:
            pass     
        else: 
            ranges = self.ranges
            for index, value in enumerate(ranges):
                if math.isinf(value): value = self.max_range
                if value > self.max_range:
                    ranges[index] = self.max_range

            closest_obstacle_dist = min(ranges)

            if closest_obstacle_dist <= self.min_dist:
                velocity = 0.0
            else:
                velocity = (closest_obstacle_dist - self.min_dist)/(self.max_range - self.min_dist)
            
            self.get_logger().info(f"{closest_obstacle_dist=} | velocity: {velocity}")
            
            msg = ObstacleStatus()
            msg.velocity = velocity
            self.velocity_publisher.publish(msg)
        


def main(args=None):
    rclpy.init(args=args)
    node = LidarNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()