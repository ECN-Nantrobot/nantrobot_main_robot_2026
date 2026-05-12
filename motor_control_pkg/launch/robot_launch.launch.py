from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    debug_terminal = LaunchConfiguration('esp32_debug_terminal')
    debug_terminal_prefix = LaunchConfiguration('esp32_debug_terminal_prefix')
    serial_trace = LaunchConfiguration('esp32_serial_trace')

    return LaunchDescription([
        DeclareLaunchArgument(
            'esp32_debug_terminal',
            default_value='false',
            description='Run control_gateway in a dedicated xterm terminal.'
        ),
        DeclareLaunchArgument(
            'esp32_serial_trace',
            default_value='false',
            description='Print all serial traffic between ROS and ESP32.'
        ),
        DeclareLaunchArgument(
            'esp32_debug_terminal_prefix',
            default_value='x-terminal-emulator -T control_gateway_debug -e',
            description='Terminal prefix used when esp32_debug_terminal is enabled.'
        ),

        # Unified control gateway and task action servers.
        Node(
            package='motor_control_pkg',
            executable='control_gateway',
            name='control_gateway',
            output='screen',
            parameters=[{'serial_trace': serial_trace}],
            condition=UnlessCondition(debug_terminal)
        ),
        Node(
            package='motor_control_pkg',
            executable='control_gateway',
            name='control_gateway',
            output='screen',
            parameters=[{'serial_trace': serial_trace}],
            prefix=debug_terminal_prefix,
            condition=IfCondition(debug_terminal)
        ),

        # Keep simulator odometry support in software-only runs.
        Node(
            package='motor_control_pkg',
            executable='interface_node',
            name='odom_node',
            output='screen'
        ),
        Node(
            package='motor_control_pkg',
            executable='odom_node_sim',
            name='odom_sim',
            output='screen'
        )
    ])
