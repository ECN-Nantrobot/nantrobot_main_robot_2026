import threading
import time

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import Float32
from lidar_pkg.msg import ObstacleStatus

from nantrobot_interfaces.action import (
    Goto,
    InitOdom,
    Orientation,
    Pick,
    Put,
    SetTeam,
    Stop,
)

try:
    import serial
except ImportError:
    serial = None


class ControlGateway(Node):
    def __init__(self):
        super().__init__('control_gateway')
        self.declare_parameter('serial_port', '/tmp/ttyV0')
        self.declare_parameter('serial_baud', 115200)
        self.declare_parameter('serial_trace', False)

        serial_port = self.get_parameter('serial_port').get_parameter_value().string_value
        serial_baud = (
            self.get_parameter('serial_baud').get_parameter_value().integer_value
        )
        self._serial_trace = (
            self.get_parameter('serial_trace').get_parameter_value().bool_value
        )

        self.current_x = 0.0
        self.current_y = 0.0
        self.current_theta = 0.0
        self.max_speed = 0.2

        self._state_lock = threading.Lock()
        self._response_cv = threading.Condition()
        self._response_queue = []
        self._active_task = None
        self._stop_requested = False

        self.arduino = None
        self._serial_reader_thread = None
        if serial is not None:
            try:
                self.arduino = serial.Serial(serial_port, serial_baud, timeout=0.1)
                self.get_logger().info(
                    f'Connected to serial {serial_port} @ {serial_baud} baud'
                )
                self._serial_reader_thread = threading.Thread(
                    target=self._serial_reader_loop,
                    daemon=True,
                )
                self._serial_reader_thread.start()
            except Exception as exc:
                self.get_logger().error(f'Serial connection failed: {exc}')

        self.create_subscription(ObstacleStatus, '/max_speed', self._max_speed_cb, 10)

        self._goto_server = ActionServer(
            self,
            Goto,
            'goto',
            execute_callback=self._execute_goto,
            goal_callback=lambda _goal: self._goal_callback('goto'),
            cancel_callback=self._cancel_callback,
        )
        self._orientation_server = ActionServer(
            self,
            Orientation,
            'orientation',
            execute_callback=self._execute_orientation,
            goal_callback=lambda _goal: self._goal_callback('orientation'),
            cancel_callback=self._cancel_callback,
        )
        self._pick_server = ActionServer(
            self,
            Pick,
            'pick',
            execute_callback=self._execute_pick,
            goal_callback=lambda _goal: self._goal_callback('pick'),
            cancel_callback=self._cancel_callback,
        )
        self._put_server = ActionServer(
            self,
            Put,
            'put',
            execute_callback=self._execute_put,
            goal_callback=lambda _goal: self._goal_callback('put'),
            cancel_callback=self._cancel_callback,
        )
        self._init_odom_server = ActionServer(
            self,
            InitOdom,
            'init_odom',
            execute_callback=self._execute_init_odom,
            goal_callback=lambda _goal: self._goal_callback('init_odom'),
            cancel_callback=self._cancel_callback,
        )
        self._set_team_server = ActionServer(
            self,
            SetTeam,
            'set_team',
            execute_callback=self._execute_set_team,
            goal_callback=lambda _goal: self._goal_callback('set_team'),
            cancel_callback=self._cancel_callback,
        )
        self._stop_server = ActionServer(
            self,
            Stop,
            'stop',
            execute_callback=self._execute_stop,
            goal_callback=lambda _goal: GoalResponse.ACCEPT,
            cancel_callback=self._cancel_callback,
        )

        if self._serial_trace:
            self.get_logger().info('Serial trace enabled: ROS <-> ESP32 traffic will be printed.')

    def _goal_callback(self, task_name):
        if task_name:
            self.get_logger().debug(f'Received "{task_name}" goal request.')
        return GoalResponse.ACCEPT

    def _cancel_callback(self, _cancel_request):
        self._stop_requested = True
        self._send_command('stop')
        return CancelResponse.ACCEPT

    def _set_active_task(self, task_name, is_motion=False):
        with self._state_lock:
            if self._active_task is not None:
                return False, self._active_task
            self._active_task = task_name
            self._stop_requested = False
        return True, None

    def _clear_active_task(self):
        with self._state_lock:
            self._active_task = None
            self._stop_requested = False

    def _max_speed_cb(self, msg:ObstacleStatus):
        new_speed = max(0.0, float(msg.velocity))
        self.max_speed = new_speed
        self._send_command(f'max_speed {new_speed:.3f}')

    def _send_command(self, command):
        if self.arduino is None:
            self.get_logger().warn(f'No serial available, command not sent: {command}')
            return False
        try:
            line = f'{command}\n'
            if self._serial_trace:
                self.get_logger().info(f'[ROS->ESP32] {command}')
            self.arduino.write(line.encode('utf-8'))
            return True
        except Exception as exc:
            self.get_logger().error(f'Failed to write serial command "{command}": {exc}')
            return False

    def _serial_reader_loop(self):
        while rclpy.ok() and self.arduino is not None:
            try:
                raw = self.arduino.readline()
            except Exception as exc:
                self.get_logger().error(f'Serial read error: {exc}')
                time.sleep(0.1)
                continue

            if not raw:
                continue

            line = raw.decode('utf-8', errors='ignore').strip()
            if not line:
                continue
            self._handle_serial_line(line)

    def _handle_serial_line(self, line):
        if self._serial_trace:
            self.get_logger().info(f'[ESP32->ROS] {line}')

        parts = line.split()
        if not parts:
            return

        head = parts[0].lower()
        if head == 'odom' and len(parts) >= 4:
            try:
                self.current_x = float(parts[1])
                self.current_y = float(parts[2])
                self.current_theta = float(parts[3])
            except ValueError:
                self.get_logger().warn(f'Invalid odom line: {line}')
            return

        with self._response_cv:
            if head == 'started' and len(parts) >= 2:
                command = parts[1].lower()
                self.get_logger().info(f'Arduino started command: {command}')
                self._response_queue.append(('started', command, ''))
                self._response_cv.notify_all()
            elif head == 'stopped' and len(parts) >= 2:
                command = parts[1].lower()
                self._response_queue.append(('stopped', command, ''))
                self._response_cv.notify_all()
            elif head == 'success' and len(parts) >= 2:
                command = parts[1].lower()
                self._response_queue.append(('success', command, ''))
                self._response_cv.notify_all()
            elif head == 'error':
                command = parts[1].lower() if len(parts) >= 2 else ''
                message = ' '.join(parts[2:]) if len(parts) >= 3 else 'unknown error'
                self._response_queue.append(('error', command, message))
                self._response_cv.notify_all()

    def _wait_for_command_response(self, command_name, goal_handle, feedback_cb):
        command_name = command_name.lower()
        while rclpy.ok():
            if goal_handle.is_cancel_requested:
                self._stop_requested = True
                self._send_command('stop')
                return False, 'goal canceled'

            with self._state_lock:
                if self._stop_requested and command_name != 'stop':
                    return False, 'stopped'

            feedback_cb()

            with self._response_cv:
                for idx, (kind, event_command, payload) in enumerate(self._response_queue):
                    if event_command != command_name:
                        continue

                    if kind == 'started':
                        self._response_queue.pop(idx)
                        break

                    if kind == 'error':
                        self._response_queue.pop(idx)
                        return False, payload

                    if kind == 'stopped':
                        self._response_queue.pop(idx)
                        return False, 'stopped'

                    if kind == 'success':
                        self._response_queue.pop(idx)
                        return True, ''

                self._response_cv.wait(timeout=0.1)

        return False, 'ROS shutdown'

    def _motion_feedback(self, feedback_msg):
        feedback_msg.current_x = self.current_x
        feedback_msg.current_y = self.current_y
        feedback_msg.current_theta = self.current_theta

    def _finalize_goal(self, goal_handle, result, success, error_message):
        result.success = success
        result.error_message = error_message
        if success:
            goal_handle.succeed()
        elif goal_handle.is_cancel_requested:
            goal_handle.canceled()
        else:
            goal_handle.abort()
        return result

    async def _execute_goto(self, goal_handle):
        feedback_msg = Goto.Feedback()
        result = Goto.Result()
        accepted, active_task = self._set_active_task('goto')
        if not accepted:
            return self._finalize_goal(
                goal_handle,
                result,
                False,
                f'busy: "{active_task}" already active',
            )
        target_x = float(goal_handle.request.target_x)
        target_y = float(goal_handle.request.target_y)
        forward = 1 if goal_handle.request.forward else 0

        try:
            command = f'goto {target_x:.3f} {target_y:.3f} {forward}'
            if not self._send_command(command):
                return self._finalize_goal(goal_handle, result, False, 'serial unavailable')

            ok, message = self._wait_for_command_response(
                'goto',
                goal_handle,
                lambda: (
                    self._motion_feedback(feedback_msg),
                    goal_handle.publish_feedback(feedback_msg),
                ),
            )
            return self._finalize_goal(goal_handle, result, ok, message)
        finally:
            self._clear_active_task()

    async def _execute_orientation(self, goal_handle):
        feedback_msg = Orientation.Feedback()
        result = Orientation.Result()
        accepted, active_task = self._set_active_task('orientation', is_motion=True)
        if not accepted:
            return self._finalize_goal(
                goal_handle,
                result,
                False,
                f'busy: "{active_task}" already active',
            )
        target_theta = float(goal_handle.request.target_theta)

        try:
            command = f'orientation {target_theta:.3f} {self.max_speed:.3f}'
            if not self._send_command(command):
                return self._finalize_goal(goal_handle, result, False, 'serial unavailable')

            ok, message = self._wait_for_command_response(
                'orientation',
                goal_handle,
                lambda: (
                    self._motion_feedback(feedback_msg),
                    goal_handle.publish_feedback(feedback_msg),
                ),
            )
            return self._finalize_goal(goal_handle, result, ok, message)
        finally:
            self._clear_active_task()

    async def _execute_pick(self, goal_handle):
        feedback_msg = Pick.Feedback()
        result = Pick.Result()
        accepted, active_task = self._set_active_task('pick', is_motion=False)
        if not accepted:
            return self._finalize_goal(
                goal_handle,
                result,
                False,
                f'busy: "{active_task}" already active',
            )
        try:
            direction = 1 if goal_handle.request.forward else 0
            if not self._send_command(f'pick {direction}'):
                return self._finalize_goal(goal_handle, result, False, 'serial unavailable')
            ok, message = self._wait_for_command_response(
                'pick',
                goal_handle,
                lambda: (
                    goal_handle.publish_feedback(feedback_msg),
                ),
            )
            return self._finalize_goal(goal_handle, result, ok, message)
        finally:
            self._clear_active_task()

    async def _execute_put(self, goal_handle):
        feedback_msg = Put.Feedback()
        result = Put.Result()
        accepted, active_task = self._set_active_task('put', is_motion=False)
        if not accepted:
            return self._finalize_goal(
                goal_handle,
                result,
                False,
                f'busy: "{active_task}" already active',
            )
        try:
            direction = 1 if goal_handle.request.forward else 0
            if not self._send_command(f'put {direction}'):
                return self._finalize_goal(goal_handle, result, False, 'serial unavailable')
            ok, message = self._wait_for_command_response(
                'put',
                goal_handle,
                lambda: (
                    goal_handle.publish_feedback(feedback_msg),
                ),
            )
            return self._finalize_goal(goal_handle, result, ok, message)
        finally:
            self._clear_active_task()

    async def _execute_init_odom(self, goal_handle):
        feedback_msg = InitOdom.Feedback()
        result = InitOdom.Result()
        accepted, active_task = self._set_active_task('init_odom', is_motion=False)
        if not accepted:
            return self._finalize_goal(
                goal_handle,
                result,
                False,
                f'busy: "{active_task}" already active',
            )
        try:
            if not self._send_command('init_odom'):
                return self._finalize_goal(goal_handle, result, False, 'serial unavailable')
            ok, message = self._wait_for_command_response(
                'init_odom',
                goal_handle,
                lambda: (
                    goal_handle.publish_feedback(feedback_msg),
                ),
            )
            return self._finalize_goal(goal_handle, result, ok, message)
        finally:
            self._clear_active_task()

    async def _execute_set_team(self, goal_handle):
        feedback_msg = SetTeam.Feedback()
        result = SetTeam.Result()
        accepted, active_task = self._set_active_task('set_team', is_motion=False)
        if not accepted:
            return self._finalize_goal(
                goal_handle,
                result,
                False,
                f'busy: "{active_task}" already active',
            )
        try:
            team = 1 if goal_handle.request.team else 0
            if not self._send_command(f'set_team {"blue" if team == 1 else "yellow"}'):
                return self._finalize_goal(goal_handle, result, False, 'serial unavailable')
            ok, message = self._wait_for_command_response(
                'set_team',
                goal_handle,
                lambda: (
                    goal_handle.publish_feedback(feedback_msg),
                ),
            )
            return self._finalize_goal(goal_handle, result, ok, message)
        finally:
            self._clear_active_task()

    async def _execute_stop(self, goal_handle):
        feedback_msg = Stop.Feedback()
        result = Stop.Result()
        self._stop_requested = True
        goal_handle.publish_feedback(feedback_msg)
        if not self._send_command('stop'):
            return self._finalize_goal(goal_handle, result, False, 'serial unavailable')

        ok, message = self._wait_for_command_response(
            'stop',
            goal_handle,
            lambda: (
                goal_handle.publish_feedback(feedback_msg),
            ),
        )
        return self._finalize_goal(goal_handle, result, ok, message)


def main(args=None):
    rclpy.init(args=args)
    node = ControlGateway()
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
