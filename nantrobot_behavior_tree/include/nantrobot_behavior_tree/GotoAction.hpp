#ifndef GOTO_ACTION_HPP
#define GOTO_ACTION_HPP

#include <behaviortree_ros2/bt_action_node.hpp>
#include <rclcpp/rclcpp.hpp>

#include "nantrobot_interfaces/action/goto.hpp"

using Goto = nantrobot_interfaces::action::Goto;

using namespace BT;

class GotoAction : public RosActionNode<Goto>
{
public:
  GotoAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
    : RosActionNode<Goto>(name, conf, params)
  {}

  static PortsList providedPorts()
  {
    return providedBasicPorts(
      {
        InputPort<double>("x"),
        InputPort<double>("y"),
        InputPort<bool>("forward"),
        OutputPort<double>("current_x"),
        OutputPort<double>("current_y"),
        OutputPort<double>("current_theta"),
      });
  }

  bool setGoal(RosActionNode::Goal& goal) override
  {
    const auto x = getInput<double>("x");
    if (!x)
    {
      RCLCPP_ERROR(logger(), "GotoAction: missing required input [x]");
      return false;
    }

    const auto y = getInput<double>("y");
    if (!y)
    {
      RCLCPP_ERROR(logger(), "GotoAction: missing required input [y]");
      return false;
    }

    goal.target_x = *x;
    goal.target_y = *y;
    goal.forward = getInput<bool>("forward").value_or(true);
    return true;
  }

  NodeStatus onResultReceived(const WrappedResult& wr) override
  {
    if (!wr.result->success)
    {
      RCLCPP_ERROR(logger(), "GotoAction failed: %s", wr.result->error_message.c_str());
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
    RCLCPP_ERROR(logger(), "GotoAction transport failure: %s", toStr(error));
    return NodeStatus::FAILURE;
  }
};

#endif // GOTO_ACTION_HPP
