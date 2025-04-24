import asyncio
from bleak import BleakClient, BleakScanner
import sys
# BLE service and characteristic UUIDs - must match Arduino
MESSAGE_SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
MESSAGE_CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
# Arduino device name - must match what you set in the Arduino sketch
DEVICE_NAME = "ArduinoNano33"
async def find_arduino():
    print(f"Scanning for {DEVICE_NAME}...")
    # Scan for devices
    device = await BleakScanner.find_device_by_name(DEVICE_NAME)
    if device is None:
        print(f"Could not find {DEVICE_NAME}")
        return None
    print(f"Found {DEVICE_NAME} at {device.address}")
    return device
async def run():
    # Find the Arduino
    device = await find_arduino()
    if not device:
        return
    # Connect to the Arduino
    print(f"Connecting to {device.address}...")
    async with BleakClient(device) as client:
        print(f"Connected to {device.address}")
        # Main messaging loop
        try:
            while True:
                # Get user input
                message = input("Enter message to send (or 'exit' to quit): ")
                if message.lower() == 'exit':
                    break
                # Convert string to bytes and send to Arduino
                await client.write_gatt_char(
                    MESSAGE_CHARACTERISTIC_UUID,
                    message.encode()
                )
                print(f"Sent: {message}")
                # Small delay to prevent flooding
                await asyncio.sleep(0.5)
        except KeyboardInterrupt:
            print("Interrupted by user")
        print("Disconnecting...")
if __name__ == "__main__":
    # Check Python version (Bleak needs Python 3.7+)
    if sys.version_info < (3, 7):
        print("This script requires Python 3.7 or higher")
        sys.exit(1)
    # Install required packages if not present
    try:
        import bleak
    except ImportError:
        print("Bleak package not found. Install it with: pip install bleak")
        sys.exit(1)
    # Run the main async function
    asyncio.run(run())







