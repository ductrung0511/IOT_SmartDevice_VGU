import json
import time
import paho.mqtt.client as mqtt
import threading

id = "2fdac31a-b52e-4ea4-a2f6-4e6629111b7e"

client_telemetry_topic = id + "/telemetry"
server_command_topic = id + "/command"
client_name = id + "soilmoisturesensor_client"
water_time = 5
wait_time = 20

def send_relay_command(client, state):
    command = { 'relay_on' : state }
    print("Sending message:", command)
    client.publish(server_command_topic, json.dumps(command))

def control_relay(client):
    print("Unsubscribing from telemetry")
    mqtt_client.unsubscribe(client_telemetry_topic)

    send_relay_command(client, True)
    time.sleep(water_time)
    send_relay_command(client, False)

    time.sleep(wait_time)

    print("Subscribing to telemetry")
    mqtt_client.subscribe(client_telemetry_topic)

# Callback function when a message is received
def handle_telemetry(client, userdata, message):
    payload = json.loads(message.payload.decode())
    print("Message received:", payload)

    if payload['soil_moisture'] > 450:
        threading.Thread(target=control_relay, args=(client,)).start()
        
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



