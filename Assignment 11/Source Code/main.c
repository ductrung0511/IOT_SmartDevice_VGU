#include <Arduino.h>
#include <TinyGPSPlus.h>
#include <HardwareSerial.h>

// Use pins 12 (RX) and 13 (TX) for GPS
HardwareSerial GPSSerial(1);  // Use Serial1 on ESP32 (change if using different board)
TinyGPSPlus gps;

void setup() {
  Serial.begin(9600);
  GPSSerial.begin(9600, SERIAL_8N1, 12, 13); // RX = 12, TX = 13
  Serial.println("GPS Module Test Started...");
}

void GPS() {
  static unsigned long lastRun = 0;

  // Only run every 5000 milliseconds (5 seconds)
  if (millis() - lastRun < 5000) return;
  lastRun = millis();

  // Feed data into GPS parser
  while (GPSSerial.available() > 0) {
    gps.encode(GPSSerial.read());
  }

  if (gps.location.isValid()) {
    Serial.print(F("- latitude: "));
    Serial.println(gps.location.lat(), 6);

    Serial.print(F("- longitude: "));
    Serial.println(gps.location.lng(), 6);

    Serial.print(F("- altitude: "));
    if (gps.altitude.isValid())
      Serial.println(gps.altitude.meters());
    else
      Serial.println(F("INVALID"));
  } else {
    Serial.println(F("- location: INVALID"));
  }

  Serial.print(F("- speed: "));
  if (gps.speed.isValid()) {
    Serial.print(gps.speed.kmph());
    Serial.println(F(" km/h"));
  } else {
    Serial.println(F("INVALID"));
  }

  Serial.print(F("- GPS date&time: "));
  if (gps.date.isValid() && gps.time.isValid()) {
    Serial.print(gps.date.year());
    Serial.print(F("-"));
    Serial.print(gps.date.month());
    Serial.print(F("-"));
    Serial.print(gps.date.day());
    Serial.print(F(" "));
    Serial.print(gps.time.hour());
    Serial.print(F(":"));
    Serial.print(gps.time.minute());
    Serial.print(F(":"));
    Serial.println(gps.time.second());
  } else {
    Serial.println(F("INVALID"));
  }

  Serial.println();
}

void loop() {
  GPS(); // Call the GPS function regularly
}
