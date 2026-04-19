#ifndef STOP_ACTION_HPP
#define STOP_ACTION_HPP

#include <behaviortree_ros2/bt_action_node.hpp>
#include <rclcpp/rclcpp.hpp>

#include "nantrobot_interfaces/action/stop.hpp"

using Stop = nantrobot_interfaces::action::Stop;

using namespace BT;

class StopAction : public RosActionNode<Stop>
{
public:
  StopAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
    : RosActionNode<Stop>(name, conf, params)
  {}

  static PortsList providedPorts()
  {
    return providedBasicPorts({});
  }

  bool setGoal(RosActionNode::Goal&) override
  {
    return true;
  }

  NodeStatus onResultReceived(const WrappedResult& wr) override
  {
    if (!wr.result->success)
    {
      RCLCPP_ERROR(logger(), "StopAction failed: %s", wr.result->error_message.c_str());
    }
    return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
  }

  NodeStatus onFeedback(const std::shared_ptr<const Feedback> /*feedback*/) override
  {
    return NodeStatus::RUNNING;
  }

  NodeStatus onFailure(ActionNodeErrorCode error) override
  {
    RCLCPP_ERROR(logger(), "StopAction transport failure: %s", toStr(error));
    return NodeStatus::FAILURE;
  }
};

#endif // STOP_ACTION_HPP
