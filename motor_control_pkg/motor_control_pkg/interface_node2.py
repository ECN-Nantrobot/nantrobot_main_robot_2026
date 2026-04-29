import rclpy
from rclpy.node import Node
import serial

from nav_msgs.msg import Odometry 
import math

from rclpy.action import ActionServer
from std_msgs.msg import String
from nantrobot_interfaces.srv import SetString


class RobotInterfaceNode(Node):
    def __init__(self):
        super().__init__('robot_interface_node')
        
        try:
            self.arduino = serial.Serial('/tmp/ttyV0', 115200, timeout=1)
            self.get_logger().info("Connected to Virtual Serial /tmp/ttyV0")
        except Exception as e:
            self.get_logger().error(f"Serial Error: {e}")


        self.actions = self.upload_actions()
        self.current_action = {"action": self.actions[0], "status": "SET"}
        """
        STATUS:
            - SET
            - SENT
            - DONE
        """
        self.get_logger().info(f"{self.actions}")

        self.odom_client = self.create_client(SetString, 'set_odom_action')
        

        
        self.timer = self.create_timer(0.1, self.run_logic)
        self.get_logger().info("Action Server & CLI Menu Ready.")
    
    def upload_actions(self):
        with open("src/nantrobot_main_robot_2026/motor_control_pkg/motor_control_pkg/action_list.txt", "r") as f:
            act = f.readlines()
        
        actions = []
        for action in act:
            action = action.strip("\n")
            if action[0] == "P":
                action = "1" + action[1:]
            elif action[0] == "D":
                action = "2" + action[1:]
            elif action[0] == "M":
                action = "3" + action[1:]
            actions.append(action)
        return actions

    def listener_odom(self, msg):
        """Updates the robot's current position from the /odom topic"""
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y

    def send_action_arduino(self, action):
        if self.arduino and self.arduino.is_open:
            # Formats to: "1-0-0" for pick up or "3-2000-1" for move
            self.arduino.write(action.encode('utf-8'))


    def run_logic(self):
        
        if self.current_action["status"] == "DONE":
            # TODO: send a request to the odom node sending to it the string self.current_action["action"]
            if not self.odom_client.wait_for_service(timeout_sec=1.0):
                self.get_logger().warn('Odom service not available...')
                return

            # Create the Request object
            request = SetString.Request()
            request.string = self.current_action["action"]

            # Call asynchronously so your timer/node doesn't freeze
            self.odom_client.call_async(request)

            self.actions.pop(0)

            # Clean exit
            if self.actions == []:
                self.get_logger().info('All actions completed. Shutting down.')
                rclpy.shutdown() 
                return
            
            # Go to the next action
            self.current_action["action"] = self.actions[0] 
            self.current_action["status"] = "SET"

        elif self.current_action["status"] == "SET":
            self.send_action_arduino(self.current_action["action"])
            self.current_action["status"] = "SEND"
        
        elif self.current_action["status"] == "SEND":
            # TODO: wait for feedback completed from arduino
            # if self.arduino.in_waiting > 0:
            #     feedback = self.arduino.readline().decode('utf-8').strip()
            #     self.get_logger().info(f"Arduino says: {feedback}")

            feedback = "OK"
                
                # Only set to DONE if the Arduino confirms it's finished
            if "OK" in feedback: # Or whatever string your Arduino prints
                self.current_action["status"] = "DONE"

            self.current_action["status"] = "DONE"
        # self.get_logger().info(f'CURRENT ACTION: {self.current_action}')



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
