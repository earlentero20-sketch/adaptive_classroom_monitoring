"""Tests for RMS-based dBFS measurement."""

import numpy as np
import pytest

from src.monitor.level_meter import calculate_dbfs


def test_silence_returns_finite_floor() -> None:
    """Silence maps to the finite -120 dBFS floor."""
    assert calculate_dbfs(np.zeros(1024)) == -120.0


def test_full_scale_rms_sine_is_about_zero_dbfs() -> None:
    """A sine wave with RMS amplitude 1.0 maps to 0 dBFS."""
    phase = np.linspace(0.0, 2.0 * np.pi * 8, 1024, endpoint=False)
    samples = np.sqrt(2.0) * np.sin(phase)

    assert calculate_dbfs(samples) == pytest.approx(0.0, abs=0.02)


def test_half_amplitude_sine_is_about_minus_six_dbfs() -> None:
    """A sine wave at half the full-scale RMS amplitude maps to about -6 dBFS."""
    phase = np.linspace(0.0, 2.0 * np.pi * 8, 1024, endpoint=False)
    samples = (np.sqrt(2.0) / 2.0) * np.sin(phase)

    assert calculate_dbfs(samples) == pytest.approx(-6.0206, abs=0.02)


def test_empty_samples_raise_clear_error() -> None:
    """Empty sample arrays are rejected with a clear message."""
    with pytest.raises(ValueError, match="samples must not be empty"):
        calculate_dbfs(np.array([]))
