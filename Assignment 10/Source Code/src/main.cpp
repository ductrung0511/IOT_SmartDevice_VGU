#include <WiFi.h>
#include <mqtt_client.h>
#include <azure/az_iot.h>
#include <azure/az_core.h>
#include "DHT.h"

#define DHT_PIN 4
#define RELAY_PIN 2 // Adjust the pin
unsigned long sas_token_expiry_time = 0;  // You need to store the expiry time of the SAS token
const unsigned long sas_token_valid_duration = 3600; // 1 hour validity for SAS token (60 minutes * 60 seconds)
String sas_token;
esp_mqtt_client_config_t mqtt_config = {};

DHT dht(DHT_PIN, DHT11);

const char* ssid = "your_wifi_ssid";
const char* password = "your_wifi_password";
const char* host = "soil-sensor-Deuna.azure-devices.net";
const char* device_id = "soil-moisture-sensor";
const char* device_key = "xoXd0VgAbPaIHjd4ZcdZG674oL1HvcN8/85LUKEQehg=";  // Use SAS token or X.509 certs
// hubname: soil-sensor-Deuna
#define MQTT_PORT 8883

// Sensor data variables
float humidity = 0.0f;
float temperature = 0.0f;
uint16_t potentiometer = 0;
uint16_t flame = 0;

esp_mqtt_client_handle_t mqtt_client;
az_iot_hub_client client;
char telemetry_topic[128] = "devices/soil-moisture-sensor/messages/events/";
char ClientID[128];
String telemetry_payload = "";

// Utility function to connect to WiFi
void connectToWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
}

#include <mbedtls/base64.h>
#include <mbedtls/md.h>

#define SAS_TOKEN_DURATION_IN_MINUTES 60
String generateSasToken(const char* device_key, const char* host, const char* device_id) {
  // Calculate expiry time (SAS token validity in seconds from now)
  unsigned long expiry_time = time(NULL) + (SAS_TOKEN_DURATION_IN_MINUTES * 60);  // Expiry in seconds

  // Prepare the signature string
  String signature = host + String("/devices/") + String(device_id);
  String signature_with_expiry = signature + "\n" + String(expiry_time);

  // Base64 encode the device key (decoded to raw binary)
  uint8_t decoded_key[64];
  size_t decoded_key_len = 0;
  mbedtls_base64_decode(decoded_key, sizeof(decoded_key), &decoded_key_len, (const uint8_t*)device_key, strlen(device_key));

  // HMAC-SHA256 signature generation
  uint8_t hmac_result[32];
  mbedtls_md_context_t ctx;
  const mbedtls_md_info_t* md_info = mbedtls_md_info_from_type(MBEDTLS_MD_SHA256);
  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, md_info, 1);
  mbedtls_md_hmac_starts(&ctx, decoded_key, decoded_key_len);
  mbedtls_md_hmac_update(&ctx, (const uint8_t*)signature_with_expiry.c_str(), signature_with_expiry.length());
  mbedtls_md_hmac_finish(&ctx, hmac_result);
  mbedtls_md_free(&ctx);

  // Base64 encode the HMAC result
  char base64_signature[128];
  size_t base64_sig_len;
  mbedtls_base64_encode((uint8_t*)base64_signature, sizeof(base64_signature), &base64_sig_len, hmac_result, sizeof(hmac_result));
  base64_signature[base64_sig_len] = '\0';

  // Format the final SAS token
  String sas_token = "SharedAccessSignature sr=" + signature + "&sig=" + String(base64_signature) + "&se=" + String(expiry_time);
  
  return sas_token;
}


static void mqtt_event_handler(void* handler_args, esp_event_base_t base, int32_t event_id, void* event_data) {
  esp_mqtt_event_handle_t event = (esp_mqtt_event_handle_t)event_data; // cast from void* to "esp_mqtt_event_handle_t type".
  String payload = "";  // Initialize payload variable
  String ack_message = "";  // Initialize ack_message variable
  switch (event->event_id) { // access the event_id field of the esp_mqtt_event_handle_t structure.
    case MQTT_EVENT_CONNECTED:
      Serial.println("Connected to MQTT Broker");
      break;
    case MQTT_EVENT_DISCONNECTED:
      Serial.println("Disconnected from MQTT Broker");
      reconnectMqttClient();
      break;
    case MQTT_EVENT_DATA:
      // Process incoming command
      payload = String((char*)event->data, event->data_len);
      Serial.println("Received command: " + payload);

      // Turn relay on or off based on the command received
      if (payload == "turn_on") {
        digitalWrite(RELAY_PIN, HIGH);  // Turn the relay on
        Serial.println("Relay turned ON");
      } else if (payload == "turn_off") {
        digitalWrite(RELAY_PIN, LOW);  // Turn the relay off
        Serial.println("Relay turned OFF");
      }

      ack_message = "{\"status\": \"success\", \"command\": \"" + payload + "\"}";
      esp_mqtt_client_publish(mqtt_client, "$iothub/twin/PATCH/properties/reported", ack_message.c_str(), 0, 1, 0);
      break;
    default:
      break;
  }
}

