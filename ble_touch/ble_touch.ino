#include <ArduinoBLE.h>
#include <Arduino_APDS9960.h>
#include <CapacitiveSensor.h>

// Capacitive sensor setup
CapacitiveSensor touchSensor = CapacitiveSensor(4, 2);
long baseline = 0;
long threshold = 50; // Adjust this value based on testing
unsigned long lastCalibrationTime = 0;
const unsigned long CALIBRATION_INTERVAL = 10000;

// Pin definitions
const int ledPin = 8;

// BLE setup
BLEService messageService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLEStringCharacteristic messageCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLEWrite | BLENotify, 512);

void setup() {
  pinMode(ledPin, OUTPUT);

  Serial.begin(9600);
  unsigned long startTime = millis();
  while (!Serial && millis() - startTime < 5000); // Optional serial wait

  // Initialize BLE
  if (!BLE.begin()) {
    if (Serial) Serial.println("Starting BLE failed!");
    while (1);
  }

  BLE.setLocalName("ArduinoNano33");
  BLE.setAdvertisedService(messageService);
  messageService.addCharacteristic(messageCharacteristic);
  BLE.addService(messageService);
  messageCharacteristic.writeValue("BLE ready");

  BLE.advertise();
  if (Serial) Serial.println("Bluetooth device active, waiting for connections...");

  delay(2000); // Stabilize sensor
  baseline = getAverageReading(300);
  if (Serial) {
    Serial.print("Baseline: ");
    Serial.println(baseline);
  }
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    if (Serial) {
      Serial.print("Connected to central: ");
      Serial.println(central.address());
    }

    while (central.connected()) {
      long currentValue = touchSensor.capacitiveSensor(40);

      // Touch detection logic
      if (currentValue < threshold) {
        digitalWrite(ledPin, HIGH);
        messageCharacteristic.writeValue("Touch detected");
      } else {
        digitalWrite(ledPin, LOW);
        messageCharacteristic.writeValue("No touch");
      }

      delay(100); // Throttle BLE updates to reduce spam
    }

    if (Serial) {
      Serial.print("Disconnected from central: ");
      Serial.println(central.address());
    }
  }
}

long getAverageReading(int samples) {
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += touchSensor.capacitiveSensor(40);
    delay(5);
  }
  return sum / samples;
}
