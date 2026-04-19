#ifndef SET_TEAM_ACTION_HPP
#define SET_TEAM_ACTION_HPP

#include <behaviortree_ros2/bt_action_node.hpp>
#include <rclcpp/rclcpp.hpp>

#include "nantrobot_interfaces/action/set_team.hpp"

using SetTeam = nantrobot_interfaces::action::SetTeam;

using namespace BT;

class SetTeamAction : public RosActionNode<SetTeam>
{
public:
  SetTeamAction(const std::string& name, const NodeConfig& conf, const RosNodeParams& params)
    : RosActionNode<SetTeam>(name, conf, params)
  {}

  static PortsList providedPorts()
  {
    return providedBasicPorts({InputPort<bool>("team")});
  }

  bool setGoal(RosActionNode::Goal& goal) override
  {
    const auto team = getInput<bool>("team");
    if (!team)
    {
      RCLCPP_ERROR(logger(), "SetTeamAction: missing required input [team]");
      return false;
    }
    goal.team = *team;
    return true;
  }

  NodeStatus onResultReceived(const WrappedResult& wr) override
  {
    if (!wr.result->success)
    {
      RCLCPP_ERROR(logger(), "SetTeamAction failed: %s", wr.result->error_message.c_str());
    }
    return wr.result->success ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
  }

  NodeStatus onFeedback(const std::shared_ptr<const Feedback> /*feedback*/) override
  {
    return NodeStatus::RUNNING;
  }

  NodeStatus onFailure(ActionNodeErrorCode error) override
  {
    RCLCPP_ERROR(logger(), "SetTeamAction transport failure: %s", toStr(error));
    return NodeStatus::FAILURE;
  }
};

#endif // SET_TEAM_ACTION_HPP
