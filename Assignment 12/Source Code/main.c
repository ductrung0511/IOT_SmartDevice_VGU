#include <TinyGPSPlus.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <HardwareSerial.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://<soi-sensor-Deuna>.azurewebsites.net/api/upload_blob_from_esp32" 

TinyGPSPlus gps;
HardwareSerial GPSSerial(2); // Use UART2 for GPS

void setup() {
  Serial.begin(115200);
  GPSSerial.begin(9600, SERIAL_8N1, 16, 17); // RX, TX

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

void loop() {
  while (GPSSerial.available()) {
    gps.encode(GPSSerial.read());
  }

  static unsigned long lastSend = 0;
  if (millis() - lastSend > 5000) {
    lastSend = millis();

    if (gps.location.isValid()) {
      String json = "{";
      json += "\"latitude\":" + String(gps.location.lat(), 6) + ",";
      json += "\"longitude\":" + String(gps.location.lng(), 6) + ",";
      json += "\"altitude\":" + String(gps.altitude.isValid() ? gps.altitude.meters() : 0) + ",";
      json += "\"speed\":" + String(gps.speed.isValid() ? gps.speed.kmph() : 0) + ",";
      json += "\"course\":" + String(gps.course.isValid() ? gps.course.deg() : 0) + ",";
      json += "\"satellites\":" + String(gps.satellites.isValid() ? gps.satellites.value() : 0) + ",";
      json += "\"hdop\":" + String(gps.hdop.isValid() ? gps.hdop.value() : 0) + ",";
      json += "\"timestamp\":\"" + String(gps.date.year()) + "-" + String(gps.date.month()) + "-" + String(gps.date.day()) + "T" +
              String(gps.time.hour()) + ":" + String(gps.time.minute()) + ":" + String(gps.time.second()) + "Z\"";
      json += "}";

      Serial.println("Sending to Azure:");
      Serial.println(json);

      HTTPClient http;
      http.begin(serverUrl);
      http.addHeader("Content-Type", "application/json");

      int httpResponseCode = http.POST(json);
      if (httpResponseCode > 0) {
        Serial.printf("HTTP Response code: %d\n", httpResponseCode);
      } else {
        Serial.printf("Error sending request: %s\n", http.errorToString(httpResponseCode).c_str());
      }

      http.end();
    } else {
      Serial.println("No valid GPS data yet...");
    }
  }
}
