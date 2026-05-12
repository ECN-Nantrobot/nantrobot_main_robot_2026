import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

from launch.actions import TimerAction

WAIT_TIME = 10.0


def generate_launch_description():
    # 1. Path to the SLLidar launch file
    sllidar_dir = get_package_share_directory('sllidar_ros2')
    sllidar_launch_path = os.path.join(sllidar_dir, 'launch', 'view_sllidar_c1_launch.py')

    # 2. Include the SLLidar launch
    included_sllidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(sllidar_launch_path)
    )

    # 3. Define your custom lidar processing node
    lidar_node = Node(
        package='lidar_pkg',
        executable='lidar.py',
        name='lidar_node',
        output='screen'
    )

    # 4. Define your serial bridge node
    arduino_node = Node(
        package='lidar_pkg',
        executable='lidar_to_arduino.py',
        name='vel_node',
        output='screen'
    )


    delayed_node = TimerAction(
        period=WAIT_TIME,
        actions=[arduino_node, lidar_node]
    )



    # Create the launch description and add the actions
    return LaunchDescription([
        included_sllidar_launch,
        delayed_node
    ])