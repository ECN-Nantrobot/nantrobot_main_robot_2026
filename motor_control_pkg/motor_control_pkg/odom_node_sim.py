import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math
from nantrobot_interfaces.srv import SetString


class OdomSim(Node):
    def __init__(self):
        super().__init__('odom_sim')

        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.odom_srv = self.create_service(
            SetString,
            'set_odom_action',
            self.set_odom_action_callback,
        )
        
        # Initialize Pose
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        

    def set_odom_action_callback(self, request, response):
        try:
            self.get_logger().info(f"{request.string}")
            self.update_odometry_after_action_complete(request.string)
            response.success = True
            self.publish_odometry(self.get_clock().now())
        except (AttributeError, ValueError) as exc:
            self.get_logger().warn(f'Invalid odom action "{request.string}": {exc}')
            response.success = False
        return response
    
    def update_odometry_after_action_complete(self, msg):
        action, distance, angle = msg.split('-', 2)
        distance = float(distance)
        angle = float(angle)
        if action.strip() != '3':
            return
        
        angle_rad = math.radians(angle)
        self.th = math.atan2(math.sin(self.th), math.cos(self.th))  # Between -pi and pi 

        self.th += angle_rad
        self.x += distance * math.cos(self.th)
        self.y += distance * math.sin(self.th)

        self.publish_odom()
        

    def publish_odom(self):
        odom = Odometry()
        current_time = self.get_clock().now()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = "odom"

        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = math.sin(self.th / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.th / 2.0)


        self.odom_pub.publish(odom)



    def update_odometry(self):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time

        if dt <= 0.0:
            self.publish_odometry(current_time)
            return

        dist = self.linear_v * dt
        dth = self.angular_v * dt
        if abs(dth) < 1e-9:
            self.x += dist * math.cos(self.th)
            self.y += dist * math.sin(self.th)
        else:
            radius = dist / dth
            new_th = self.th + dth
            self.x += radius * (math.sin(new_th) - math.sin(self.th))
            self.y -= radius * (math.cos(new_th) - math.cos(self.th))
            self.th = new_th
        self.th = math.atan2(math.sin(self.th), math.cos(self.th))

        self.publish_odometry(current_time)

    def publish_odometry(self, current_time):
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"

        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = math.sin(self.th / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.th / 2.0)

        # odom.twist.twist.linear.x = self.linear_v
        # odom.twist.twist.angular.z = self.angular_v

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
