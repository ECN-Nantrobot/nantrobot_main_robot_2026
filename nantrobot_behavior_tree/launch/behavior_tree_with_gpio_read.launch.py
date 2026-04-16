from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    behavior_tree_node = Node(
        package='nantrobot_behavior_tree',
        executable='behavior_tree',
        name='behavior_tree',
        output='screen',
    )

    gpio_read_server_node = Node(
        package='nantrobot_servers',
        executable='gpio_read_action_server',
        name='gpio_read_action_server',
        output='screen',
    )

    gpio_write_server_node = Node(
        package='nantrobot_servers',
        executable='gpio_write_action_server',
        name='gpio_write_action_server',
        output='screen',
    )

    return LaunchDescription([
        gpio_read_server_node,
        gpio_write_server_node,
        behavior_tree_node,
    ])
