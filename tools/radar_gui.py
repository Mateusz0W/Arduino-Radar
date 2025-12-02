import threading
import queue
import time
import math
from dataclasses import dataclass
import logging

import numpy as np
import serial
from serial.tools import list_ports

# Use Tkinter + Matplotlib backend
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

@dataclass
class ScanConfig:
    resolution: int = 180  # steps within angle
    angle: int = 180       # degrees, max 270


class SerialRadarClient:
    def __init__(self):
        self.ser: serial.Serial | None = None
        self.read_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.sweep_queue: queue.Queue[list[tuple[float, float]]] = queue.Queue()

    def connect(self, port: str, baud: int = 115200, timeout: float = 1.0):
        if self.ser and self.ser.is_open:
            return
        self.ser = serial.Serial(port, baud, timeout=timeout)
        # Give Arduino time to reset on serial open
        time.sleep(2.0)
        self.stop_event.clear()
        self.read_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.read_thread.start()

    def disconnect(self):
        self.stop_event.set()
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1.0)
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None

    def is_connected(self) -> bool:
        return bool(self.ser and self.ser.is_open)

    def send_line(self, line: str):
        if not self.is_connected():
            return
        logging.info(f"Sending command: {line.strip()}")
        self.ser.write((line.strip() + "\n").encode("utf-8"))

    def apply_config(self, cfg: ScanConfig):
        # Optional: firmware may ignore; send a concise string
        self.send_line(f"Resolution: {int(cfg.resolution)}, Angle: {int(cfg.angle)}")

    def start_auto(self, enabled: bool = True):
        # Deprecated in this GUI revision
        pass

    def trigger_single_scan(self):
        # Deprecated in this GUI revision
        pass

    def _reader_loop(self):
        buf: list[tuple[float, float]] = []
        ser = self.ser
        assert ser is not None
        while not self.stop_event.is_set():
            try:
                raw = ser.readline().decode(errors="ignore").strip()
            except Exception:
                break
            if not raw:
                continue
            if raw == "END":
                if buf:
                    self.sweep_queue.put(buf)
                    buf = []
                continue
            # Accept JSON {"Angle": ..., "Distance": ...} or CSV "angle,distance"
            try:
                if raw.startswith("{"):
                    import json
                    obj = json.loads(raw)
                    a = obj.get("Angle")
                    d = obj.get("Distance")
                    if a is None or d is None:
                        raise ValueError()
                    buf.append((float(a), float(d)))
                else:
                    angle_str, dist_str = raw.split(",")
                    a = float(angle_str)
                    d = float(dist_str)
                    buf.append((a, d))
            except Exception:
                # Ignore malformed lines
                continue


class RadarGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Arduino Radar GUI")
        self.client = SerialRadarClient()
        self.cfg = ScanConfig()
        self.controls_enabled = tk.BooleanVar(value=True)  # send commands to firmware?
        self.display_rate_hz = tk.DoubleVar(value=5.0)      # visualization throttle
        self._last_draw_ts = 0.0
        self.resolution = tk.IntVar(value=int(self.cfg.resolution))
        self.angle = tk.IntVar(value=int(self.cfg.angle))

        self._build_ui()
        self._schedule_update()

    def _build_ui(self):
        # Top controls frame
        top = ttk.Frame(self.root)
        top.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        # Port selection
        ttk.Label(top, text="Port:").grid(row=0, column=0, sticky=tk.W, padx=(0, 4))
        self.port_var = tk.StringVar(value=self._default_port())
        self.port_combo = ttk.Combobox(top, textvariable=self.port_var, width=18, values=self._list_ports())
        self.port_combo.grid(row=0, column=1, padx=4)
        ttk.Button(top, text="Refresh", command=self._refresh_ports).grid(row=0, column=2, padx=4)

        # Baud
        ttk.Label(top, text="Baud:").grid(row=0, column=3, sticky=tk.W, padx=(12, 4))
        self.baud_var = tk.StringVar(value="115200")
        ttk.Entry(top, textvariable=self.baud_var, width=10).grid(row=0, column=4, padx=4)

        self.connect_btn = ttk.Button(top, text="Connect", command=self._toggle_connect)
        self.connect_btn.grid(row=0, column=5, padx=(12, 4))

        # Removed firmware-only controls for simplicity

        # Config controls
        cfg = ttk.LabelFrame(self.root, text="Scan Config")
        cfg.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0, 6))


        def add_labeled(row, col, label, widget):
            ttk.Label(cfg, text=label).grid(row=row, column=col, sticky=tk.W, padx=(0, 4), pady=3)
            widget.grid(row=row, column=col + 1, padx=(0, 10), pady=3)

        add_labeled(0, 0, "Resolution (steps):", ttk.Entry(cfg, textvariable=self.resolution, width=10))
        add_labeled(0, 2, "Angle (°):", ttk.Spinbox(cfg, from_=0, to=270, increment=1, textvariable=self.angle, width=8))

        ttk.Button(cfg, text="Apply", command=self._apply_cfg).grid(row=0, column=10, padx=6)

        # Firmware control toggle and display throttle
        ttk.Checkbutton(cfg, text="Send commands to firmware (optional)", variable=self.controls_enabled).grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(4, 0))
        ttk.Label(cfg, text="Display sweeps/sec").grid(row=1, column=4, sticky=tk.W, padx=(20, 4))
        ttk.Spinbox(cfg, from_=1, to=30, increment=1, textvariable=self.display_rate_hz, width=6).grid(row=1, column=5, sticky=tk.W)

        # Plot area
        plot_frame = ttk.Frame(self.root)
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.fig = Figure(figsize=(10, 4), dpi=100)
        self.ax_polar = self.fig.add_subplot(121, projection="polar")
        self.ax_cart = self.fig.add_subplot(122)
        self.ax_cart.set_xlim(-200, 200)
        self.ax_cart.set_ylim(0, 200)
        self.ax_cart.set_aspect("equal")
        self.ax_cart.set_xlabel("X (cm)")
        self.ax_cart.set_ylabel("Y (cm)")
        self.ax_cart.grid(True, linestyle=":", linewidth=0.5)

        self.polar_points, = self.ax_polar.plot([], [], "g.")
        self.cart_points, = self.ax_cart.plot([], [], "g.")

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _default_port(self) -> str:
        # Heuristic default
        for p in self._list_ports():
            if "ACM" in p or "USB" in p or "tty" in p:
                return p
        return "/dev/ttyACM0"

    def _list_ports(self):
        return [p.device for p in list_ports.comports()]

    def _refresh_ports(self):
        self.port_combo["values"] = self._list_ports()

    def _toggle_connect(self):
        if self.client.is_connected():
            self.client.disconnect()
            self.connect_btn.config(text="Connect")
        else:
            port = self.port_var.get()
            try:
                baud = int(self.baud_var.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid baud rate")
                return
            try:
                self.client.connect(port, baud)
            except Exception as e:
                messagebox.showerror("Connection failed", str(e))
                return
            self.connect_btn.config(text="Disconnect")
            # Optionally send config to firmware
            if self.controls_enabled.get():
                self._apply_cfg()

    def _apply_cfg(self):
        # Validate and apply Resolution and Angle
        try:
            res = int(self.resolution.get())
            ang = int(self.angle.get())
            if res < 1 or ang < 0 or ang > 270:
                raise ValueError()
            self.cfg.resolution = res
            self.cfg.angle = ang
        except (ValueError, tk.TclError):
            messagebox.showerror("Invalid values", "Resolution must be >=1 and Angle must be between 0 and 270")
            return
        if self.client.is_connected() and self.controls_enabled.get():
            self.client.apply_config(self.cfg)

    def _toggle_auto(self):
        pass

    def _single_scan(self):
        pass

    def _update_control_state(self):
        # No firmware-only controls to toggle
        pass

    def _schedule_update(self):
        self._update_plots()
        self.root.after(50, self._schedule_update)

    def _update_plots(self):
        updated = False
        # Throttle drawing to display_rate_hz
        min_interval = 1.0 / max(0.1, float(self.display_rate_hz.get()))
        now = time.time()
        while not self.client.sweep_queue.empty():
            sweep = self.client.sweep_queue.get_nowait()
            if not sweep:
                continue
            angles_deg = np.array([a for a, _ in sweep])
            dists = np.array([d for _, d in sweep])

            # No start/end filtering; data shown as received
            # Convert to radians for polar
            angles_rad = np.deg2rad(angles_deg)
            self.polar_points.set_data(angles_rad, dists)

            # Cartesian projection (assuming sensor at origin facing +Y)
            x = dists * np.sin(angles_rad)
            y = dists * np.cos(angles_rad)
            self.cart_points.set_data(x, y)

            # Adjust radial max to data range
            try:
                rmax = float(np.nanmax(dists))
                if math.isfinite(rmax) and rmax > 0:
                    self.ax_polar.set_rmax(rmax + 20)
            except ValueError:
                pass
            updated = True

        if updated and (now - self._last_draw_ts >= min_interval):
            self.canvas.draw_idle()
            self._last_draw_ts = now


def main():
    root = tk.Tk()
    RadarGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
