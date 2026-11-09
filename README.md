# Adaptive Classroom Noise Monitor

## Requirements

- Python 3.10 or newer
- A microphone supported by your operating system

## Setup on Windows PowerShell

Open PowerShell in this project directory, then run:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell prevents activating the virtual environment, run this once for
the current user and open a new PowerShell window:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Run tests

```powershell
python -m pytest
```

## Run the live level meter

```powershell
python -m src.monitor.main
```

The program lists available input devices and reads from the default
microphone. It displays the current RMS level in dBFS and stops cleanly with
Ctrl+C. Audio samples are processed in memory only and are not saved.
