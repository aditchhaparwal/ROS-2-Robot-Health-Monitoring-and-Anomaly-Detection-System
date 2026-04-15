import json
from datetime import datetime, timezone
from typing import Any, Dict

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from robot_interfaces.msg import RobotTelemetry


class DashboardBridge(Node):
    def __init__(self) -> None:
        super().__init__("robot_dashboard_bridge")
        self.latest: Dict[str, Any] = {
            "telemetry": {},
            "status": {},
            "alerts": {},
            "updated_at": None,
        }
        self.create_subscription(RobotTelemetry, "robot/telemetry", self._on_telemetry, 10)
        self.create_subscription(String, "robot/health/status", self._on_status, 10)
        self.create_subscription(String, "robot/alerts/history", self._on_alerts, 10)
        self.bridge_pub = self.create_publisher(String, "robot/dashboard/json", 10)
        self.get_logger().info("Dashboard bridge started.")

    def _on_telemetry(self, msg: RobotTelemetry) -> None:
        self.latest["telemetry"] = {
            "battery_level": msg.battery_level,
            "motor_temperature": msg.motor_temperature,
            "joint_velocity": msg.joint_velocity,
            "current_draw": msg.current_draw,
            "vibration": msg.vibration,
            "error_code": msg.error_code,
            "cpu_load": msg.cpu_load,
            "memory_usage": msg.memory_usage,
        }
        self._publish()

    def _on_status(self, msg: String) -> None:
        self.latest["status"] = self._safe_json(msg.data)
        self._publish()

    def _on_alerts(self, msg: String) -> None:
        self.latest["alerts"] = self._safe_json(msg.data)
        self._publish()

    def _publish(self) -> None:
        self.latest["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.bridge_pub.publish(String(data=json.dumps(self.latest)))

    @staticmethod
    def _safe_json(raw: str) -> Dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}


def main(args=None) -> None:
    rclpy.init(args=args)
    node = DashboardBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
