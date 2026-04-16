#include <behaviortree_cpp/bt_factory.h>
#include <behaviortree_cpp/loggers/groot2_publisher.h>
#include <iostream>

#include "nantrobot_behavior_tree/GpioReadAction.hpp"

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
  const PortsList init_motors_ports = { InputPort<bool>("team") };
  factory.registerSimpleAction("InitMotors", [&](TreeNode& self) {
    const auto team = self.getInput<bool>("team");
    if (!team)
    {
      std::cerr << "InitMotors: missing input port 'team'" << std::endl;
      return NodeStatus::FAILURE;
    }
    std::cout << "InitMotors team=" << (*team ? "true" : "false") << std::endl;
    return NodeStatus::SUCCESS;
  }, init_motors_ports);

  const PortsList move_to_ports = {
    InputPort<bool>("team"),
    InputPort<bool>("forward"),
    InputPort<double>("x"),
    InputPort<double>("y"),
    InputPort<double>("orientation")
  };
  factory.registerSimpleAction("MoveTo", [&](TreeNode& self) {
    const auto team = self.getInput<bool>("team");
    if (!team)
    {
      std::cerr << "MoveTo: missing input port 'team'" << std::endl;
      return NodeStatus::FAILURE;
    }
    const auto forward = self.getInput<bool>("forward");
    if (!forward)
    {
      std::cerr << "MoveTo: missing input port 'forward'" << std::endl;
      return NodeStatus::FAILURE;
    }
    std::cout << "MoveTo team=" << (*team ? "true" : "false")
              << " forward=" << (*forward ? "true" : "false") << std::endl;
    return NodeStatus::SUCCESS;
  }, move_to_ports);

  const PortsList pick_ports = { InputPort<bool>("forward") };
  factory.registerSimpleAction("Pick", [&](TreeNode& self) {
    const auto forward = self.getInput<bool>("forward");
    if (!forward)
    {
      std::cerr << "Pick: missing input port 'forward'" << std::endl;
      return NodeStatus::FAILURE;
    }
    std::cout << "Pick forward=" << (*forward ? "true" : "false") << std::endl;
    return NodeStatus::SUCCESS;
  }, pick_ports);

  const PortsList put_ports = { InputPort<bool>("forward") };
  factory.registerSimpleAction("Put", [&](TreeNode& self) {
    const auto forward = self.getInput<bool>("forward");
    if (!forward)
    {
      std::cerr << "Put: missing input port 'forward'" << std::endl;
      return NodeStatus::FAILURE;
    }
    std::cout << "Put forward=" << (*forward ? "true" : "false") << std::endl;
    return NodeStatus::SUCCESS;
  }, put_ports);

  factory.registerSimpleAction("Stop", [&](TreeNode&) {
    std::cout << "Stop" << std::endl;
    return NodeStatus::SUCCESS;
  });

  //You can also create SimpleActionNodes using methods of a class

  // Trees are created at deployment-time (i.e. at run-time, but only 
  // once at the beginning). 
    
  // IMPORTANT: when the object "tree" goes out of scope, all the 
  // TreeNodes are destroyed
  auto global_bb = BT::Blackboard::create();
  auto maintree_bb = BT::Blackboard::create(global_bb);
  
   auto tree = factory.createTreeFromFile("./install/nantrobot_behavior_tree/share/nantrobot_behavior_tree/ressources/behavior_tree.xml", maintree_bb);
  
   BT::Groot2Publisher publisher(tree);
  // To "execute" a Tree you need to "tick" it.
  // The tick is propagated to the children based on the logic of the tree.
  // In this case, the entire sequence is executed, because all the children
  // of the Sequence return SUCCESS.
  tree.tickWhileRunning();

  rclcpp::shutdown();
  return 0;
}
