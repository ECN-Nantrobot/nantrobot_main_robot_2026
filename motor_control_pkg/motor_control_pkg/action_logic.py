import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial

class MotorDriver(Node):
    def __init__(self):
        
        self.arduino = serial.Serial('/tmp/ttyV0', 115200, timeout=1) 
        self.get_logger().info('Action Node started, connected to /tmp/ttyV0')



    def send_action():
        pass

def main(args=None):
    rclpy.init(args=args)
    node = MotorDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()