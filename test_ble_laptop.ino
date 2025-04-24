#include <ArduinoBLE.h>
#include <Arduino_APDS9960.h>
// Define a BLE service and characteristic
BLEService messageService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLEStringCharacteristic messageCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLEWrite | BLENotify, 512);
void setup() {
  Serial.begin(9600);
  while (!Serial); // Wait for serial port to connect
  // Initialize BLE
  if (!BLE.begin()) {
    Serial.println("Starting BLE failed!");
    while (1);
  }
  // Set up the BLE device
  BLE.setLocalName("ArduinoNano33");
  BLE.setAdvertisedService(messageService);
  // Add the characteristic to the service
  messageService.addCharacteristic(messageCharacteristic);
  // Add the service
  BLE.addService(messageService);
  // Initial value
  messageCharacteristic.writeValue("Ready to receive messages");
  // Start advertising
  BLE.advertise();
  Serial.println("Bluetooth device active, waiting for connections...");
}
void loop() {
  // Listen for BLE peripherals to connect
  BLEDevice central = BLE.central();
  // If a central is connected to peripheral
  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());
    // While the central is still connected to peripheral
    while (central.connected()) {
      // If the characteristic value was updated by the central
      if (messageCharacteristic.written()) {
        // Get the new value
        String message = messageCharacteristic.value();
        // Print the new value to the Serial Monitor
        Serial.print("Received message: ");
        Serial.println(message);
      }
    }
    // When the central disconnects
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }
}











