#ifndef GPIO_WRITE_ACTION_HPP
#define GPIO_WRITE_ACTION_HPP

#include <behaviortree_ros2/bt_action_node.hpp>
#include "nantrobot_interfaces/action/gpio_write.hpp"
#include <rclcpp/rclcpp.hpp>

using GpioWrite = nantrobot_interfaces::action::GpioWrite;

using namespace BT;

class GpioWriteAction: public RosActionNode<GpioWrite>
{
public:
  GpioWriteAction(const std::string& name,
                  const NodeConfig& conf,
                  const RosNodeParams& params)
    : RosActionNode<GpioWrite>(name, conf, params)
  {}

  GpioWriteAction(const std::string& name,
                  const NodeConfig& conf)
    : RosActionNode<GpioWrite>(name, conf, RosNodeParams(std::make_shared<rclcpp::Node>("gpio_write"), "gpio_write"))
  {}

  GpioWriteAction(const std::string& name)
    : RosActionNode<GpioWrite>(name, NodeConfig(), RosNodeParams(std::make_shared<rclcpp::Node>("gpio_write"), "gpio_write"))
  {}

  static PortsList providedPorts()
  {
    return providedBasicPorts(
      {
        InputPort<unsigned>("pin"),
        InputPort<bool>("state")
      });
  }

  bool setGoal(RosActionNode::Goal& goal) override
  {
    const auto pin = getInput<unsigned>("pin");
    if (!pin)
    {
      RCLCPP_ERROR(logger(), "GpioWriteAction: missing required input [pin]");
      return false;
    }

    const auto state = getInput<bool>("state");
    if (!state)
    {
      RCLCPP_ERROR(logger(), "GpioWriteAction: missing required input [state]");
      return false;
    }

    goal.pin = *pin;
    goal.state = *state;
    return true;
  }

  NodeStatus onResultReceived(const WrappedResult& wr) override
  {
    return wr.result->value == getInput<bool>("state") ? NodeStatus::SUCCESS : NodeStatus::FAILURE;
  }

  NodeStatus onFailure(ActionNodeErrorCode error) override
  {
    RCLCPP_ERROR(logger(), "Error: %d", error);
    return NodeStatus::FAILURE;
  }

  void halt() override
  {
    if(status() == NodeStatus::RUNNING)
    {
      resetStatus();
    }
  }
};

#endif // GPIO_WRITE_ACTION_HPP