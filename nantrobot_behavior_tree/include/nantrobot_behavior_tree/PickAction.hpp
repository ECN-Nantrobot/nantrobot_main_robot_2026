#ifndef PICK_ACTION_HPP
#define PICK_ACTION_HPP

#include <behaviortree_ros2/bt_action_node.hpp>
#include <rclcpp/rclcpp.hpp>

#include "nantrobot_interfaces/action/pick.hpp"

using Pick = nantrobot_interfaces::action::Pick;

using namespace BT;

class PickAction : public RosActionNode<Pick>
{
public:
  PickAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
    : RosActionNode<Pick>(name, conf, params)
  {}

  static PortsList providedPorts()
  {
    return providedBasicPorts({InputPort<bool>("forward")});
  }

  bool setGoal(RosActionNode::Goal& goal) override
  {
    const auto forward = getInput<bool>("forward");
    if (!forward)
    {
      RCLCPP_ERROR(logger(), "PickAction: missing required input [forward]");
      return false;
    }
    goal.forward = *forward;
    return true;
  }

  NodeStatus onResultReceived(const WrappedResult& wr) override
  {
    if (!wr.result->success)
    {
      RCLCPP_ERROR(logger(), "PickAction failed: %s", wr.result->error_message.c_str());
    }
    return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
  }

  NodeStatus onFeedback(const std::shared_ptr<const Feedback> /*feedback*/) override
  {
    return NodeStatus::RUNNING;
  }

  NodeStatus onFailure(ActionNodeErrorCode error) override
  {
    RCLCPP_ERROR(logger(), "PickAction transport failure: %s", toStr(error));
    return NodeStatus::FAILURE;
  }
};

#endif // PICK_ACTION_HPP
