import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, ActionClient
from geometry_msgs.msg import Twist
from example_interfaces.action import Fibonacci 
import serial
import time
import os
import threading
from nav_msgs.msg import Odometry 


class RobotInterfaceNode(Node):
    def __init__(self):
        super().__init__('robot_interface_node')
        
        # 1. Serial setup
        try:
            self.arduino = serial.Serial('/tmp/ttyV0', 115200, timeout=1)
            self.get_logger().info("Connected to Virtual Serial /tmp/ttyV0")
        except Exception as e:
            self.get_logger().error(f"Serial Error: {e}")

        # 2. Velocity State and Publisher
        self.vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.current_linear_vel = 0.0
        self.current_angular_vel = 0.0

        self.current_x = 0.0
        self.current_y = 0.0

        # 3. Action Server
        self._action_server = ActionServer(self, Fibonacci, 'robot_task', self.execute_callback)
        
        self.subscription = self.create_subscription(Odometry, '/odom', self.listener_odom, 10)

        # 4. Start Menu Thread
        self.menu_thread = threading.Thread(target=self.menu_loop, daemon=True)
        self.menu_thread.start()

        self._move_client = ActionClient(self, Fibonacci, 'navigate_to_goal')
        
        self.get_logger().info("Action Server & CLI Menu Ready.")

    def listener_odom(self, msg):
        """Updates the robot's current position from the /odom topic"""
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

    def menu_loop(self):
        """Interactive Terminal Menu"""
        while rclpy.ok():
            os.system('clear' if os.name != 'nt' else 'clear')
            print("====================================")
            print(f"    ROBOT INTERFACE CONTROL")
            print(f"    Lin Vel: {self.current_linear_vel} | Ang Vel: {self.current_angular_vel}")
            print(f"    X pos: {self.current_x} | Y pos: {self.current_y}")
            print("====================================")
            print(" A - PICK UP")
            print(" B - DROP")
            print(" C - CHANGE LINEAR VELOCITY")
            print(" D - CHANGE ANGULAR VELOCITY")
            print(" E - CHANGE LINEAR AND ANGULAR VELOCITY")
            print(" F - SELECT GOAL")
            print(" Q - QUIT")
            print("====================================")
            
            user_input = input("\nSelect Action: ").upper()

            if user_input == 'C':
                try:
                    val = float(input("Enter new linear velocity (m/s): "))
                    self.update_velocities(linear=val)
                except ValueError:
                    print("Invalid input.")
                    time.sleep(1)

            elif user_input == 'D':
                try:
                    val = float(input("Enter new angular velocity (rad/s): "))
                    self.update_velocities(angular=val)
                except ValueError:
                    print("Invalid input.")
                    time.sleep(1)

            elif user_input == 'E':
                try:
                    val1 = float(input("Enter new linear velocity (m/s): "))
                    val2 = float(input("Enter new angular velocity (rad/s): "))
                    self.update_velocities(linear=val1, angular=val2)
                except ValueError:
                    print("Invalid input.")
                    time.sleep(1)
            
            elif user_input == 'F':
                try:
                    val1 = float(input("Enter x coordinate (e.g. 1.2): "))
                    val2 = float(input("Enter y coordinate (e.g. 3.4): "))
                    
                    # Encoding: Convert 1.23 to 123.
                    # We use 1000 as a multiplier to allow 3 decimal places.
                    # Formula: (X * 100000) + (Y * 100) -> 120340
                    # Simplest way: (X * 100) and (Y * 100) then concatenate
                    
                    packed_x = int(val1 * 100) # 1.23 -> 123
                    packed_y = int(val2 * 100) # 3.45 -> 345
                    
                    # Combine into one integer: XXXXYYYY
                    # We multiply x by 10000 to move it to the left side of the integer
                    encoded_goal = (packed_x * 10000) + packed_y
                    
                    self.send_navigation_goal(encoded_goal)
                except ValueError:
                    print("Invalid input. Please enter numbers.")


            elif user_input == 'A':
                self.trigger_arduino_logic(1)
                time.sleep(2)
            elif user_input == 'B':
                self.trigger_arduino_logic(2)
                time.sleep(2)
            elif user_input == 'Q':
                os._exit(0)
    
    def send_navigation_goal(self, val):
        self.get_logger().info("Checking for server...")
        if not self._move_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error("Move Action Server not available!")
            return
        goal_msg = Fibonacci.Goal()
        goal_msg.order = val  # Sending our "packed" coordinates
        self._move_client.send_goal_async(goal_msg)
    

    def update_velocities(self, linear=None, angular=None):
        """Updates internal state and publishes the combined Twist message"""
        if linear is not None:
            self.current_linear_vel = linear
        if angular is not None:
            self.current_angular_vel = angular

        msg = Twist()
        msg.linear.x = self.current_linear_vel
        msg.angular.z = self.current_angular_vel
        
        self.vel_pub.publish(msg)
        self.get_logger().info(f"Published: Lin={msg.linear.x}, Ang={msg.angular.z}")

    def trigger_arduino_logic(self, action_id):
        if self.arduino and self.arduino.is_open:
            cmd = f"TASK:{action_id}\n"
            self.arduino.write(cmd.encode('utf-8'))

    async def execute_callback(self, goal_handle):
        action_id = goal_handle.request.order
        self.trigger_arduino_logic(action_id)
        goal_handle.publish_feedback(Fibonacci.Feedback(sequence=[action_id]))
        time.sleep(2)
        goal_handle.succeed()
        return Fibonacci.Result(sequence=[action_id])

def main(args=None):
    rclpy.init(args=args)
    node = RobotInterfaceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()