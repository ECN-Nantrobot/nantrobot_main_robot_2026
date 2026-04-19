import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Pose
from nav_msgs.msg import Odometry 
import serial
import math
import time

class OdomSim(Node):
    def __init__(self):
        super().__init__('odom_sim')
        
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.subscription = self.create_subscription(Twist, 'cmd_vel', self.listener_callback, 10)
        
        # Initialize Pose
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        
        self.linear_v = 0.0
        self.angular_v = 0.0
        self.last_time = self.get_clock().now()

        # Create a timer to publish Odom at 10Hz
        self.timer = self.create_timer(0.1, self.update_odometry)

    def listener_callback(self, msg):
        self.linear_v = msg.linear.x  
        self.angular_v = msg.angular.z
        

    def update_odometry(self):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time

        # Calculate delta displacement in robot frame
        dist = self.linear_v * dt
        dth = self.angular_v * dt

        # Update absolute pose (Dead Reckoning)
        self.x += dist * math.cos(self.th)
        self.y += dist * math.sin(self.th)
        self.th += dth

        # Create Odometry Message
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"

        # Position
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        
        # Orientation (Simplified Quaternion from Yaw)
        odom.pose.pose.orientation.z = math.sin(self.th / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.th / 2.0)

        # Twist (Current Velocity)
        odom.twist.twist.linear.x = self.linear_v
        odom.twist.twist.angular.z = self.angular_v

        self.odom_pub.publish(odom)

def main(args=None):
    rclpy.init(args=args)
    node = OdomSim()
    while True:
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()