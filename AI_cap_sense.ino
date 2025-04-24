#include <CapacitiveSensor.h>

// 10M resistor between pins 4 & 2, pushrim connected to pin 2

CapacitiveSensor touchSensor = CapacitiveSensor(4, 2);

long baseline = 0;

long threshold = 50; // Adjust based user observation and testing

unsigned long lastCalibrationTime = 0;



const unsigned long CALIBRATION_INTERVAL = 10000; // 15 seconds

void setup() {


pinMode(13, OUTPUT); // Set pin 13 as an output

pinMode(8, OUTPUT); // Set pin 13 as an output

Serial.begin(9600);

delay(2000);
Serial.print("hello");

// Initial calibration

baseline = getAverageReading(300);



//Don't print text labels during setup for Serial Plotter

//Just print the value once t initialize the plot

Serial.print(baseline);

Serial.print(" ");

Serial.print(threshold);

Serial.print(" ");

Serial.println(0);
Serial.print("hello2");

}

void loop() {

// Read the current value

long currentValue = touchSensor.capacitiveSensor(40);
// digitalWrite(8, HIGH);

// delay(40);

// digitalWrite(8, LOW);

// For Serial Plotter, just print the values without text labels

// Each value should be on the same line separated by spaces, with a newline at the end

Serial.print(currentValue);

Serial.print(" threshold: ");

Serial.print(threshold);

Serial.print("baseline: ");

Serial.print(baseline);

Serial.print(" ");

Serial.println(threshold -baseline);

// Check for touch (we don't print text here to keep Serial Plotter working)

if (currentValue < threshold) {

  digitalWrite(8, HIGH);

 
 
  // Touch detected - if you need to take action, do it here

  // Don't print text messages while using Serial Plotter

  }

else{ 
  digitalWrite(8, LOW); 
  Serial.println("touch sensed");

} 


// Periodic baseline recalibration (when not touched)

// if (currentValue < baseline) {

//   if (currentValue < (baseline + threshold / 2)) {

//   // Only recalibrate if not currently being touched

//   baseline = (baseline * 0.5) + (getAverageReading(100) * 0.5);

//   lastCalibrationTime = millis();

//   }

// }

// if (millis() - lastCalibrationTime > CALIBRATION_INTERVAL) {

//   if (currentValue < (baseline + threshold / 2)) {

//   // Only recalibrate if not currently being touched

//   baseline = (baseline * 0.5) + (getAverageReading(100) * 0.5);

//   lastCalibrationTime = millis();

//   }

// }




delay(40);

}

long getAverageReading(int samples) {
  digitalWrite(8, LOW); delay(10);


  long sum = 0;
  long new_base = 0;

  for (int i = 0; i < samples; i++) {

    sum += touchSensor.capacitiveSensor(40);

    if (new_base < touchSensor.capacitiveSensor(40)){
      new_base =  touchSensor.capacitiveSensor(40);
    }
    

    delay(5);

  } 

  return sum / samples;

}