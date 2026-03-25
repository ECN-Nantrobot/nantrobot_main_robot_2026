#include <behaviortree_cpp/bt_factory.h>
#include <behaviortree_cpp/loggers/groot2_publisher.h>
#include <iostream>

#include "nantrobot_main_robot_2026/GpioReadAction.hpp"

// file that contains the custom nodes definitions
//#include "nantrobot_main_robot_2026/bt_nodes.hpp"

using namespace BT;

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);

  auto node_gpio_read = std::make_shared<rclcpp::Node>("gpio_read");
    // We use the BehaviorTreeFactory to register our custom nodes
  BehaviorTreeFactory factory;

  // The recommended way to create a Node is through inheritance.
  factory.registerNodeType<GpioReadAction>("GpioRead", RosNodeParams(node_gpio_read, "gpio_read"));

  // Registering a SimpleActionNode using a function pointer.
  // You can use C++11 lambdas or std::bind
  factory.registerSimpleCondition("SetTeam", [&](TreeNode&) { return NodeStatus::SUCCESS; } );

  factory.registerSimpleCondition("WaitForStart", [&](TreeNode&) { std::cout << "WaitForStart" << std::endl; return NodeStatus::FAILURE; } );

  factory.registerSimpleCondition("InitPoses", [&](TreeNode&) { std::cout << "InitPoses" << std::endl; return NodeStatus::SUCCESS; } );

  factory.registerSimpleCondition("MoveTo", [&](TreeNode&) { std::cout << "MoveTo" << std::endl; return NodeStatus::SUCCESS; } );

  factory.registerSimpleCondition("Pick", [&](TreeNode&) { std::cout << "Pick" << std::endl; return NodeStatus::SUCCESS; } );

  factory.registerSimpleCondition("Stop", [&](TreeNode&) { std::cout << "Stop" << std::endl; return NodeStatus::SUCCESS; } );

  //You can also create SimpleActionNodes using methods of a class

  // Trees are created at deployment-time (i.e. at run-time, but only 
  // once at the beginning). 
    
  // IMPORTANT: when the object "tree" goes out of scope, all the 
  // TreeNodes are destroyed
  
   auto tree = factory.createTreeFromFile("./install/nantrobot_main_robot_2026/share/nantrobot_main_robot_2026/ressources/my_tree.xml");
  
   BT::Groot2Publisher publisher(tree);
  // To "execute" a Tree you need to "tick" it.
  // The tick is propagated to the children based on the logic of the tree.
  // In this case, the entire sequence is executed, because all the children
  // of the Sequence return SUCCESS.
  tree.tickWhileRunning();

  rclcpp::shutdown();
  return 0;
}
