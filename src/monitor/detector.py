"""Calibration and sustained-noise detection using supplied readings."""

import math
from statistics import median


class Calibrator:
    """Collect level readings over a duration and calculate their median."""

    def __init__(self, duration_seconds: float = 10.0) -> None:
        """Create a calibrator for the requested duration in seconds."""
        if not math.isfinite(duration_seconds) or duration_seconds < 0:
            raise ValueError("duration_seconds must be finite and non-negative")

        self.duration_seconds = duration_seconds
        self._readings: list[float] = []
        self._start_timestamp: float | None = None
        self._latest_timestamp: float | None = None

    def add_reading(self, timestamp: float, level_dbfs: float) -> None:
        """Store a finite dBFS reading and its finite, nondecreasing timestamp."""
        if not math.isfinite(timestamp):
            raise ValueError("timestamp must be finite")
        if not math.isfinite(level_dbfs):
            raise ValueError("level_dbfs must be finite")
        if (
            self._latest_timestamp is not None
            and timestamp < self._latest_timestamp
        ):
            raise ValueError("timestamps must be nondecreasing")

        if self._start_timestamp is None:
            self._start_timestamp = timestamp
        self._latest_timestamp = timestamp
        self._readings.append(level_dbfs)

    def is_complete(self) -> bool:
        """Return whether readings span at least the configured duration."""
        return (
            self._start_timestamp is not None
            and self._latest_timestamp is not None
            and self._latest_timestamp - self._start_timestamp
            >= self.duration_seconds
        )

    def baseline(self) -> float:
        """Return the median level, or raise ValueError when no readings exist."""
        if not self._readings:
            raise ValueError("cannot calculate a baseline without readings")
        return float(median(self._readings))


class NoiseDetector:
    """Detect levels sustained above a baseline-relative threshold."""

    def __init__(
        self,
        baseline_dbfs: float,
        margin_db: float = 15.0,
        sustain_seconds: float = 5.0,
        cooldown_seconds: float = 30.0,
        enabled: bool = True,
    ) -> None:
        """Create a detector with threshold, sustain, cooldown, and mode settings."""
        if not math.isfinite(baseline_dbfs):
            raise ValueError("baseline_dbfs must be finite")
        if not math.isfinite(margin_db):
            raise ValueError("margin_db must be finite")
        if not math.isfinite(sustain_seconds) or sustain_seconds < 0:
            raise ValueError("sustain_seconds must be finite and non-negative")
        if not math.isfinite(cooldown_seconds) or cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be finite and non-negative")

        self.threshold_dbfs = baseline_dbfs + margin_db
        self.sustain_seconds = sustain_seconds
        self.cooldown_seconds = cooldown_seconds
        self.enabled = enabled
        self._sustain_start: float | None = None
        self._last_alert_time: float | None = None
        self._latest_timestamp: float | None = None

    def update(self, timestamp: float, level_dbfs: float) -> bool:
        """Process a timestamped level and return whether this reading fires."""
        if not math.isfinite(timestamp):
            raise ValueError("timestamp must be finite")
        if not math.isfinite(level_dbfs):
            raise ValueError("level_dbfs must be finite")
        if (
            self._latest_timestamp is not None
            and timestamp < self._latest_timestamp
        ):
            raise ValueError("timestamps must be nondecreasing")
        self._latest_timestamp = timestamp

        if not self.enabled:
            self._sustain_start = None
            return False

        if level_dbfs <= self.threshold_dbfs:
            self._sustain_start = None
            return False

        if self._sustain_start is None:
            self._sustain_start = timestamp
        if timestamp - self._sustain_start < self.sustain_seconds:
            return False
        if (
            self._last_alert_time is not None
            and timestamp - self._last_alert_time < self.cooldown_seconds
        ):
            return False

        self._last_alert_time = timestamp
        self._sustain_start = None
        return True

    def set_enabled(self, enabled: bool) -> None:
        """Set whether detection is active, clearing sustain when disabled."""
        self.enabled = enabled
        if not enabled:
            self._sustain_start = None
