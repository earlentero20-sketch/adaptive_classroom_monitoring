"""Live microphone level display."""

import queue
import sys
from typing import Any

import sounddevice as sd

from .level_meter import calculate_dbfs


def main() -> None:
    """List input devices and display the default microphone level."""
    try:
        devices = sd.query_devices()
    except sd.PortAudioError as error:
        print(f"Unable to query audio devices: {error}", file=sys.stderr)
        return

    input_devices = [
        (index, device)
        for index, device in enumerate(devices)
        if device["max_input_channels"] > 0
    ]
    print("Available input devices:")
    if input_devices:
        for index, device in input_devices:
            print(f"  {index}: {device['name']}")
    else:
        print("  No input devices found.")
        return

    try:
        default_device = sd.query_devices(kind="input")
    except sd.PortAudioError as error:
        print(f"No default microphone is available: {error}", file=sys.stderr)
        return

    levels: queue.Queue[float] = queue.Queue(maxsize=1)

    def receive_audio(indata: Any, frames: int, timing: Any, status: Any) -> None:
        """Measure each incoming block without retaining audio samples."""
        del frames, timing
        if status:
            print(f"Audio input warning: {status}", file=sys.stderr)
        level = calculate_dbfs(indata[:, 0])
        try:
            levels.put_nowait(level)
        except queue.Full:
            try:
                levels.get_nowait()
            except queue.Empty:
                pass
            levels.put_nowait(level)

    try:
        with sd.InputStream(
            samplerate=default_device["default_samplerate"],
            channels=1,
            callback=receive_audio,
        ):
            print("Listening to the default microphone. Press Ctrl+C to stop.")
            while True:
                try:
                    level = levels.get(timeout=0.1)
                    print(f"\rLevel: {level:6.1f} dBFS", end="", flush=True)
                except queue.Empty:
                    continue
    except KeyboardInterrupt:
        print("\nStopped.")
    except sd.PortAudioError as error:
        print(f"Unable to open the default microphone: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
