cmake_minimum_required(VERSION 3.5)
project(nantrobot_behavior_tree)

cmake_policy(SET CMP0057 NEW)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(behaviortree_cpp REQUIRED)
find_package(behaviortree_ros2 REQUIRED)
find_package(nantrobot_interfaces REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

## Install package files so they're available in the install space
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/launch")
  install(DIRECTORY launch
    DESTINATION share/${PROJECT_NAME}
  )
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/config")
  install(DIRECTORY config
    DESTINATION share/${PROJECT_NAME}
  )
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/include")
  install(DIRECTORY include/
    DESTINATION include
  )
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/ressources")
  install(DIRECTORY ressources
    DESTINATION share/${PROJECT_NAME}
  )
endif()

# Add executable and link libraries
include_directories("include/")
add_executable(behavior_tree src/behavior_tree.cpp "include/nantrobot_behavior_tree/GpioReadAction.hpp")
ament_target_dependencies(behavior_tree
  rclcpp
  rclpy
  behaviortree_cpp
  behaviortree_ros2
  nantrobot_interfaces
)

install(TARGETS
  behavior_tree
  DESTINATION lib/${PROJECT_NAME})

ament_package()
