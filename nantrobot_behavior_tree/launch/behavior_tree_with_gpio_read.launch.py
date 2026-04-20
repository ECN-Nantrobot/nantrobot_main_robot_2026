from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    behavior_tree_start_delay = LaunchConfiguration('behavior_tree_start_delay')
    debug_terminal = LaunchConfiguration('esp32_debug_terminal')
    debug_terminal_prefix = LaunchConfiguration('esp32_debug_terminal_prefix')
    serial_port = LaunchConfiguration('esp32_serial_port')
    serial_trace = LaunchConfiguration('esp32_serial_trace')

    behavior_tree_start_delay_arg = DeclareLaunchArgument(
        'behavior_tree_start_delay',
        default_value='4.0',
        description='Delay in seconds before launching behavior_tree to let GPIO action servers start.',
    )
    debug_terminal_arg = DeclareLaunchArgument(
        'esp32_debug_terminal',
        default_value='false',
        description='Run control_gateway in a dedicated terminal.',
    )
    debug_terminal_prefix_arg = DeclareLaunchArgument(
        'esp32_debug_terminal_prefix',
        default_value='x-terminal-emulator -T control_gateway_debug -e',
        description='Terminal prefix used when esp32_debug_terminal is enabled.',
    )
    serial_port_arg = DeclareLaunchArgument(
        'esp32_serial_port',
        default_value='/dev/ttyUSB0',
        description='Serial port device used by control_gateway to communicate with ESP32.',
    )
    serial_trace_arg = DeclareLaunchArgument(
        'esp32_serial_trace',
        default_value='true',
        description='Print all serial traffic between ROS and ESP32.',
    )

    behavior_tree_node = Node(
        package='nantrobot_behavior_tree',
        executable='behavior_tree',
        name='behavior_tree',
        output='screen',
    )

    gpio_servers_stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('nantrobot_gpio'),
                'launch',
                'gpio_servers_auto.launch.py',
            ])
        )
    )

    motor_control = Node(
        package='motor_control_pkg',
        executable='control_gateway',
        name='control_gateway',
        output='screen',
        parameters=[{
            'serial_port': serial_port,
            'serial_baud': 115200,
            'serial_trace': serial_trace,
        }],
        condition=UnlessCondition(debug_terminal),
    )

    motor_control_debug_terminal = Node(
        package='motor_control_pkg',
        executable='control_gateway',
        name='control_gateway',
        output='screen',
        parameters=[{
            'serial_port': serial_port,
            'serial_baud': 115200,
            'serial_trace': serial_trace,
        }],
        prefix=debug_terminal_prefix,
        condition=IfCondition(debug_terminal),
    )

    delayed_behavior_tree_start = TimerAction(
        period=behavior_tree_start_delay,
        actions=[behavior_tree_node],
    )

    return LaunchDescription([
        behavior_tree_start_delay_arg,
        debug_terminal_arg,
        debug_terminal_prefix_arg,
        serial_port_arg,
        serial_trace_arg,
        gpio_servers_stack,
        motor_control,
        motor_control_debug_terminal,
        delayed_behavior_tree_start,
    ])
