#ifndef MOVE_TO_ACTION_HPP
#define MOVE_TO_ACTION_HPP

#include <behaviortree_ros2/bt_action_node.hpp>
#include <rclcpp/rclcpp.hpp>

#include "nantrobot_interfaces/action/robot_move.hpp"

using RobotMove = nantrobot_interfaces::action::RobotMove;

using namespace BT;

class MoveToAction : public RosActionNode<RobotMove>
{
public:
  MoveToAction(const std::string& name,
                  const NodeConfig& conf,
                  const RosNodeParams& params)
    : RosActionNode<RobotMove>(name, conf, params)
  {}

  static PortsList providedPorts()
  {
    // Keep the MoveTo ports to remain compatible with current BT XML.
    return providedBasicPorts(
      {
        InputPort<bool>("team"),
        InputPort<bool>("forward"),
        InputPort<double>("x"),
        InputPort<double>("y"),
        OutputPort<double>("current_x"),
        OutputPort<double>("current_y"),
        OutputPort<double>("remaining_distance")
      });
  }

  bool setGoal(RosActionNode::Goal& goal) override
  {
    const auto x = getInput<double>("x");
    if (!x)
    {
      RCLCPP_ERROR(logger(), "MoveToAction: missing required input [x]");
      return false;
    }

    const auto y = getInput<double>("y");
    if (!y)
    {
      RCLCPP_ERROR(logger(), "MoveToAction: missing required input [y]");
      return false;
    }

    goal.target_x = *x;
    goal.target_y = *y;
    return true;
  }

  NodeStatus onResultReceived(const WrappedResult& wr) override
  {
    return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
  }

  NodeStatus onFeedback(const std::shared_ptr<const Feedback> feedback) override
  {
    setOutput("current_x", feedback->current_x);
    setOutput("current_y", feedback->current_y);
    setOutput("remaining_distance", feedback->remaining_distance);
    return NodeStatus::RUNNING;
  }

  NodeStatus onFailure(ActionNodeErrorCode error) override
  {
    RCLCPP_ERROR(logger(), "MoveToAction failed: %s", toStr(error));
    return NodeStatus::FAILURE;
  }
};

#endif // MOVE_TO_ACTION_HPP