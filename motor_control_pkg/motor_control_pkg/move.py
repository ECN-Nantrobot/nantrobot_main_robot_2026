import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.action import CancelResponse
from geometry_msgs.msg import Twist
import math
import time
from nantrobot_interfaces.action import RobotMove
from nav_msgs.msg import Odometry

from rclpy.executors import MultiThreadedExecutor

class MoveActionServer(Node):
    def __init__(self):
        super().__init__('move_action_server')
        self._action_server = ActionServer(
            self,
            RobotMove,
            'navigate_to_goal',
            execute_callback=self.execute_callback,
            cancel_callback=self.cancel_callback,
        )
        self.vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0

    def odom_callback(self, msg):
        """Updates the robot's current position from the /odom topic"""
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        
        # Convert Quaternion to Yaw (Rotation around Z)
        q = msg.pose.pose.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)

    def cancel_callback(self, _cancel_request):
        return CancelResponse.ACCEPT

    def _safe_stop(self):
        # Avoid publishing while shutting down; this can happen on Ctrl+C.
        if not rclpy.ok():
            return
        try:
            self.vel_pub.publish(Twist())
        except Exception:
            pass

    async def execute_callback(self, goal_handle):
        target_x = goal_handle.request.target_x
        target_y = goal_handle.request.target_y

        feedback_msg = RobotMove.Feedback()

        vel_msg = Twist()
        goal_reached = False

        abs_target_x = self.current_x + target_x
        abs_target_y = self.current_y + target_y

        while rclpy.ok():
            if goal_handle.is_cancel_requested:
                self._safe_stop()
                result = RobotMove.Result()
                result.success = False
                goal_handle.canceled()
                return result

            # Goal is relative to current pose at acceptance time.
            dist_x = abs_target_x - self.current_x
            dist_y = abs_target_y - self.current_y
            
            remaining_distance = math.sqrt(dist_x**2 + dist_y**2)

            # Give feedback to the action client (i.e. the behavior tree)
            feedback_msg.current_x = self.current_x
            feedback_msg.current_y = self.current_y
            feedback_msg.remaining_distance = remaining_distance
            goal_handle.publish_feedback(feedback_msg)
            
            # Angle to the goal point
            goal_angle = math.atan2(dist_y, dist_x)
            # Difference between where we face and where we want to go
            angle_error = goal_angle - self.current_yaw
            
            # Normalize angle to [-pi, pi]
            angle_error = math.atan2(math.sin(angle_error), math.cos(angle_error))

            if remaining_distance < 0.05:
                goal_reached = True
                break # Goal reached!

            # 2. Movement Logic (Proportional control is better for real robots)
            if abs(angle_error) > 0.1:
                vel_msg.linear.x = 0.0
                vel_msg.angular.z = 0.4 if angle_error > 0 else -0.4
            else:
                vel_msg.linear.x = 0.2
                vel_msg.angular.z = 0.0

            try:
                self.vel_pub.publish(vel_msg)
            except Exception:
                break

            time.sleep(0.1)

        self._safe_stop()

        if not goal_reached:
            result = RobotMove.Result()
            result.success = False
            if rclpy.ok():
                try:
                    goal_handle.abort()
                except Exception:
                    pass
            return result

        # End the action with success
        result = RobotMove.Result()
        result.success = True
        goal_handle.succeed()
        return result
    
def main(args=None):
    rclpy.init(args=args)
    node = MoveActionServer()
    
    # Use a MultiThreadedExecutor so the Action and Odom can run in parallel
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    
    try:
        executor.spin() 
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
