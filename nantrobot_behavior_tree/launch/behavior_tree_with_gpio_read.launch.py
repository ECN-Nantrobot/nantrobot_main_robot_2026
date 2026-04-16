from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    behavior_tree_node = Node(
        package='nantrobot_behavior_tree',
        executable='behavior_tree',
        name='behavior_tree',
        output='screen',
    )

    gpio_servers_stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('nantrobot_servers'),
                'launch',
                'gpio_servers_auto.launch.py',
            ])
        )
    )

    delayed_behavior_tree_start = TimerAction(
        period=1.5,
        actions=[behavior_tree_node],
    )

    return LaunchDescription([
        gpio_servers_stack,
        delayed_behavior_tree_start,
    ])
