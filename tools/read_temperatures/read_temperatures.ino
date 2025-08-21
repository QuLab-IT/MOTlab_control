// 3950 THERMISTOR EXAMPLE.
// Written by Miguel Angel Califa Urquiza
// Released under an MIT license.

// Depends on the following Arduino libraries:
// - Arduino thermistor library: https://github.com/miguel5612/Arduino-ThermistorLibrary

#include <thermistor.h>

thermistor therm1(A13, 11); // Analog Pin which is connected to the 3950 temperature sensor, and 0 represents TEMP_SENSOR_0 (see configuration.h for more information).
thermistor therm2(A14, 11); // Analog Pin which is connected to the 3950 temperature sensor, and 0 represents TEMP_SENSOR_0 (see configuration.h for more information).
thermistor therm3(A15, 11); // Analog Pin which is connected to the 3950 temperature sensor, and 0 represents TEMP_SENSOR_0 (see configuration.h for more information).

void setup()
{
  Serial.begin(9600); // Initialize serial port at 9600 Bauds.
  // Optional: Add a small delay to ensure serial is ready
  delay(100);
}

void loop()
{
  // Check if data is available to read from serial
  if (Serial.available() > 0)
  {
    // Read the incoming byte (the command character)
    char command = Serial.read();

    // Optional: Clear any remaining bytes in the buffer (like newline characters)
    while (Serial.available() > 0)
    {
      Serial.read();
    }

    // Check if the command is 'R'
    if (command == 'R')
    {
      // Read temperatures
      double temp1 = therm1.analog2temp(); // read temperature from thermistor 1
      double temp2 = therm2.analog2temp(); // read temperature from thermistor 2
      double temp3 = therm3.analog2temp(); // read temperature from thermistor 3

      // Print temperatures as comma-separated values
      Serial.print(temp1);
      Serial.print(",");
      Serial.print(temp2);
      Serial.print(",");
      Serial.println(temp3); // Use println to add a newline
    }
    // You could add else if blocks here for other commands if needed
    // else if (command == 'S') { /* do something else */ }
  }
  // No delay needed here, loop runs continuously waiting for input
}