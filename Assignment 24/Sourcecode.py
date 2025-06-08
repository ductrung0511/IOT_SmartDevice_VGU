import speech_recognition as sr
import pyttsx3
import re
import time
import threading
import paho.mqtt.client as mqtt
from googletrans import Translator  # Add this import

# Initialize the translator
translator = Translator()

id = "2fdac31a-b52e-4ea4-a2f6-4e6629111b7e"
translate_topic = id + "/translate_topic"

recognizer = sr.Recognizer()
tts_engine = pyttsx3.init()
stop_flag = threading.Event()  # shared flag to stop the timer
tts_lock = threading.Lock()  # Add a lock for TTS operations


connected_once = False  # Global flag

def on_connect(client, userdata, flags, rc):
    global connected_once
    if rc == 0:
        if not connected_once:
            print("✅ Connected to MQTT Broker")
            client.subscribe(translate_topic)
            connected_once = True
    else:
        print(f"❌ MQTT connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        stop_flag.set()  # STOP voice input loop immediately

        german_text = msg.payload.decode()
        print(f"\n📩 Received (German): {german_text}")

        # Translate German to English
        translation = translator.translate(german_text, src='de', dest='en')
        english_text = translation.text
        print(f"🌐 Translated (English): {english_text}")

        # Speak translation
        speak(f"The translation is: {english_text}")

        stop_flag.clear()  # RESUME voice input loop after speaking

    except Exception as e:
        print(f"❌ Error during translation: {e}")
        stop_flag.clear()  # Make sure to clear the flag even on error


def speak(text):
    with tts_lock:  # Use a lock to prevent concurrent access
        tts_engine.say(text)
        tts_engine.runAndWait()


def get_voice_command(prompt="Say what  you want translate to other person ?"):
    with sr.Microphone() as source:
        print(prompt)
        speak(prompt)
        audio = recognizer.listen(source)
    try:
        command = recognizer.recognize_google(audio)
        print(f"You said: {command}")
        return command.lower()
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
        return ""




def send_to_MQTT(client, command):
    client.publish(translate_topic, command)
    print(f"📡 Sent telemetry: {command}")

def main():
    client_name = id + "translate_client"
    stop_flag.clear()
    mqtt_client = mqtt.Client(client_name)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    try:
        mqtt_client.connect("broker.hivemq.com", 1883, 60)
        mqtt_client.loop_start()  # Start MQTT in background
        # Start thread for continuous voice input and sending
        def voice_loop():
            while not stop_flag.is_set():
                command = get_voice_command()
                if command:
                    send_to_MQTT(mqtt_client, command)
                time.sleep(0.5)  # Optional: short pause between messages

        voice_thread = threading.Thread(target=voice_loop)
        voice_thread.start()

        # Keep the main thread alive to receive MQTT messages
        while True:
            time.sleep(1)
    except Exception as e:
        print("❌ MQTT connection error:", e)


if __name__ == "__main__":
    main()
