import asyncio
from bleak import BleakClient, BleakScanner
import sys
import termios
import tty
import select

MESSAGE_SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
MESSAGE_CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
DEVICE_NAME = "ArduinoNano33"

def handle_notification(sender, data):
    message = data.decode('utf-8')
    print(f"\n[BLE] {message}")

async def find_arduino():
    print(f"Scanning for {DEVICE_NAME}...")
    device = await BleakScanner.find_device_by_name(DEVICE_NAME)
    if device is None:
        print(f"Could not find {DEVICE_NAME}")
        return None
    print(f"Found {DEVICE_NAME} at {device.address}")
    return device

# Utility to read single keypress without blocking
def is_key_pressed():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    return dr

def read_key():
    return sys.stdin.read(1) if is_key_pressed() else None

async def keypress_monitor():
    print("Press 'q' to quit.")
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())
    try:
        while True:
            key = read_key()
            if key and key.lower() == 'q':
                print("\n[q] pressed. Exiting...")
                return
            await asyncio.sleep(0.1)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

async def run():
    device = await find_arduino()
    if not device:
        return

    print(f"Connecting to {device.address}...")
    async with BleakClient(device) as client:
        print(f"Connected to {device.address}")
        await client.start_notify(MESSAGE_CHARACTERISTIC_UUID, handle_notification)
        print("Listening for BLE notifications...")

        try:
            await keypress_monitor()
        except KeyboardInterrupt:
            print("Interrupted by user.")
        finally:
            await client.stop_notify(MESSAGE_CHARACTERISTIC_UUID)
            print("Notification stopped. Disconnecting...")

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
