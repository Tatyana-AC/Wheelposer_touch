import asyncio
from bleak import BleakClient, BleakScanner
import sys
import termios
import tty
import select
from datetime import datetime
import csv
import os
import matplotlib.pyplot as plt

MESSAGE_SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
MESSAGE_CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
DEVICE_NAME = "ArduinoNano33"

recording = False
session_started = False
session_file = None
csv_writer = None
recorded_data = []
session_name = ""
client = None  # Will be initialized in run()

# Notification handler
def handle_notification(sender, data):
    global recording, session_started, csv_writer, recorded_data
    message = data.decode('utf-8').strip()
    if session_started:
        print(f"[BLE] {message}")
    if recording and csv_writer:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        csv_writer.writerow([timestamp, message])
        value = float(message)
        threshold = sum(v for _, v in recorded_data) / len(recorded_data) * 0.92 if recorded_data else 0
        touch = 1 if value < threshold else 0
        csv_writer.writerow([timestamp, value, touch])
        recorded_data.append((timestamp, value))

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

def plot_session_data(name):
    from matplotlib.dates import DateFormatter
    global recorded_data
    if not recorded_data:
        print("No data to plot.")
        return
    timestamps, values, touches = zip(*[(ts, val, 1 if val < (sum(v for _, v in recorded_data) / len(recorded_data) * 0.92 if recorded_data else 0) else 0) for ts, val in recorded_data])
    time_axis = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f") for ts in timestamps]

    plt.figure(figsize=(10, 4))
    plt.plot(time_axis, values, label='Sensor Value')
    touch_times = [t for t, touch in zip(time_axis, touches) if touch]
    touch_vals = [v for v, touch in zip(values, touches) if touch]
    plt.scatter(touch_times, touch_vals, color='red', s=15, label='Touch Points')
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.title(f"Session: {name} (Analog)")
    plt.legend()
    plt.gca().xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
    plt.tight_layout()
    analog_filename = f"session_{name}.png"
    plt.savefig(analog_filename)
    plt.close()
    print(f"Analog plot saved as: {analog_filename}")

    threshold = sum(values) / len(values) * 0.92
    digital_values = [1 if v < threshold else 0 for v in values]
    plt.figure(figsize=(10, 2))
    plt.step(time_axis, digital_values, where='post', label='Touch State')
    plt.ylim(-0.2, 1.2)
    plt.xlabel("Time")
    plt.ylabel("Touch")
    plt.title(f"Session: {name} (Touch/No-Touch)")
    plt.tight_layout()
    digital_filename = f"session_{name}_touch.png"
    plt.savefig(digital_filename)
    plt.show()
    plt.close()
    print(f"Touch-state plot saved as: {digital_filename}")

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
                        filename = f"session_{session_name}.csv"
                        session_file = open(filename, mode='w', newline='')
                        csv_writer = csv.writer(session_file)
                        csv_writer.writerow(["Timestamp", "Value", "Touch"])
                        recorded_data = []
                        recording = True
                        session_started = True
                        print(f"Recording started: {filename}")
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
                        if session_file:
                            session_file.close()
                        if recording:
                            plot_session_data(session_name)
                        os._exit(0)
                    elif char == 'e':
                        print("\nEnding session...")
                        if recording:
                            recording = False
                            session_started = False
                            if client:
                                await client.write_gatt_char(MESSAGE_CHARACTERISTIC_UUID, b"session_off")
                            if session_file:
                                session_file.close()
                                session_file = None
                                csv_writer = None
                            plot_session_data(session_name)
                            print("Recording stopped.")
                        user_input = input("Start a new session? (y/n): ").strip().lower()
                        if user_input == 'y':
                            print("Type 'start' then your session name to begin.")
                        else:
                            print("No active recording.")

            await asyncio.sleep(0.1)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

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
            if recording:
                plot_session_data(session_name)

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
