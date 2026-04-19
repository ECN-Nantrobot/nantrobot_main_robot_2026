#ifndef ORIENTATION_ACTION_HPP
#define ORIENTATION_ACTION_HPP

#include <behaviortree_ros2/bt_action_node.hpp>
#include <rclcpp/rclcpp.hpp>

#include "nantrobot_interfaces/action/orientation.hpp"

using Orientation = nantrobot_interfaces::action::Orientation;

using namespace BT;

class OrientationAction : public RosActionNode<Orientation>
{
public:
  OrientationAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
    : RosActionNode<Orientation>(name, conf, params)
  {}

  static PortsList providedPorts()
  {
    return providedBasicPorts(
      {
        InputPort<double>("theta"),
        OutputPort<double>("current_x"),
        OutputPort<double>("current_y"),
        OutputPort<double>("current_theta"),
      });
  }

  bool setGoal(RosActionNode::Goal& goal) override
  {
    const auto theta = getInput<double>("theta");
    if (!theta)
    {
      RCLCPP_ERROR(logger(), "OrientationAction: missing required input [theta]");
      return false;
    }

    goal.target_theta = *theta;
    return true;
  }

  NodeStatus onResultReceived(const WrappedResult& wr) override
  {
    if (!wr.result->success)
    {
      RCLCPP_ERROR(logger(), "OrientationAction failed: %s", wr.result->error_message.c_str());
    }
    return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
  }

  NodeStatus onFeedback(const std::shared_ptr<const Feedback> feedback) override
  {
    setOutput("current_x", feedback->current_x);
    setOutput("current_y", feedback->current_y);
    setOutput("current_theta", feedback->current_theta);
    return NodeStatus::RUNNING;
  }

  NodeStatus onFailure(ActionNodeErrorCode error) override
  {
    RCLCPP_ERROR(logger(), "OrientationAction transport failure: %s", toStr(error));
    return NodeStatus::FAILURE;
  }
};

#endif // ORIENTATION_ACTION_HPP
