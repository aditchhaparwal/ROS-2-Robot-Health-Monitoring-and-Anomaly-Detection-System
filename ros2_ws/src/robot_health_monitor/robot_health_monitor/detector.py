from collections import defaultdict, deque
from statistics import mean
from typing import Deque, Dict, List

from .models import DetectorAlert, TelemetrySample


class AnomalyDetector:
    def __init__(self, config: Dict):
        self.config = config
        self.drift_window = int(config.get("drift", {}).get("window_size", 12))
        self.spike_window = int(config.get("spike", {}).get("window_size", 8))
        self.spike_multiplier = float(config.get("spike", {}).get("multiplier", 1.8))

        self.history: Dict[str, Deque[float]] = defaultdict(
            lambda: deque(maxlen=max(self.drift_window, self.spike_window))
        )

    def evaluate(self, sample: TelemetrySample) -> List[DetectorAlert]:
        alerts: List[DetectorAlert] = []
        alerts.extend(self._threshold_alerts(sample))
        alerts.extend(self._drift_alerts(sample))
        alerts.extend(self._spike_alerts(sample))
        alerts.extend(self._error_code_alerts(sample))
        self._update_history(sample)
        return alerts

    def _threshold_alerts(self, sample: TelemetrySample) -> List[DetectorAlert]:
        cfg = self.config
        alerts: List[DetectorAlert] = []

        if sample.battery_level < cfg["battery_level"]["min"]:
            alerts.append(
                DetectorAlert(
                    severity="high",
                    probable_root_cause="Power subsystem degradation",
                    message=f"Battery level low: {sample.battery_level:.1f}%",
                    tags=["battery", "threshold"],
                )
            )
        if sample.motor_temperature > cfg["motor_temperature"]["max"]:
            alerts.append(
                DetectorAlert(
                    severity="critical",
                    probable_root_cause="Motor overheating",
                    message=f"Motor temperature high: {sample.motor_temperature:.1f}C",
                    tags=["motor", "temperature", "threshold"],
                )
            )
        if abs(sample.joint_velocity) > cfg["joint_velocity"]["max"]:
            alerts.append(
                DetectorAlert(
                    severity="medium",
                    probable_root_cause="Joint control instability",
                    message=f"Joint velocity above limit: {sample.joint_velocity:.2f} rad/s",
                    tags=["joint", "velocity", "threshold"],
                )
            )
        if sample.current_draw > cfg["current_draw"]["max"]:
            alerts.append(
                DetectorAlert(
                    severity="high",
                    probable_root_cause="Actuator overcurrent",
                    message=f"Current draw above limit: {sample.current_draw:.2f} A",
                    tags=["power", "current", "threshold"],
                )
            )
        if sample.vibration > cfg["vibration"]["max"]:
            alerts.append(
                DetectorAlert(
                    severity="high",
                    probable_root_cause="Mechanical imbalance or wear",
                    message=f"Vibration above limit: {sample.vibration:.2f} g",
                    tags=["vibration", "mechanical", "threshold"],
                )
            )
        if sample.cpu_load > cfg["cpu_load"]["max"] or sample.memory_usage > cfg["memory_usage"]["max"]:
            alerts.append(
                DetectorAlert(
                    severity="medium",
                    probable_root_cause="Controller resource saturation",
                    message=(
                        f"Controller load high (CPU {sample.cpu_load:.1f}%, "
                        f"RAM {sample.memory_usage:.1f}%)"
                    ),
                    tags=["controller", "resources", "threshold"],
                )
            )
        return alerts

    def _drift_alerts(self, sample: TelemetrySample) -> List[DetectorAlert]:
        drift_cfg = self.config.get("drift", {})
        alerts: List[DetectorAlert] = []

        checks = {
            "motor_temperature": (
                sample.motor_temperature,
                drift_cfg.get("motor_temperature_delta", 8.0),
                "Motor temperature drift",
                "cooling_efficiency_loss",
            ),
            "current_draw": (
                sample.current_draw,
                drift_cfg.get("current_draw_delta", 4.0),
                "Current draw drift",
                "actuator_friction_growth",
            ),
            "vibration": (
                sample.vibration,
                drift_cfg.get("vibration_delta", 0.8),
                "Vibration drift",
                "bearing_or_alignment_degradation",
            ),
        }

        for signal, (value, delta_limit, label, cause) in checks.items():
            window = self.history[signal]
            if len(window) < self.drift_window:
                continue
            avg = mean(window)
            if value - avg > float(delta_limit):
                alerts.append(
                    DetectorAlert(
                        severity="medium",
                        probable_root_cause=cause,
                        message=f"{label}: current={value:.2f}, baseline={avg:.2f}",
                        tags=[signal, "drift"],
                    )
                )
        return alerts

    def _spike_alerts(self, sample: TelemetrySample) -> List[DetectorAlert]:
        alerts: List[DetectorAlert] = []
        checks = {
            "motor_temperature": sample.motor_temperature,
            "current_draw": sample.current_draw,
            "vibration": sample.vibration,
        }

        for signal, value in checks.items():
            window = self.history[signal]
            if len(window) < self.spike_window:
                continue
            baseline = max(mean(window), 0.0001)
            if value > baseline * self.spike_multiplier:
                alerts.append(
                    DetectorAlert(
                        severity="high",
                        probable_root_cause=f"{signal}_transient_spike",
                        message=f"Sudden spike in {signal}: {value:.2f} vs baseline {baseline:.2f}",
                        tags=[signal, "spike"],
                    )
                )
        return alerts

    def _error_code_alerts(self, sample: TelemetrySample) -> List[DetectorAlert]:
        code = int(sample.error_code)
        if code == 0:
            return []

        critical_codes = set(self.config.get("error_codes", {}).get("critical", []))
        warning_codes = set(self.config.get("error_codes", {}).get("warning", []))
        if code in critical_codes:
            return [
                DetectorAlert(
                    severity="critical",
                    probable_root_cause="controller_reported_critical_fault",
                    message=f"Critical controller error code: {code}",
                    tags=["error_code", "critical"],
                )
            ]
        if code in warning_codes:
            return [
                DetectorAlert(
                    severity="medium",
                    probable_root_cause="controller_reported_warning",
                    message=f"Controller warning code: {code}",
                    tags=["error_code", "warning"],
                )
            ]
        return [
            DetectorAlert(
                severity="low",
                probable_root_cause="unknown_controller_code",
                message=f"Unknown non-zero controller code: {code}",
                tags=["error_code", "unknown"],
            )
        ]

    def _update_history(self, sample: TelemetrySample) -> None:
        self.history["motor_temperature"].append(sample.motor_temperature)
        self.history["current_draw"].append(sample.current_draw)
        self.history["vibration"].append(sample.vibration)
