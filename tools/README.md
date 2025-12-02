# Radar GUI and Tools

This folder contains Python tools to interact with the Arduino radar:

- `radar_gui.py` — Tkinter GUI with live 360° view and controls for angle range and rotation speed.
- `radar_plot.py` — Minimal matplotlib live plot (no controls).
- `serial_reader.py` — Simple CSV recorder.

## GUI features

- Connect/disconnect to a serial port.
- Configure scan range (start°..end°), max speed, acceleration, and per-sample delay.
- Toggle auto-scan (ping-pong) or trigger a single scan.
- Visualize points in polar and Cartesian projections.

## Serial data format (current firmware)

The plots expect the Arduino to continuously print lines in the format:

```
<angle_degrees>,<distance_cm>
...
END
```

That is, a sweep consists of multiple angle/distance lines terminated by a single `END` line. The GUI will visualize each completed sweep when `END` is received.

Advanced controls (sending commands to change range/speed) are optional and require matching firmware support. You can enable/disable this in the GUI using the "Send commands to firmware (experimental)" toggle.

## Requirements

Python packages (see `requirements.txt` at repo root):

- matplotlib
- numpy
- pyserial

Install into a venv and run:

```
python tools/radar_gui.py
```

Adjust the serial port as needed (e.g., `/dev/ttyACM0` on Linux).
