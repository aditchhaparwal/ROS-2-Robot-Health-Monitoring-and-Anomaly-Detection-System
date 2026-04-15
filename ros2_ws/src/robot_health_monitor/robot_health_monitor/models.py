from dataclasses import dataclass, field
from typing import List


@dataclass
class TelemetrySample:
    battery_level: float
    motor_temperature: float
    joint_velocity: float
    current_draw: float
    vibration: float
    error_code: int
    cpu_load: float
    memory_usage: float


@dataclass
class DetectorAlert:
    severity: str
    probable_root_cause: str
    message: str
    tags: List[str] = field(default_factory=list)
