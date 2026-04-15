FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY ros2_ws /app/ros2_ws
COPY config /app/config
COPY api /app/api

WORKDIR /app/ros2_ws
RUN . /opt/ros/humble/setup.sh && colcon build

CMD ["/bin/bash", "-lc", ". /opt/ros/humble/setup.sh && . /app/ros2_ws/install/setup.bash && ros2 launch robot_bringup robot_health_system.launch.py"]
