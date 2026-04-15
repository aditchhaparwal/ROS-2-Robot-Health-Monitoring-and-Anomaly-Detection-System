import json
from typing import List

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from robot_interfaces.msg import RobotAlert, RobotTelemetry

from .config import load_detector_config
from .detector import AnomalyDetector
from .models import DetectorAlert, TelemetrySample


class RobotHealthMonitor(Node):
    def __init__(self) -> None:
        super().__init__("robot_health_monitor")
        self.declare_parameter("config_path", "")
        config_path = self.get_parameter("config_path").value
        config = load_detector_config(config_path)
        self.detector = AnomalyDetector(config)

        self.telemetry_sub = self.create_subscription(
            RobotTelemetry, "robot/telemetry", self._on_telemetry, 10
        )
        self.alert_pub = self.create_publisher(RobotAlert, "robot/alerts/raw", 10)
        self.health_pub = self.create_publisher(String, "robot/health/status", 10)
        self.get_logger().info("Robot health monitor started.")

    def _on_telemetry(self, msg: RobotTelemetry) -> None:
        sample = TelemetrySample(
            battery_level=float(msg.battery_level),
            motor_temperature=float(msg.motor_temperature),
            joint_velocity=float(msg.joint_velocity),
            current_draw=float(msg.current_draw),
            vibration=float(msg.vibration),
            error_code=int(msg.error_code),
            cpu_load=float(msg.cpu_load),
            memory_usage=float(msg.memory_usage),
        )
        alerts = self.detector.evaluate(sample)
        self._publish_status(alerts, sample)
        for alert in alerts:
            self._publish_alert(alert, msg)

    def _publish_status(self, alerts: List[DetectorAlert], sample: TelemetrySample) -> None:
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        overall = "nominal"
        if alerts:
            overall = max(alerts, key=lambda a: severity_order.get(a.severity, 0)).severity
        payload = {
            "status": overall,
            "active_alerts": len(alerts),
            "battery_level": sample.battery_level,
            "error_code": sample.error_code,
        }
        self.health_pub.publish(String(data=json.dumps(payload)))

    def _publish_alert(self, alert: DetectorAlert, telemetry_msg: RobotTelemetry) -> None:
        out = RobotAlert()
        out.header = telemetry_msg.header
        out.alert_id = f"{self.get_clock().now().nanoseconds}"
        out.source = "robot_health_monitor"
        out.severity = alert.severity
        out.probable_root_cause = alert.probable_root_cause
        out.message = alert.message
        out.tags = alert.tags
        out.active = True
        self.alert_pub.publish(out)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = RobotHealthMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
