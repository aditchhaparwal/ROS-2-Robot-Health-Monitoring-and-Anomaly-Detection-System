import json
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, List

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from robot_interfaces.msg import RobotAlert


class RobotAlertManager(Node):
    def __init__(self) -> None:
        super().__init__("robot_alert_manager")
        self.raw_alert_sub = self.create_subscription(
            RobotAlert, "robot/alerts/raw", self._on_raw_alert, 10
        )
        self.alert_stream_pub = self.create_publisher(String, "robot/alerts/stream", 10)
        self.alert_history_pub = self.create_publisher(String, "robot/alerts/history", 10)
        self.alert_buffer: Deque[Dict] = deque(maxlen=150)
        self.get_logger().info("Robot alert manager started.")

    def _on_raw_alert(self, msg: RobotAlert) -> None:
        event = {
            "alert_id": msg.alert_id,
            "source": msg.source,
            "severity": msg.severity,
            "probable_root_cause": msg.probable_root_cause,
            "message": msg.message,
            "tags": list(msg.tags),
            "active": bool(msg.active),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.alert_buffer.append(event)
        self.alert_stream_pub.publish(String(data=json.dumps(event)))
        self.alert_history_pub.publish(
            String(
                data=json.dumps(
                    {
                        "total_alerts": len(self.alert_buffer),
                        "latest_severity": event["severity"],
                        "recent_alerts": self._recent_alerts(),
                    }
                )
            )
        )

    def _recent_alerts(self) -> List[Dict]:
        return list(self.alert_buffer)[-10:]


def main(args=None) -> None:
    rclpy.init(args=args)
    node = RobotAlertManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
