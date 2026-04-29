#include <behaviortree_cpp/bt_factory.h>
#include <behaviortree_cpp/loggers/groot2_publisher.h>
#include <iostream>

#include "nantrobot_behavior_tree/GpioReadAction.hpp"
#include "nantrobot_behavior_tree/GpioWriteAction.hpp"
#include "nantrobot_behavior_tree/GotoAction.hpp"
#include "nantrobot_behavior_tree/OrientationAction.hpp"
#include "nantrobot_behavior_tree/PickAction.hpp"
#include "nantrobot_behavior_tree/PutAction.hpp"
#include "nantrobot_behavior_tree/InitOdomAction.hpp"
#include "nantrobot_behavior_tree/SetTeamAction.hpp"
#include "nantrobot_behavior_tree/StopAction.hpp"

// file that contains the custom nodes definitions
//#include "nantrobot_main_robot_2026/bt_nodes.hpp"

using namespace BT;

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);

  // We use the BehaviorTreeFactory to register our custom nodes
  BehaviorTreeFactory factory;

  // Ignore global launch arguments (like __node remapping) so these
  // helper nodes keep stable names for action client connectivity.
  auto action_client_node_options = rclcpp::NodeOptions().use_global_arguments(false);
  // The recommended way to create a Node is through inheritance.
  auto node_gpio_read = std::make_shared<rclcpp::Node>("gpio_read_action_client", action_client_node_options);
  RosNodeParams gpio_read_params;
  gpio_read_params.nh = node_gpio_read;
  gpio_read_params.default_port_value = "gpio_read";
  factory.registerNodeType<GpioReadAction>("GpioRead", gpio_read_params);

  auto node_gpio_write = std::make_shared<rclcpp::Node>("gpio_write_action_client", action_client_node_options);
  RosNodeParams gpio_write_params;
  gpio_write_params.nh = node_gpio_write;
  gpio_write_params.default_port_value = "gpio_write";
  factory.registerNodeType<GpioWriteAction>("GpioWrite", gpio_write_params);

  auto node_goto = std::make_shared<rclcpp::Node>("goto_action_client", action_client_node_options);
  RosNodeParams goto_params;
  goto_params.nh = node_goto;
  goto_params.default_port_value = "goto";
  factory.registerNodeType<GotoAction>("Goto", goto_params);

  auto node_orientation = std::make_shared<rclcpp::Node>("orientation_action_client", action_client_node_options);
  RosNodeParams orientation_params;
  orientation_params.nh = node_orientation;
  orientation_params.default_port_value = "orientation";
  factory.registerNodeType<OrientationAction>("Orientation", orientation_params);

  auto node_pick = std::make_shared<rclcpp::Node>("pick_action_client", action_client_node_options);
  RosNodeParams pick_params;
  pick_params.nh = node_pick;
  pick_params.default_port_value = "pick";
  factory.registerNodeType<PickAction>("Pick", pick_params);

  auto node_put = std::make_shared<rclcpp::Node>("put_action_client", action_client_node_options);
  RosNodeParams put_params;
  put_params.nh = node_put;
  put_params.default_port_value = "put";
  factory.registerNodeType<PutAction>("Put", put_params);

  auto node_init_odom = std::make_shared<rclcpp::Node>("init_odom_action_client", action_client_node_options);
  RosNodeParams init_odom_params;
  init_odom_params.nh = node_init_odom;
  init_odom_params.default_port_value = "init_odom";
  factory.registerNodeType<InitOdomAction>("InitOdom", init_odom_params);

  auto node_set_team = std::make_shared<rclcpp::Node>("set_team_action_client", action_client_node_options);
  RosNodeParams set_team_params;
  set_team_params.nh = node_set_team;
  set_team_params.default_port_value = "set_team";
  factory.registerNodeType<SetTeamAction>("SetTeam", set_team_params);

  auto node_stop = std::make_shared<rclcpp::Node>("stop_action_client", action_client_node_options);
  RosNodeParams stop_params;
  stop_params.nh = node_stop;
  stop_params.default_port_value = "stop";
  factory.registerNodeType<StopAction>("Stop", stop_params);

  //You can also create SimpleActionNodes using methods of a class

  // Trees are created at deployment-time (i.e. at run-time, but only 
  // once at the beginning). 
    
  // IMPORTANT: when the object "tree" goes out of scope, all the 
  // TreeNodes are destroyed
  auto global_bb = BT::Blackboard::create();
  auto maintree_bb = BT::Blackboard::create(global_bb);
  
  //  auto tree = factory.createTreeFromFile("./install/nantrobot_behavior_tree/share/nantrobot_behavior_tree/ressources/behavior_tree.xml", maintree_bb);
   auto tree = factory.createTreeFromFile("./install/nantrobot_behavior_tree/share/nantrobot_behavior_tree/ressources/test_tree.xml", maintree_bb);
  
   BT::Groot2Publisher publisher(tree);
  // To "execute" a Tree you need to "tick" it.
  // The tick is propagated to the children based on the logic of the tree.
  // In this case, the entire sequence is executed, because all the children
  // of the Sequence return SUCCESS.
  tree.tickWhileRunning();

  rclcpp::shutdown();
  return 0;
}
