"""RMS-based audio level measurement."""

import numpy as np


SILENCE_FLOOR_DBFS = -120.0


def calculate_dbfs(samples: np.ndarray) -> float:
    """Return the RMS level of samples in dBFS, using -120 dBFS for silence.

    Samples are normalized so an RMS value of 1.0 corresponds to 0 dBFS.
    """
    values = np.asarray(samples)
    if values.size == 0:
        raise ValueError("samples must not be empty")
    if not np.issubdtype(values.dtype, np.number):
        raise TypeError("samples must contain numeric values")
    if not np.all(np.isfinite(values)):
        raise ValueError("samples must contain only finite values")

    rms = float(np.sqrt(np.mean(np.square(values, dtype=np.float64))))
    if rms == 0.0:
        return SILENCE_FLOOR_DBFS

    return max(20.0 * float(np.log10(rms)), SILENCE_FLOOR_DBFS)
