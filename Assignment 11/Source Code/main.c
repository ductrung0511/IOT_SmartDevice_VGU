#include <TinyGPSPlus.h>
#include <HardwareSerial.h>
#include <Arduino.h>

// For ESP32: use UART2 (pins RX=16, TX=17 as an example)
HardwareSerial GPSSerial(2);
TinyGPSPlus gps;

void setup() {
  Serial.begin(115200);
  GPSSerial.begin(9600, SERIAL_8N1, 16, 17); // RX, TX
  Serial.println(F("GPS Data Logger Initialized"));
}

void loop() {
  // Feed GPS data to the parser
  while (GPSSerial.available() > 0) {
    gps.encode(GPSSerial.read());
  }

  static unsigned long lastDisplay = 0;
  if (millis() - lastDisplay > 5000) { // Display every 5 seconds
    lastDisplay = millis();

    Serial.println(F("===== GPS DATA ====="));

    // Location
    if (gps.location.isValid()) {
      Serial.print(F("Latitude: "));
      Serial.println(gps.location.lat(), 6);
      Serial.print(F("Longitude: "));
      Serial.println(gps.location.lng(), 6);
    } else {
      Serial.println(F("Location: INVALID"));
    }

    // Altitude
    if (gps.altitude.isValid()) {
      Serial.print(F("Altitude: "));
      Serial.print(gps.altitude.meters());
      Serial.println(F(" m"));
    } else {
      Serial.println(F("Altitude: INVALID"));
    }

    // Speed
    if (gps.speed.isValid()) {
      Serial.print(F("Speed: "));
      Serial.print(gps.speed.kmph());
      Serial.println(F(" km/h"));
    } else {
      Serial.println(F("Speed: INVALID"));
    }

    // Course (direction)
    if (gps.course.isValid()) {
      Serial.print(F("Course: "));
      Serial.print(gps.course.deg());
      Serial.println(F("°"));
    } else {
      Serial.println(F("Course: INVALID"));
    }

    // Date and Time
    if (gps.date.isValid() && gps.time.isValid()) {
      Serial.print(F("Date: "));
      Serial.print(gps.date.day());
      Serial.print(F("/"));
      Serial.print(gps.date.month());
      Serial.print(F("/"));
      Serial.println(gps.date.year());

      Serial.print(F("Time (UTC): "));
      Serial.print(gps.time.hour());
      Serial.print(F(":"));
      Serial.print(gps.time.minute());
      Serial.print(F(":"));
      Serial.println(gps.time.second());
    } else {
      Serial.println(F("Date/Time: INVALID"));
    }

    // Satellites
    if (gps.satellites.isValid()) {
      Serial.print(F("Satellites: "));
      Serial.println(gps.satellites.value());
    } else {
      Serial.println(F("Satellites: INVALID"));
    }

    // HDOP (precision)
    if (gps.hdop.isValid()) {
      Serial.print(F("HDOP: "));
      Serial.println(gps.hdop.value());
    } else {
      Serial.println(F("HDOP: INVALID"));
    }

    Serial.println(F("=====================\n"));
  }
}
