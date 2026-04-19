#ifndef INIT_ODOM_ACTION_HPP
#define INIT_ODOM_ACTION_HPP

#include <behaviortree_ros2/bt_action_node.hpp>
#include <rclcpp/rclcpp.hpp>

#include "nantrobot_interfaces/action/init_odom.hpp"

using InitOdom = nantrobot_interfaces::action::InitOdom;

using namespace BT;

class InitOdomAction : public RosActionNode<InitOdom>
{
public:
  InitOdomAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
    : RosActionNode<InitOdom>(name, conf, params)
  {}

  bool setGoal(RosActionNode::Goal& goal) override
  {
    (void)goal;
    return true;
  }

  NodeStatus onResultReceived(const WrappedResult& wr) override
  {
    if (!wr.result->success)
    {
      RCLCPP_ERROR(logger(), "InitOdomAction failed: %s", wr.result->error_message.c_str());
    }
    return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
  }

  NodeStatus onFailure(ActionNodeErrorCode error) override
  {
    RCLCPP_ERROR(logger(), "InitOdomAction transport failure: %s", toStr(error));
    return NodeStatus::FAILURE;
  }
};

#endif // INIT_ODOM_ACTION_HPP
