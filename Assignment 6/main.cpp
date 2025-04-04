#include <Arduino.h>

#define M_PIN A1      // Moisture sensor pin
#define RELAY_PIN 4   // Relay connected to D4

void setup() {
    Serial.begin(9600);
    pinMode(M_PIN, INPUT);
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, LOW);  // Start with relay OFF
}

void loop() {
    int moisture = analogRead(M_PIN); // Read moisture sensor

    // Check moisture level and control relay
    if (moisture > 450) {
        Serial.println("Soil moisture is too low, turning relay on");
        digitalWrite(RELAY_PIN, HIGH);  // Turn relay ON
    } else {
        Serial.println("Moisture level sufficient, turning relay off");
        digitalWrite(RELAY_PIN, LOW);  // Turn relay OFF
    }

    // Print moisture value to Serial Monitor
    Serial.print("Moisture Level: ");
    Serial.println(moisture);

    delay(1000);  // Wait 1 second before next reading
}




