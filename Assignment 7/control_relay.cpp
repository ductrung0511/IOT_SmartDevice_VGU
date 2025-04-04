
#include <Arduino.h>

#define RELAY_PIN 7
void setup() {
pinMode(A0, INPUT);
pinMode(RELAY_PIN, OUTPUT);

}

void loop() {

int soil_moisture = analogRead(A0);
Serial.print("Soil Moisture: ");
Serial.println(soil_moisture);
if (soil_moisture > 450)
{
Serial.println("Soil Moisture is too low, turning relay on.");
digitalWrite(RELAY_PIN, HIGH);
}
else
{
Serial.println("Soil Moisture is ok, turning relay off.");
digitalWrite(RELAY_PIN, LOW);
}

delay(10000);

}
