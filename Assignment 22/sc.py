import speech_recognition as sr
import pyttsx3
import re
import time
import threading

recognizer = sr.Recognizer()
tts_engine = pyttsx3.init()
stop_flag = threading.Event()  # shared flag to stop the timer
tts_lock = threading.Lock()  # Add a lock for TTS operations


def speak(text):
    with tts_lock:  # Use a lock to prevent concurrent access
        tts_engine.say(text)
        tts_engine.runAndWait()


def get_voice_command(prompt="What timer do you want to set?"):
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


def extract_time(command):
    match = re.search(r'(\d+)\s*(second|seconds|minute|minutes|hour|hours)', command)
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if 'second' in unit:
        return value
    elif 'minute' in unit:
        return value * 60
    elif 'hour' in unit:
        return value * 3600
    else:
        return None


def run_timer(duration):
    speak(f"Timer started for {duration} seconds.")
    start_time = time.time()
    while time.time() - start_time < duration:
        if stop_flag.is_set():
            speak("Timer has been stopped.")
            print("Timer was manually stopped.")
            return
        time.sleep(1)
    speak("Time's up! Executing your command.")
    print("Timer finished. Running command...")
    # Replace this with your custom command
    print(">> Your command goes here.")


def listen_for_stop():
    while not stop_flag.is_set():
        # Modified to avoid continuous prompting
        print("Say 'stop' to cancel.")
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
                command = recognizer.recognize_google(audio).lower()
                print(f"You said: {command}")
                if "stop" in command:
                    stop_flag.set()
                    print("Stop command received. Stopping the timer.")
                    return
            except sr.WaitTimeoutError:
                # Just continue listening
                pass
            except sr.UnknownValueError:
                # Just continue listening
                pass
            
            # Check if timer has been stopped by other means
            if stop_flag.is_set():
                return


def main():
    stop_flag.clear()  # Reset the stop flag
    command = get_voice_command()
    timer_duration = extract_time(command)

    if timer_duration:
        timer_thread = threading.Thread(target=run_timer, args=(timer_duration,))
        stop_listener_thread = threading.Thread(target=listen_for_stop)

        timer_thread.start()
        stop_listener_thread.start()

        timer_thread.join()
        # Set the stop flag to ensure the listener thread exits
        stop_flag.set()
        stop_listener_thread.join()
    else:
        speak("Sorry, I couldn't understand the timer duration.")


if __name__ == "__main__":
    main()
