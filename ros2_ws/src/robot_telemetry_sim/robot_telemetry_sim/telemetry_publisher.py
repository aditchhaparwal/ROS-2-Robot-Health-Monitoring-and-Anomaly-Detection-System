import math
import random
from typing import Tuple

import rclpy
from rclpy.node import Node

from robot_interfaces.msg import RobotTelemetry


class TelemetryPublisher(Node):
    def __init__(self) -> None:
        super().__init__("robot_telemetry_publisher")
        self.publisher_ = self.create_publisher(RobotTelemetry, "robot/telemetry", 10)
        self.timer = self.create_timer(0.5, self._publish_telemetry)
        self.tick = 0
        self.get_logger().info("Telemetry publisher started.")

    def _error_code(self) -> int:
        roll = random.random()
        if roll < 0.92:
            return 0
        if roll < 0.97:
            return random.choice([42, 78, 120])
        return random.choice([101, 205, 500])

    def _base_signal(self) -> Tuple[float, float, float]:
        phase = self.tick / 8.0
        temperature = 58.0 + 10.0 * math.sin(phase)
        current = 11.0 + 2.6 * math.sin(phase * 1.8)
        vibration = 1.0 + 0.45 * math.sin(phase * 3.0)
        return temperature, current, vibration

    def _publish_telemetry(self) -> None:
        self.tick += 1
        msg = RobotTelemetry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"

        temperature, current, vibration = self._base_signal()

        msg.battery_level = max(5.0, 100.0 - (self.tick * 0.07) + random.uniform(-0.4, 0.4))
        msg.motor_temperature = temperature + random.uniform(-0.7, 0.7)
        msg.joint_velocity = 2.5 + 1.8 * math.sin(self.tick / 5.0) + random.uniform(-0.15, 0.15)
        msg.current_draw = current + random.uniform(-0.4, 0.4)
        msg.vibration = max(0.05, vibration + random.uniform(-0.1, 0.1))
        msg.error_code = self._error_code()
        msg.cpu_load = 45.0 + 25.0 * abs(math.sin(self.tick / 12.0)) + random.uniform(-4.0, 4.0)
        msg.memory_usage = 48.0 + 22.0 * abs(math.sin(self.tick / 15.0 + 0.4)) + random.uniform(-3.5, 3.5)

        # Inject occasional synthetic anomalies for demo value.
        if self.tick % 55 == 0:
            msg.motor_temperature += random.uniform(12.0, 18.0)
        if self.tick % 70 == 0:
            msg.vibration += random.uniform(1.0, 1.7)
        if self.tick % 90 == 0:
            msg.battery_level -= random.uniform(10.0, 14.0)

        self.publisher_.publish(msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TelemetryPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
