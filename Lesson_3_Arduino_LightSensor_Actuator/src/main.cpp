#include <Arduino.h>

const int lightSensorPin = A0; // Light sensor on A0
const int ledPin = 9;          // LED on pin 9

void setup() {
    pinMode(lightSensorPin, INPUT);
    pinMode(ledPin, OUTPUT);
    Serial.begin(9600); // Start serial communication
}

void loop() {
    int lightValue = analogRead(lightSensorPin); // Read light sensor value
    Serial.print("Light value: ");
    Serial.println(lightValue); // Print the light value

    if (lightValue < 300) {
        digitalWrite(ledPin, HIGH); // Turn on LED in darkness
    } else {
        digitalWrite(ledPin, LOW);  // Turn off LED in brightness
    }

    delay(1000); // Delay 1 second
}