// Initialize MQTT client and Azure IoT client
void initializeIoTHubClient() {
  az_iot_hub_client_options options = az_iot_hub_client_options_default();
  options.user_agent = AZ_SPAN_FROM_STR("ESP32 IoT SDK");

  az_result rc = az_iot_hub_client_init(&client, az_span_create((uint8_t*)host, strlen(host)), az_span_create((uint8_t*)device_id, strlen(device_id)), &options);
  if (az_result_failed(rc)) {
    Serial.println("Failed initializing IoT Hub client");
    return;
  }

  size_t client_id_length;
  rc = az_iot_hub_client_get_client_id(&client, ClientID, sizeof(ClientID) - 1, &client_id_length);
  if (az_result_failed(rc)) {
    Serial.println("Failed getting client ID");
    return;
  }
  
  Serial.print("Client ID: ");
  Serial.println(ClientID);
}

// Function to generate SAS token with expiration
String generateSasTokenWithExpiry(const char* device_key, const char* host, const char* device_id) {
  // SAS token expiration time is typically 1 hour (3600 seconds)
  unsigned long current_time = millis() / 1000;  // Get the current time in seconds

  // If the token has expired or is about to expire in less than 60 seconds, regenerate it
  if (current_time >= sas_token_expiry_time - 60) {
    Serial.println("Regenerating SAS token...");
    String new_token = generateSasToken(device_key, host, device_id);
    sas_token_expiry_time = current_time + sas_token_valid_duration;  // Set new expiry time
    return new_token;
  } else {
    return sas_token; // Return empty if the token is still valid
  }
}

void reconnectMqttClient() {
  // Try to reconnect to the MQTT broker after disconnection
  Serial.println("Attempting to reconnect to MQTT broker...");
  unsigned long current_time = millis() / 1000;  // Get the current time in seconds

  // If the token has expired or is about to expire in less than 60 seconds, regenerate it
  if (current_time >= sas_token_expiry_time - 60) {
    Serial.println("SAS token expired. Regenerating SAS token...");
    sas_token = generateSasToken(device_key, host, device_id);
    sas_token_expiry_time = current_time + sas_token_valid_duration;
  }
  
  if (sas_token.length() == 0) {
    Serial.println("Failed to generate SAS token");
    return;  // Early exit if SAS token generation fails
  }
  esp_mqtt_client_stop(mqtt_client); 
  mqtt_config.password = sas_token.c_str();  // Use this token for MQTT password

  mqtt_client = esp_mqtt_client_init(&mqtt_config);
  if (mqtt_client == NULL) {
    Serial.println("Failed to initialize MQTT client");
    return;  // Early exit if MQTT client initialization fails
  }

  esp_mqtt_client_register_event(mqtt_client, MQTT_EVENT_ANY, mqtt_event_handler, NULL);

  esp_err_t err = esp_mqtt_client_start(mqtt_client);
  if (err != ESP_OK) {
    Serial.println("Failed to start MQTT client");
    return;  // Early exit if starting the MQTT client fails
  }

  Serial.println("MQTT Client re_initialized and re_connected to Azure IoT Hub");
}
// Initialize MQTT connection to Azure IoT Hub
void initializeMqttClient() {
  mqtt_config.uri = "mqtts://soil-sensor-Deuna.azure-devices.net";
  mqtt_config.port = MQTT_PORT;
  mqtt_config.client_id = ClientID;

  char username_buffer[256]; 
  size_t username_length;
  az_result rc = az_iot_hub_client_get_user_name(&client, username_buffer, sizeof(username_buffer), &username_length);
  if (az_result_failed(rc)) {
    Serial.println("Failed to get username for MQTT");
    return;  // Early exit if username retrieval fails
  }
  mqtt_config.username = username_buffer;  // Ensure the format is correct

  // SAS Token handling
  sas_token = generateSasToken(device_key, host, device_id); 
  if (sas_token.length() == 0) {
    Serial.println("Failed to generate SAS token");
    return;  // Early exit if SAS token generation fails
  }
  mqtt_config.password = sas_token.c_str();  // Use this token for MQTT password

  mqtt_client = esp_mqtt_client_init(&mqtt_config);
  if (mqtt_client == NULL) {
    Serial.println("Failed to initialize MQTT client");
    return;  // Early exit if MQTT client initialization fails
  }

  esp_mqtt_client_register_event(mqtt_client, MQTT_EVENT_ANY, mqtt_event_handler, NULL);

  esp_err_t err = esp_mqtt_client_start(mqtt_client);
  if (err != ESP_OK) {
    Serial.println("Failed to start MQTT client");
    return;  // Early exit if starting the MQTT client fails
  }

  Serial.println("MQTT Client initialized and connected to Azure IoT Hub");
}

// Generate telemetry payload from sensor data
void generateTelemetryPayload() {
  
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }

  telemetry_payload = "{ \"Temperature\": " + String(temperature) + ", \"Humidity\": " + String(humidity) ;
}

// Send telemetry to Azure IoT Hub
void sendTelemetry() {
  generateTelemetryPayload();

  // Publish to Azure IoT Hub telemetry topic
  int msg_id = esp_mqtt_client_publish(mqtt_client, telemetry_topic, telemetry_payload.c_str(), telemetry_payload.length(), 1, 0);
  if (msg_id == -1) {
    Serial.println("Failed to send message");
  } else {
    Serial.println("Telemetry sent!");
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT); 
  connectToWiFi();
  dht.begin();
  initializeIoTHubClient();
  initializeMqttClient();
}

void loop() {
  // Update sensor readings and send telemetry every 5 seconds
  if (WiFi.status() == WL_CONNECTED) {
    sendTelemetry();
    delay(5000); // Send every 5 seconds
  } else {
    connectToWiFi();
  }
}
