#ifndef GPIO_READ_ACTION_HPP
#define GPIO_READ_ACTION_HPP
#include <behaviortree_ros2/bt_action_node.hpp>
#include "nantrobot_interfaces/action/gpio_read.hpp"
#include <rclcpp/rclcpp.hpp>


// let's define these, for brevity
using GpioRead = nantrobot_interfaces::action::GpioRead;
using GoalHandleGpioRead = rclcpp_action::ServerGoalHandle<GpioRead>;

using namespace BT;

class GpioReadAction: public RosActionNode<GpioRead>
{
public:
  GpioReadAction(const std::string& name,
                  const NodeConfig& conf,
                  const RosNodeParams& params)
    : RosActionNode<GpioRead>(name, conf, params)
  {}

  GpioReadAction(const std::string& name,
                  const NodeConfig& conf)
    : RosActionNode<GpioRead>(name, conf, RosNodeParams(std::make_shared<rclcpp::Node>("gpio_read"), "gpio_read"))
  {}

  GpioReadAction(const std::string& name)
    : RosActionNode<GpioRead>(name, NodeConfig(), RosNodeParams(std::make_shared<rclcpp::Node>("gpio_read"), "gpio_read"))
  {}

  // The specific ports of this Derived class
  // should be merged with the ports of the base class,
  // using RosActionNode::providedBasicPorts()
  static PortsList providedPorts()
  {
    return providedBasicPorts({InputPort<unsigned>("pin"), OutputPort<bool>("value")});
  }

  // This is called when the TreeNode is ticked and it should
  // send the request to the action server
  bool setGoal(RosActionNode::Goal& goal) override 
  {
    // get "pin" from the Input port
    getInput("pin", goal.pin);
    // return true, if we were able to set the goal correctly.
    return true;
  }
  
  // Callback executed when the reply is received.
  // Based on the reply you may decide to return SUCCESS or FAILURE.
  NodeStatus onResultReceived(const WrappedResult& wr) override
  {
    setOutput("value", wr.result->value);
    return NodeStatus::SUCCESS;
  }

  // Callback invoked when there was an error at the level
  // of the communication between client and server.
  // This will set the status of the TreeNode to either SUCCESS or FAILURE,
  // based on the return value.
  // If not overridden, it will return FAILURE by default.
  virtual NodeStatus onFailure(ActionNodeErrorCode error) override
  {
    RCLCPP_ERROR(logger(), "Error: %d", error);
    return NodeStatus::FAILURE;
  }

  void halt() override
  {
    if(status() == NodeStatus::RUNNING)
    {
      // GPIO reads are short-lived; avoid cancelGoal() races on halt.
      resetStatus();
    }
  }

  // we also support a callback for the feedback, as in
  // the original tutorial.
  // Usually, this callback should return RUNNING, but you
  // might decide, based on the value of the feedback, to abort
  // the action, and consider the TreeNode completed.
  // In that case, return SUCCESS or FAILURE.
  // The Cancel request will be send automatically to the server.
//   NodeStatus onFeedback(const std::shared_ptr<const Feedback> feedback)
//   {
//     std::stringstream ss;
//     ss << "Next number in sequence received: ";
//     for (auto number : feedback->partial_sequence) {
//       ss << number << " ";
//     }
//     RCLCPP_INFO(logger(), ss.str().c_str());
//     return NodeStatus::RUNNING;
//   }
};

#endif // GPIO_READ_ACTION_HPP
