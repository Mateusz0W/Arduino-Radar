import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

PORT = "/dev/ttyACM0"  # change to the serial port your Arduino uses
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)

fig = plt.figure(figsize=(10, 4))
ax_polar = fig.add_subplot(121, projection="polar")
ax_cart = fig.add_subplot(122)
ax_cart.set_xlim(-200, 200)
ax_cart.set_ylim(0, 200)
ax_cart.set_aspect("equal")
ax_cart.set_xlabel("X (cm)")
ax_cart.set_ylabel("Y (cm)")
ax_cart.grid(True, linestyle=":", linewidth=0.5)

polar_points, = ax_polar.plot([], [], "g.")
cart_points, = ax_cart.plot([], [], "g.")


def read_scan():
    angles_deg = []
    distances = []
    while True:
        raw = ser.readline().decode(errors="ignore").strip()
        if not raw:
            break
        if raw == "END":
            return angles_deg, distances
        try:
            angle_str, dist_str = raw.split(",")
            angles_deg.append(float(angle_str))
            distances.append(float(dist_str))
        except ValueError:
            continue
    return None, None


def update(_):
    angles_deg, distances = read_scan()
    if not angles_deg:
        return polar_points, cart_points

    angles_rad = np.deg2rad(angles_deg)
    dists = np.array(distances)

    polar_points.set_data(angles_rad, dists)

    x = dists * np.sin(angles_rad)
    y = dists * np.cos(angles_rad)
    cart_points.set_data(x, y)

    ax_polar.set_rmax(max(dists) + 20)
    return polar_points, cart_points


def main():
    ani = animation.FuncAnimation(fig, update, interval=500, blit=True)
    plt.show()


if __name__ == "__main__":
    main()
