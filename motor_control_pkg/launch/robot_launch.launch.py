from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Node 1: The Motor Driver (Subscribes to /cmd_vel)
        Node(
            package='motor_control_pkg',
            executable='motor_node',
            name='motor_driver',
            parameters=[{'port': '/tmp/ttyV0'}],
            output='screen'
        ),
        
        # Node 2: The Action Interface (CLI + Action Server)
        Node(
            package='motor_control_pkg',
            executable='interface_node',
            name='robot_interface',
            output='screen',
            # This allows the terminal to accept your A/B keyboard input
            prefix="xterm -e" 
        ),
        
        Node(
            package='motor_control_pkg',
            executable='move',
            name='move_node',
            output='screen'
        ), 

        # Odometry computation node
        Node(
            package='motor_control_pkg',
            executable='odom_node_sim',
            name='odom_node',
            output='screen'
        )
    ])