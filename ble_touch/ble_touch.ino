#include <ArduinoBLE.h>
#include <Arduino_APDS9960.h>
#include <CapacitiveSensor.h>

CapacitiveSensor touchSensor = CapacitiveSensor(4, 2);

long baseline = 0;
float thresholdFactor = 0.92;
float releaseFactor = 0.96;
bool touchActive = false;

#define OSC_WINDOW_SIZE 5
bool touchHistory[OSC_WINDOW_SIZE] = {false};
int historyIndex = 0;
int oscillationCount = 0;
int maxOscillation = 3;

unsigned long lastCalibrationTime = 0;
const unsigned long CALIBRATION_INTERVAL = 15000;

const int ledPin = 13;

BLEService messageService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLEStringCharacteristic messageCharacteristic(
  "19B10001-E8F2-537E-4F6C-D104768A1214",
  BLERead | BLEWrite | BLENotify, 512
);

void setup() {
  pinMode(ledPin, OUTPUT);
  Serial.begin(9600);
  unsigned long startTime = millis();
  while (!Serial && millis() - startTime < 3000);

  if (!BLE.begin()) {
    if (Serial) Serial.println("BLE failed!");
    while (1);
  }

  BLE.setLocalName("ArduinoNano33");
  BLE.setAdvertisedService(messageService);
  messageService.addCharacteristic(messageCharacteristic);
  BLE.addService(messageService);
  messageCharacteristic.writeValue("BLE ready");
  BLE.advertise();

  delay(2000);
  baseline = getAverageReading(300);
  if (Serial) {
    Serial.print("Initial Baseline: ");
    Serial.println(baseline);
  }
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    if (Serial) {
      Serial.print("Connected to: ");
      Serial.println(central.address());
    }

    while (central.connected()) {
      long currentValue = getAverageReading(10);
      bool isTouchedNow;

      if (!touchActive) {
        isTouchedNow = currentValue < (baseline * thresholdFactor);
      } else {
        isTouchedNow = currentValue < (baseline * releaseFactor);
      }

      touchHistory[historyIndex] = isTouchedNow;
      historyIndex = (historyIndex + 1) % OSC_WINDOW_SIZE;

      oscillationCount = 0;
      for (int i = 1; i < OSC_WINDOW_SIZE; i++) {
        if (touchHistory[i] != touchHistory[i - 1]) {
          oscillationCount++;
        }
      }

      bool finalTouchState = isTouchedNow;
      if (oscillationCount >= maxOscillation) {
        finalTouchState = true;
      }

      if (finalTouchState != touchActive) {
        touchActive = finalTouchState;
        digitalWrite(ledPin, touchActive ? HIGH : LOW);
      }

      // Send raw value continuously for plotting
      messageCharacteristic.writeValue(String(currentValue));

      if (millis() - lastCalibrationTime > CALIBRATION_INTERVAL && !touchActive) {
        baseline = getAverageReading(100);
        lastCalibrationTime = millis();
        if (Serial) {
          Serial.print("Recalibrated Baseline: ");
          Serial.println(baseline);
        }
      }

      delay(30); // Faster updates for smoother graphing
    }

    if (Serial) {
      Serial.print("Disconnected from: ");
      Serial.println(central.address());
    }
  }
}

long getAverageReading(int samples) {
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += touchSensor.capacitiveSensor(30);
    delay(1);
  }
  return sum / samples;
}
