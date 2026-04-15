from setuptools import find_packages, setup

package_name = "robot_alert_manager"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["tests"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Project Maintainer",
    maintainer_email="maintainer@example.com",
    description="Aggregates and enriches robot alerts.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "alert_manager = robot_alert_manager.alert_manager_node:main",
        ],
    },
)
