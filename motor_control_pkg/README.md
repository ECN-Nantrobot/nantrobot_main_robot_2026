sudo apt update && sudo apt install xterm && sudo apt install ros-jazzy-example-interfaces


terminal 1
socat -d -d PTY,link=/tmp/ttyV0,raw,echo=0 PTY,link=/tmp/ttyV1,raw,echo=0

terminal 2
python3 ~/ros2_ws/src/motor_control_pkg/arduino/arduino_sim.py

terminal 3
colcon build --packages-select motor_control_pkg && source ~/ros2_ws/install/setup.bash && ros2 launch motor_control_pkg robot_launch.launch.py


Note
Actions
- Pick up: 1
- Drop: 2

#TODO: the odom computation does not work


On the ROS2 level
I want to send: 
Message of type A-distance-angle, where
- A is the action
1. Pick up: 1
2. Drop: 2
3. Move: 3, it can be use also for emergency and stop the robot
- Distance to move: 0 for pick up and drop
- Angle to move: 0 for pick up and drop

P-2000-1

On the ESP3 level