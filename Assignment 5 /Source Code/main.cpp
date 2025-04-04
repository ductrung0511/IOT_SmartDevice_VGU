
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include<LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2); 
#define LED 2  // Indicating the wifi connect at the start of the program
#define DHT_PIN 7
#define DHT_TYPE DHT11

DHT dht(DHT_PIN, DHT_TYPE);

const char* SSID = "VGU_Student_Guest";
const char* PASSWORD = "";
const char* ID = "2fdac31a-b52e-4ea4-a2f6-4e6629111b7e";
const char* BROKER = "test.mosquitto.org";
String CLIENT_TELEMETRY_TOPIC = String(ID) + "/telemetry";
String CLIENT_NAME = String(ID) + "temperature_sensor_client";

const long interval = 60000 * 60; // Set delay to an hour every measurement
unsigned long publish_time = 0;

void connectWiFi() {
    Serial.println("\nConnecting to WiFi!");
    WiFi.begin(SSID, PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        Serial.print(".");
        delay(500);
    }
    digitalWrite(LED, HIGH);
    delay(2000);
    digitalWrite(LED, LOW);
    Serial.println("\nConnected to WiFi!");
}

WiFiClient espClient;
PubSubClient client(espClient);

void reconnectMQTTClient() {
    while (!client.connected()) {
        Serial.println("Connecting to MQTT ...");
        if (client.connect(CLIENT_NAME.c_str())) {
            Serial.println("MQTT Connected again!");
        } else {
            Serial.println("Retrying in 5 seconds - failed, client.state=");
            Serial.println(client.state());
            delay(5000);
        }
    }
}

void createMQTTClient() {
    client.setServer(BROKER, 1883);
    reconnectMQTTClient();
}

void setup() {
    Serial.begin(9600);
    pinMode(LED, OUTPUT);
    connectWiFi();
    dht.begin();
    lcd.begin();
    lcd.backlight();
    lcd.setCursor(0, 0);
    lcd.print("Hello, Trung!");
    createMQTTClient();
}

void loop() {
    publish_time++;
    reconnectMQTTClient();
    client.loop();

    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    if (isnan(humidity) || isnan(temperature)) {
        Serial.println("DHT not correctly working!");
        return;
    }

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Publish: " + String(publish_time));

    String displayText = "H:" + String(humidity) + "% T:" + String(temperature) + "C";
    lcd.setCursor(0, 1);
    lcd.print(displayText);

    DynamicJsonDocument doc(1024);
    doc["temperature"] = temperature;
    String telemetry;
    serializeJson(doc, telemetry);

    Serial.print("Telemetry #");
    Serial.print(publish_time);
    Serial.print(": ");
    Serial.println(telemetry);
    
    client.publish(CLIENT_TELEMETRY_TOPIC.c_str(), telemetry.c_str());
    
    delay(interval);
}
