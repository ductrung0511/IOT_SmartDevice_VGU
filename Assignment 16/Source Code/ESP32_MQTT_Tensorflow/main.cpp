// This code is to run on esp32 to retrieve MQTT data (prediction result) and display on the lcd

#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

const char* ssid = "Deutsch_Trung";         
const char* password = ""; 

// MQTT Broker details
const char* mqtt_broker = "broker.hivemq.com";

const int mqtt_port = 1883;
const char* mqtt_client_id = "bcf0b04a-48ca-450b-8401-9e0083414fc4";
const char* mqtt_topic = "2fdac31a-b52e-4ea4-a2f6-4e6629111b7e/fruit_ripeness_topic";

WiFiClient espClient;
PubSubClient client(espClient);



String fruit = "";
float fruit_confidence = 0;
String ripeness = "";
float ripeness_confidence = 0;

int lcdDisplay() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  display.setCursor(0, 0);
  display.println("Fruit Details:");

  display.setCursor(0, 10);
  display.print("Fruit: ");
  display.println(fruit);

  display.setCursor(0, 20);
  display.print("Confidence: ");
  display.print(fruit_confidence);
  display.println("%");

  display.setCursor(0, 30);
  display.print("Ripeness: ");
  display.println(ripeness);

  display.setCursor(0, 40);
  display.print("Ripeness Confidence: ");
  display.print(ripeness_confidence);
  display.println("%");

  display.display();
  return 1;
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived in topic: ");
  Serial.println(topic);
  Serial.print("Message:");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();

  StaticJsonDocument<1024> doc;
  DeserializationError error = deserializeJson(doc, payload, length);

  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }

  if (doc.containsKey("fruit")) {
    fruit = doc["fruit"].as<String>();
    Serial.print("Fruit: ");
    Serial.println(fruit);
  }

  if (doc.containsKey("fruit_confidence")) {
    fruit_confidence = doc["fruit_confidence"].as<float>();
    Serial.print("Fruit Confidence: ");
    Serial.println(fruit_confidence);
  }

  if (doc.containsKey("ripeness")) {
    ripeness = doc["ripeness"].as<String>();
    Serial.print("Ripeness: ");
    Serial.println(ripeness);
  }

  if (doc.containsKey("ripeness_confidence")) {
    ripeness_confidence = doc["ripeness_confidence"].as<float>();
    Serial.print("Ripeness Confidence: ");
    Serial.println(ripeness_confidence);
  }
  lcdDisplay();
}


void reconnect() {
  Serial.print("Pinging Google... ");
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient test;
    if (test.connect("google.com", 80)) {
      Serial.println("Success");
    } else {
      Serial.println("Failed (No internet?)");
    }
  }

  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(mqtt_client_id )) {
      Serial.println("connected");
      client.subscribe(mqtt_topic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(9600);
  Serial.println();
  Serial.println("Connecting to WiFi");

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  // Initialize display
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {  // 0x3C is common I2C address
    Serial.println(F("SSD1306 allocation failed"));
    while (true);
  }
  lcdDisplay();

  client.setServer(mqtt_broker, mqtt_port);
  client.setCallback(callback);
  
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}
