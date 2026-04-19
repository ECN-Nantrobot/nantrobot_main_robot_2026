import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial

class MotorDriver(Node):
    def __init__(self):
        super().__init__('motor_driver')
        
        # Or change to '/MainRobot/cmd_vel_unstamped' based on your graph
        self.subscription = self.create_subscription(Twist, 'cmd_vel', self.listener_callback, 10)
        self.arduino = serial.Serial('/tmp/ttyV0', 115200, timeout=1) 
        self.get_logger().info('Motor Driver Node started, connected to /tmp/ttyV0')

        self.linear_v = 0
        self.angular_v = 0
        self.d = 0.2                 # Distance between wheels

    def listener_callback(self, msg):
        linear_v = msg.linear.x  
        angular_v = msg.angular.z

        
        if self.linear_v != linear_v or self.angular_v != angular_v:
            self.linear_v = linear_v 
            self.angular_v = angular_v
            left_speed = linear_v - (angular_v * self.d / 2.0)
            right_speed = linear_v + (angular_v * self.d / 2.0)
        
            command = f"Speed-{left_speed:.2f},{right_speed:.2f}\n"
            self.arduino.write(command.encode('utf-8'))
            self.get_logger().info(f'Sent to Arduino: {command.strip()}')

def main(args=None):
    rclpy.init(args=args)
    node = MotorDriver()
    while True:
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()