#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import serial
from lidar_pkg.msg import ObstacleStatus

class VelocityService(Node):
    def __init__(self):
        super().__init__('vel_node')

        self.arduino_port = '/dev/ttyUSB1' 
        self.baud_rate = 115200
        self.last_velocity_sent = None

        try:
            self.arduino = serial.Serial(self.arduino_port, self.baud_rate, timeout=1)
            # Give it a tiny bit of time to initialize
            import time
            time.sleep(2) 
            self.get_logger().info(f"Connected to Arduino on {self.arduino_port}")
        except Exception as e:
            self.get_logger().error(f"FATAL: Could not open serial port {self.arduino_port}: {e}")
            self.arduino = None

        self.vel_subscriber = self.create_subscription(ObstacleStatus, "max_speed", self.vel_callback, 10)

    
    def vel_callback(self, msg: ObstacleStatus):
            """Processes incoming obstacle status and updates Arduino if velocity changed."""
            new_vel = msg.velocity

            # self.get_logger().info(f"Velocity read: {msg.velocity} | actual velocity: {self.last_velocity_sent}")
            # self.send_arduino(f"MESSAGE RECEIVED\n")
            
            if new_vel != self.last_velocity_sent:
                self.send_arduino(str(new_vel))
                self.last_velocity_sent = new_vel

            while self.arduino and self.arduino.in_waiting > 0:
                try:
                    # Read one line at a time
                    raw_line = self.arduino.readline()
                    response = raw_line.decode('utf-8').strip()
                    if response:
                        self.get_logger().info(f"ARDUINO: {response}")
                except Exception as e:
                    self.get_logger().error(f"Read error: {e}")


    def send_arduino(self, text):
        if self.arduino and self.arduino.is_open:
            try:
                self.arduino.write(text.encode('utf-8'))
                # self.get_logger().info(f"Data sent: {text.strip()}")
            except Exception as e:
                self.get_logger().error(f"SERIAL WRITE FAILED: {e}")
        else:
            self.get_logger().error("SERIAL PORT IS NOT OPEN!")

    


def main(args=None):
    rclpy.init(args=args)
    node = VelocityService()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()