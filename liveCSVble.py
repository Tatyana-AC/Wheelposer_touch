import asyncio
from bleak import BleakClient, BleakScanner
import sys
import termios
import tty
import select
from datetime import datetime
import os
import csv
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

MESSAGE_SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
MESSAGE_CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
DEVICE_NAME = "ArduinoNano33"

recording = False
session_started = False
recorded_data = []
session_file = None
csv_writer = None
session_name = ""
client = None  # Will be initialized in run()
live_values = deque(maxlen=200)
live_touch = deque(maxlen=200)
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
marker = ax.scatter([], [], color='red', s=15)

# Notification handler
def handle_notification(sender, data):
    global recording, session_started, csv_writer, recorded_data
    message = data.decode('utf-8').strip()
    if session_started:
        print(f"[BLE] {message}")

    try:
        value = float(message)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        recorded_data.append((timestamp, value))
        if recording and csv_writer:
            threshold = sum(live_values) / len(live_values) * 0.92 if live_values else 0
            touch = 1 if value < threshold else 0
            csv_writer.writerow([timestamp, value, touch])
    except ValueError:
        return
    threshold = sum(live_values) / len(live_values) * 0.92 if live_values else 0
    touch = 1 if value < threshold else 0

    live_values.append(value)
    live_touch.append(touch)

    

# Scan and connect to the Arduino
async def find_arduino():
    print(f"Scanning for {DEVICE_NAME}...")
    device = await BleakScanner.find_device_by_name(DEVICE_NAME)
    if device is None:
        print(f"Could not find {DEVICE_NAME}")
        return None
    print(f"Found {DEVICE_NAME} at {device.address}")
    return device

# Non-blocking keypress check (macOS/Linux)
def is_key_pressed():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    return dr

def read_key():
    return sys.stdin.read(1) if is_key_pressed() else None



async def keypress_monitor():
    global recording, session_started, session_file, csv_writer, recorded_data, session_name, client
    print("Type 'start' then your session name to begin. Press 'e' to end session or 'q' to quit.")
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    try:
        buffer = ""
        typing_session_name = False
        while True:
            if is_key_pressed():
                char = sys.stdin.read(1)

                if not typing_session_name:
                    if char == '\n':
                        print()
                        command = buffer.strip()
                        buffer = ""
                        if command.lower() == "start":
                            typing_session_name = True
                            print("Enter session name:")
                        else:
                            print(f"Unknown command: {command}")
                    else:
                        buffer += char
                        print(char, end='', flush=True)
                else:
                    if char == '\n':
                        session_name = buffer.strip()
                        buffer = ""
                        typing_session_name = False
                        os.makedirs("data", exist_ok=True)
                        recorded_data = []
                        filename = os.path.join("data", f"session_{session_name}.csv")
                        session_file = open(filename, mode='w', newline='')
                        csv_writer = csv.writer(session_file)
                        csv_writer.writerow(["Timestamp", "Value", "Touch"])
                        recording = True
                        session_started = True
                        if client:
                            await client.write_gatt_char(MESSAGE_CHARACTERISTIC_UUID, b"session_on")
                    else:
                        buffer += char
                        print(char, end='', flush=True)

                if not typing_session_name and char in ['e', 'q']:
                    if char == 'q':
                        print("\nExiting...")
                        if client:
                            await client.write_gatt_char(MESSAGE_CHARACTERISTIC_UUID, b"session_off")
                        
                        
                        os._exit(0)
                    elif char == 'e':
                        print("\nEnding session...")
                        if recording:
                            recording = False
                            session_started = False
                            if client:
                                await client.write_gatt_char(MESSAGE_CHARACTERISTIC_UUID, b"session_off")
                            print("Recording stopped.")
                            analog_filename = os.path.join("data", f"session_{session_name}.png")
                            plt.savefig(analog_filename)
                            print(f"Plot saved as: {analog_filename}")
                            print("Recording stopped.")
                        user_input = input("Start a new session? (y/n): ").strip().lower()
                        if user_input == 'y':
                            print("Type 'start' then your session name to begin.")
                        else:
                            print("No active recording.")

            await asyncio.sleep(0.1)
            plt.pause(0.001)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def update_plot(frame):
    y = list(live_values)
    x = list(range(len(y)))
    line.set_data(x, y)
    import numpy as np
    points = np.array([[i, y[i]] for i in range(len(y)) if live_touch[i] == 1])
    if len(points) == 0:
        points = np.empty((0, 2))
    marker.set_offsets(points)
    ax.set_xlim(0, 200)
    if y:
        ax.set_ylim(min(y) * 0.95, max(y) * 1.05)
    return line, marker

async def run():
    global client
    device = await find_arduino()
    if not device:
        return

    print(f"Connecting to {device.address}...")
    client = BleakClient(device)
    async with client:
        print(f"Connected to {device.address}")
        await client.start_notify(MESSAGE_CHARACTERISTIC_UUID, handle_notification)
        ani = animation.FuncAnimation(fig, update_plot, interval=200, blit=False)
        plt.ion()
        plt.draw()
        print("Ready to receive commands.")

        try:
            await keypress_monitor()
        except KeyboardInterrupt:
            print("Interrupted by user.")
        finally:
            await client.stop_notify(MESSAGE_CHARACTERISTIC_UUID)
            print("Notification stopped. Disconnecting...")
            if session_file:
                session_file.close()
            

if __name__ == "__main__":
    if sys.version_info < (3, 7):
        print("This script requires Python 3.7 or higher")
        sys.exit(1)

    try:
        import bleak
    except ImportError:
        print("Bleak package not found. Install it with: pip install bleak")
        sys.exit(1)

    asyncio.run(run())

