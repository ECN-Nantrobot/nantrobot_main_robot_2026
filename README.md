# Nantrobot Middleware for the 2026 Robotics Cup

## Installation

### Get all required packages

```bash
mkdir -p ~/nantrobot_ws/src
cd ~/nantrobot_ws/src
# Get this repo
git clone https://github.com/ECN-Nantrobot/nantrobot_main_robot_2026.git
# Get the simulation
git clone https://github.com/ECN-Nantrobot/nantrobot_robot_sim.git
git clone https://github.com/ECN-Nantrobot/nantrobot_rviz_panel.git
# Get dependencies
git clone https://github.com/BehaviorTree/BehaviorTree.ROS2.git
```

### Install dependencies

```bash
cd ~/nantrobot_ws
rosdep install --from-paths src --ignore-src -r -y
```

### Build

```bash
colcon build --symlink-install
```

## Run

```bash
cd ~/nantrobot_ws
source install/setup.bash
ros2 launch nantrobot_behavior_tree behavior_tree_with_gpio_read.launch.py
```

## Concepts

### Packages

This repo is made of 3 different packages. Each one handles a specific part of the ROS2 stack.

First, the `nantrobot_interfaces` package creates customs action messages used to interract with the action servers.

Then, the `nantrobot_gpio` package consist of a few python servers that interract with the GPIO or the ESP32 (to be completed with other features). It also contains an emulator for the raspberrypi GPIO (the use of the emulated servers is auto detected).

Finally, the `nantrobot_behavior_tree` package is the orchestrator. It handles the loading of a strategy with the BehaviorTree.CPP library, and interract with the ROS action servers through BehaviorTree.ROS. It also contains a launchfile that ensures all required programs are correctly launched.

## TODO


- Implement servers to communicate with the ESP32
- Add the simulation
- Integrate the Lidar
- Build the behavior Tree
