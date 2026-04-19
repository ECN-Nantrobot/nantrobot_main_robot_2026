#ifndef PUT_ACTION_HPP
#define PUT_ACTION_HPP

#include <behaviortree_ros2/bt_action_node.hpp>
#include <rclcpp/rclcpp.hpp>

#include "nantrobot_interfaces/action/put.hpp"

using Put = nantrobot_interfaces::action::Put;

using namespace BT;

class PutAction : public RosActionNode<Put>
{
public:
  PutAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
    : RosActionNode<Put>(name, conf, params)
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
      RCLCPP_ERROR(logger(), "PutAction: missing required input [forward]");
      return false;
    }
    goal.forward = *forward;
    return true;
  }

  NodeStatus onResultReceived(const WrappedResult& wr) override
  {
    if (!wr.result->success)
    {
      RCLCPP_ERROR(logger(), "PutAction failed: %s", wr.result->error_message.c_str());
    }
    return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
  }

  NodeStatus onFeedback(const std::shared_ptr<const Feedback> /*feedback*/) override
  {
    return NodeStatus::RUNNING;
  }

  NodeStatus onFailure(ActionNodeErrorCode error) override
  {
    RCLCPP_ERROR(logger(), "PutAction transport failure: %s", toStr(error));
    return NodeStatus::FAILURE;
  }
};

#endif // PUT_ACTION_HPP
