from robot_health_monitor.detector import AnomalyDetector
from robot_health_monitor.models import TelemetrySample


def _config():
    return {
        "battery_level": {"min": 20.0},
        "motor_temperature": {"max": 85.0},
        "joint_velocity": {"max": 6.0},
        "current_draw": {"max": 18.0},
        "vibration": {"max": 2.5},
        "cpu_load": {"max": 90.0},
        "memory_usage": {"max": 92.0},
        "drift": {"window_size": 3, "motor_temperature_delta": 5.0, "current_draw_delta": 3.0, "vibration_delta": 0.6},
        "spike": {"window_size": 3, "multiplier": 1.6},
        "error_codes": {"critical": [500], "warning": [42]},
    }


def _sample(**kwargs):
    data = {
        "battery_level": 70.0,
        "motor_temperature": 60.0,
        "joint_velocity": 2.2,
        "current_draw": 9.5,
        "vibration": 1.0,
        "error_code": 0,
        "cpu_load": 40.0,
        "memory_usage": 45.0,
    }
    data.update(kwargs)
    return TelemetrySample(**data)


def test_threshold_detection_battery_and_temperature():
    detector = AnomalyDetector(_config())
    alerts = detector.evaluate(_sample(battery_level=15.0, motor_temperature=91.0))
    messages = [a.message for a in alerts]
    assert any("Battery level low" in m for m in messages)
    assert any("Motor temperature high" in m for m in messages)


def test_drift_detection_after_warmup():
    detector = AnomalyDetector(_config())
    detector.evaluate(_sample(motor_temperature=60.0))
    detector.evaluate(_sample(motor_temperature=61.0))
    detector.evaluate(_sample(motor_temperature=60.5))

    alerts = detector.evaluate(_sample(motor_temperature=70.5))
    assert any("drift" in a.message.lower() for a in alerts)


def test_spike_detection():
    detector = AnomalyDetector(_config())
    detector.evaluate(_sample(vibration=1.0))
    detector.evaluate(_sample(vibration=1.1))
    detector.evaluate(_sample(vibration=1.0))

    alerts = detector.evaluate(_sample(vibration=2.2))
    assert any("Sudden spike" in a.message for a in alerts)


def test_error_code_classification():
    detector = AnomalyDetector(_config())
    alerts = detector.evaluate(_sample(error_code=500))
    assert len(alerts) == 1
    assert alerts[0].severity == "critical"
