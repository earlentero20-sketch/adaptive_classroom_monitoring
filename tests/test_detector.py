"""Tests for calibration and sustained-noise detection."""

import pytest

from src.monitor.detector import Calibrator, NoiseDetector


def test_calibrator_baseline_is_median() -> None:
    """Calibration computes the median of collected levels."""
    calibrator = Calibrator()
    for timestamp, level in enumerate([-40.0, -42.0, -38.0, -50.0, -44.0]):
        calibrator.add_reading(float(timestamp), level)

    assert calibrator.baseline() == -42.0


def test_calibrator_incomplete_before_duration() -> None:
    """Calibration remains incomplete until its duration has elapsed."""
    calibrator = Calibrator(duration_seconds=10.0)
    calibrator.add_reading(2.0, -40.0)
    calibrator.add_reading(11.9, -42.0)

    assert not calibrator.is_complete()


def test_calibrator_complete_after_duration() -> None:
    """Calibration completes once the latest reading spans its duration."""
    calibrator = Calibrator(duration_seconds=10.0)
    calibrator.add_reading(2.0, -40.0)
    calibrator.add_reading(12.0, -42.0)

    assert calibrator.is_complete()


def test_calibrator_empty_raises_value_error() -> None:
    """An empty calibrator cannot produce a baseline."""
    with pytest.raises(ValueError, match="without readings"):
        Calibrator().baseline()


def test_single_loud_spike_does_not_fire() -> None:
    """A loud reading followed by quiet readings does not meet sustain time."""
    detector = NoiseDetector(-50.0, margin_db=10.0, sustain_seconds=3.0)

    results = [
        detector.update(0.0, -20.0),
        detector.update(1.0, -50.0),
        detector.update(2.0, -20.0),
        detector.update(3.0, -50.0),
    ]

    assert results == [False, False, False, False]


def test_sustained_loudness_fires_once() -> None:
    """Continuous loudness fires once after the sustain interval."""
    detector = NoiseDetector(-50.0, margin_db=10.0, sustain_seconds=5.0)
    results = [detector.update(float(time), -20.0) for time in range(7)]

    assert results.count(True) == 1
    assert results[5] is True


def test_cooldown_blocks_second_alert() -> None:
    """Continuous loudness cannot fire again before cooldown has passed."""
    detector = NoiseDetector(
        -50.0,
        margin_db=10.0,
        sustain_seconds=2.0,
        cooldown_seconds=5.0,
    )
    results = [detector.update(float(time), -20.0) for time in range(8)]

    assert [time for time, fired in enumerate(results) if fired] == [2, 7]


def test_disabled_detector_never_fires() -> None:
    """Loud readings do not fire while the detector is disabled."""
    detector = NoiseDetector(-50.0, margin_db=10.0, enabled=False)

    assert all(not detector.update(float(time), -20.0) for time in range(21))


def test_re_enabling_requires_full_sustain_again() -> None:
    """Re-enabling starts a fresh sustain interval."""
    detector = NoiseDetector(
        -50.0, margin_db=10.0, sustain_seconds=3.0, enabled=False
    )
    assert all(not detector.update(float(time), -20.0) for time in range(5))

    detector.set_enabled(True)
    assert detector.update(5.0, -20.0) is False
    assert detector.update(7.0, -20.0) is False
    assert detector.update(8.0, -20.0) is True


def test_non_finite_level_raises_value_error() -> None:
    """Calibration and detection reject non-finite levels."""
    calibrator = Calibrator()
    detector = NoiseDetector(-50.0)

    with pytest.raises(ValueError, match="level_dbfs must be finite"):
        calibrator.add_reading(0.0, float("nan"))
    with pytest.raises(ValueError, match="level_dbfs must be finite"):
        detector.update(0.0, float("inf"))
