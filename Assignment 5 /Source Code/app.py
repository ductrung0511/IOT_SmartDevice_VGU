
from os import path
import json
import csv
from datetime import datetime
import paho.mqtt.client as mqtt

id = "2fdac31a-b52e-4ea4-a2f6-4e6629111b7e"

client_telemetry_topic = id + "/telemetry"
client_name = id + 'temperature_sensor_server'
temperature_file_name = 'temperature.csv'
fieldnames = ['date', 'temperature']

if not path.exists(temperature_file_name):
    with open(temperature_file_name, mode="w") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames= fieldnames)
        writer.writeheader()

# Callback function when a message is received
def handle_telemetry(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
        print("Message received: ", payload, " | ")
    except json.JSONDecodeError:
        print("Error decoding JSON:", message.payload.decode())
    with open(temperature_file_name, mode='a') as temperature_file:        
        temperature_writer = csv.DictWriter(temperature_file, fieldnames=fieldnames)
        temperature_writer.writerow({'date' : datetime.now().astimezone().replace(microsecond=0).isoformat(), 'temperature' : payload['temperature']})

# Callback function when connected to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(client_telemetry_topic)
    else:
        print(f"Failed to connect, return code {rc}")

# Setup MQTT client
mqtt_client = mqtt.Client(client_name)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = handle_telemetry

# Connect to the MQTT broker
try:
    mqtt_client.connect("test.mosquitto.org", 1883, 60)
except Exception as e:
    print("Failed to connect to broker:", e)
    exit(1)
    

# Keep the connection alive and process messages
mqtt_client.loop_forever()

