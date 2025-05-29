from tensorflow.keras.models import load_model
import numpy as np
import cv2
import base64
import json
import paho.mqtt.client as mqtt
from datetime import datetime

id = "2fdac31a-b52e-4ea4-a2f6-4e6629111b7e"
image_topic = "2fdac31a-b52e-4ea4-a2f6-4e6629111b7e/image_topic"
telemetry_topic = id + "/fruit_ripeness_topic"
client_name = id + "_fruit_ripeness_client"

# Load models
fruit_model = load_model("fruit_keras_model.h5", compile=False)
apple_ripeness_model = load_model("apple_ripeness_keras_model.h5", compile=False)
tomato_ripeness_model = load_model("tomato_ripeness_keras_model.h5", compile=False)

# Load labels
fruit_names = open("fruit_labels.txt", "r").readlines()
apple_ripeness_names = open("apple_ripeness_labels.txt", "r").readlines()
tomato_ripeness_names = open("tomato_ripeness_labels.txt", "r").readlines()

# MQTT callback
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        client.subscribe(image_topic)
    else:
        print(f"❌ MQTT connection failed with code {rc}")

def on_message(client, userdata, msg):
    print(f"\n📩 Received message on topic: {msg.topic}")
    try:
        # Decode base64
        img_data = base64.b64decode(msg.payload)
        with open("received.jpg", "wb") as f:
            f.write(img_data)

        print("🖼️ Image saved as received.jpg")

        # Process the image
        image = cv2.imread("received.jpg")
        if image is None:
            print("❌ Failed to load received image")
            return

        image_resized = cv2.resize(image, (224, 224), interpolation=cv2.INTER_AREA)
        image_array = np.asarray(image_resized, dtype=np.float32).reshape(1, 224, 224, 3)
        image_array = (image_array / 127.5) - 1

        # Fruit classification
        prediction = fruit_model.predict(image_array)
        index = np.argmax(prediction)
        fruit = fruit_names[index][2:].strip()
        confidence_score = float(prediction[0][index])

        telemetry = {
            "fruit": fruit,
            "fruit_confidence": f"{confidence_score:.4f}"
        }

        print(f"🍎 Fruit: {fruit}, Confidence: {confidence_score * 100:.2f}%")

        # Ripeness prediction
        fruit_lower = fruit.lower()
        if fruit_lower == "apple":
            pred = apple_ripeness_model.predict(image_array)
            idx = np.argmax(pred)
            ripeness = apple_ripeness_names[idx][2:].strip()
            conf = float(pred[0][idx])
        elif fruit_lower == "tomato":
            pred = tomato_ripeness_model.predict(image_array)
            idx = np.argmax(pred)
            ripeness = tomato_ripeness_names[idx][2:].strip()
            conf = float(pred[0][idx])
        else:
            ripeness, conf = None, None

        if ripeness:
            telemetry["ripeness"] = ripeness
            telemetry["ripeness_confidence"] = f"{conf:.4f}"
            print(f"🍅 Ripeness: {ripeness}, Confidence: {conf * 100:.2f}%")

        # Publish telemetry
        client.publish(telemetry_topic, json.dumps(telemetry))
        print(f"📡 Sent telemetry: {telemetry}")
        cv2.imshow("Image", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    except Exception as e:
        print("❌ Error processing image:", e)

# MQTT Setup
mqtt_client = mqtt.Client(client_name)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect("broker.hivemq.com", 1883, 60)
    mqtt_client.loop_forever()
except Exception as e:
    print("❌ MQTT connection error:", e)

# # Optionally show the image by its original dimensition
# display_image = ((image[0] + 1) * 127.5).astype(np.uint8)
# cv2.imshow("Input Image", display_image)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
