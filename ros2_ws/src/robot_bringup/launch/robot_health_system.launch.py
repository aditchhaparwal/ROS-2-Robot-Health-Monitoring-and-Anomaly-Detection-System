from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    config_path_arg = DeclareLaunchArgument(
        "config_path",
        default_value="",
        description="Optional path to detector YAML config.",
    )

    telemetry_node = Node(
        package="robot_telemetry_sim",
        executable="telemetry_publisher",
        name="robot_telemetry_publisher",
        output="screen",
    )

    monitor_node = Node(
        package="robot_health_monitor",
        executable="health_monitor",
        name="robot_health_monitor",
        output="screen",
        parameters=[{"config_path": LaunchConfiguration("config_path")}],
    )

    alert_node = Node(
        package="robot_alert_manager",
        executable="alert_manager",
        name="robot_alert_manager",
        output="screen",
    )

    bridge_node = Node(
        package="robot_dashboard_bridge",
        executable="dashboard_bridge",
        name="robot_dashboard_bridge",
        output="screen",
    )

    return LaunchDescription(
        [
            config_path_arg,
            telemetry_node,
            monitor_node,
            alert_node,
            bridge_node,
        ]
    )
