import threading
import queue
import time
import math
from dataclasses import dataclass
import logging
import json

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
        # Queue holds individual points (angle, distance) and None for end-of-sweep
        self.sweep_queue: queue.Queue[tuple[float, float] | None] = queue.Queue()
        # Pending config to apply after current sweep ends
        self._pending_cfg: ScanConfig | None = None
        # Last known config; used to keep sweeps continuous
        self._current_cfg: ScanConfig = ScanConfig()

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
        
        if hasattr(self, "_pending_cfg"):
            self._pending_cfg = None

    def is_connected(self) -> bool:
        return bool(self.ser and self.ser.is_open)

    def send_line(self, line: str):
        if not self.is_connected():
            return
        logging.info(f"Sending command: {line.strip()}")
        try:
            self.ser.write((line.strip() + "\n").encode("utf-8"))
        except Exception as e:
            logging.error(f"Serial write failed: {e}")

    def apply_config(self, cfg: ScanConfig):
        # Buffer config; will be sent at end-of-sweep (when END arrives)
        self._pending_cfg = cfg
        self._current_cfg = cfg

    def start_auto(self, enabled: bool = True):
        # Deprecated in this GUI revision
        pass

    def trigger_single_scan(self):
        # Deprecated in this GUI revision
        pass

    def _reader_loop(self):
        ser = self.ser
        assert ser is not None
        while not self.stop_event.is_set():
            try:
                raw = ser.readline().decode(errors="ignore").strip()
            except Exception:
                break
            if not raw:
                continue
            logging.debug(f"Serial raw: {raw}")
            if raw == "END":
                self.sweep_queue.put(None)
                # Always send a JSON config to allow next sweep to start
                try:
                    cfg = self._pending_cfg if self._pending_cfg is not None else self._current_cfg
                    res = int(cfg.resolution)
                    ang = int(cfg.angle)
                    payload = {"Angle": ang, "Resolution": res}
                    self.send_line(json.dumps(payload))
                except Exception as e:
                    logging.error(f"Failed to send config JSON: {e}")
                finally:
                    self._pending_cfg = None
                continue
            try:
                if raw.startswith("{"):
                    import json
                    obj = json.loads(raw)
                    a = obj.get("Angle", obj.get("angle"))
                    d = obj.get("Distance", obj.get("distance"))
                    if a is None or d is None:
                        raise ValueError()
                    logging.info(f"Serial parsed -> angle={a}, distance={d}")
                    self.sweep_queue.put((float(a), float(d)))
                else:
                    angle_str, dist_str = raw.split(",")
                    a = float(angle_str)
                    d = float(dist_str)
                    logging.info(f"Serial parsed -> angle={a}, distance={d}")
                    self.sweep_queue.put((a, d))
            except Exception:
                # Ignore malformed lines
                continue

    # No simulator loop; always read from serial


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

        # Buffers for current sweep
        self._current_angles: list[float] = []
        self._current_dists: list[float] = []
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
        # Simulation option removed; always listen to serial

        # Config controls
        cfg = ttk.LabelFrame(self.root, text="Scan Config")
        cfg.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0, 6))


        def add_labeled(row, col, label, widget):
            ttk.Label(cfg, text=label).grid(row=row, column=col, sticky=tk.W, padx=(0, 4), pady=3)
            widget.grid(row=row, column=col + 1, padx=(0, 10), pady=3)

        add_labeled(0, 0, "Resolution (steps):", ttk.Entry(cfg, textvariable=self.resolution, width=10))
        add_labeled(0, 2, "Angle (°):", ttk.Spinbox(cfg, from_=0, to=270, increment=1, textvariable=self.angle, width=8))

        ttk.Button(cfg, text="Apply", command=self._apply_cfg).grid(row=0, column=10, padx=6)

        # Plot area
        plot_frame = ttk.Frame(self.root)
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.fig = Figure(figsize=(6, 6), dpi=100)
        self.ax_polar = self.fig.add_subplot(111, projection="polar")
        self.polar_points, = self.ax_polar.plot([], [], "g.")

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
            # No automatic config apply on connect; user can press Apply

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
        
        min_interval = 1.0 / max(0.1, float(self.display_rate_hz.get()))
        now = time.time()
        while not self.client.sweep_queue.empty():
            item = self.client.sweep_queue.get_nowait()
            if item is None:
                
                logging.info(f"Sweep complete: {len(self._current_angles)} points")
                self._current_angles = []
                self._current_dists = []
                continue
            angle_deg, dist = item
            
            if self._current_angles and angle_deg < self._current_angles[-1]:
                self._current_angles = []
                self._current_dists = []
            
            self._current_angles.append(angle_deg)
            self._current_dists.append(dist)
            angles_deg = np.array(self._current_angles)
            dists = np.array(self._current_dists)
            angles_rad = np.deg2rad(angles_deg)
            self.polar_points.set_data(angles_rad, dists)
            
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
