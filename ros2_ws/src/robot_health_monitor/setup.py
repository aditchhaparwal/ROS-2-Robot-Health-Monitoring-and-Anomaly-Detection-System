from setuptools import find_packages, setup

package_name = "robot_health_monitor"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["tests"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools", "pyyaml"],
    zip_safe=True,
    maintainer="Project Maintainer",
    maintainer_email="maintainer@example.com",
    description="Anomaly detector for robot telemetry.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "health_monitor = robot_health_monitor.health_monitor_node:main",
        ],
    },
)
