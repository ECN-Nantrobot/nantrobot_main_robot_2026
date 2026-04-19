from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    behavior_tree_start_delay = LaunchConfiguration('behavior_tree_start_delay')

    behavior_tree_start_delay_arg = DeclareLaunchArgument(
        'behavior_tree_start_delay',
        default_value='4.0',
        description='Delay in seconds before launching behavior_tree to let GPIO action servers start.',
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
        executable='move',
        name='motor_control_server',
        output='screen',
    )

    delayed_behavior_tree_start = TimerAction(
        period=behavior_tree_start_delay,
        actions=[behavior_tree_node],
    )

    return LaunchDescription([
        behavior_tree_start_delay_arg,
        gpio_servers_stack,
        motor_control,
        delayed_behavior_tree_start,
    ])
