#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from lidar_pkg.msg import ObstacleStatus
import math

class LidarNode(Node):
    ranges = []
    min_dist = 0.5      #in meters
    fov = math.pi/2


    def __init__(self):
        super().__init__("lidar")
        self.lidar_subscriber = self.create_subscription(LaserScan, "scan", self.callback_lidar_subscriber, 10)
        self.operation_timer = self.create_timer(1.0, self.main_loop)
        self.velocity_publisher = self.create_publisher(ObstacleStatus, "max_speed", 10)

    def callback_lidar_subscriber(self, msg:LaserScan):
        self.ranges = list(msg.ranges)

    def main_loop(self):
        max_range = 3.0   # The length of the playing board

        if self.ranges == []:
            pass     
        else: 
            ranges = self.ranges
            for index, value in enumerate(ranges):
                if value > max_range:
                    ranges[index] = max_range

            closest_obstacle_dist = min(ranges)

            if closest_obstacle_dist <= self.min_dist:
                velocity = 0.0
            else:
                velocity = (closest_obstacle_dist - self.min_dist)/(max_range - self.min_dist)
            
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