import time
import json
from geofence import GeofenceChecker
from telegram_notifier import TelegramNotifier

# Configuration - REPLACE THESE VALUES WITH YOUR OWN
GEOFENCE_FILE = "geofence.json"
GPS_DATA_FILE = "gps_data.json"
TELEGRAM_BOT_TOKEN = "7827931926:AAGYSibOnGJjXNygBx_kBnk5_66KhdCdwGc"  # Replace with your Telegram bot token
TELEGRAM_CHAT_ID = "7935793410"      # Replace with your chat ID
DEVICE_ID = "gps-sensor"

def process_gps_reading(lat, lon):
    """Process a GPS reading and check against geofence"""
    print(f"Processing GPS reading: lat={lat}, lon={lon}")
    
    # Check if the point is inside the geofence
    result = geofence_checker.check_point(lat, lon)
    
    # Print the result
    for geometry in result["geometries"]:
        distance = geometry["distance"]
        if distance == 999:
            print('Point is outside geofence')
        elif distance > 0:
            print(f'Point is just outside geofence by a distance of {distance:.2f}m')
        elif distance == -999:
            print('Point is inside geofence')
        else:
            print(f'Point is just inside geofence by a distance of {abs(distance):.2f}m')
    
    # Send notification via Telegram
    telegram_notifier.notify_geofence_status(DEVICE_ID, result)
    
    return result

def read_gps_data():
    """Read GPS readings from the JSON file and process them"""
    print(f"Reading GPS data from {GPS_DATA_FILE}...")
    
    try:
        with open(GPS_DATA_FILE, 'r') as f:
            gps_data = json.load(f)
        
        print(f"Found {len(gps_data)} GPS readings to process")
        
        for i, reading in enumerate(gps_data):
            print(f"\nProcessing reading {i+1}/{len(gps_data)}")
            process_gps_reading(reading["lat"], reading["lon"])
            time.sleep(2)  # Wait 2 seconds between readings
            
        print("\nAll GPS readings processed successfully")
        
    except FileNotFoundError:
        print(f"Error: Could not find {GPS_DATA_FILE}")
    except json.JSONDecodeError:
        print(f"Error: {GPS_DATA_FILE} is not a valid JSON file")
    except Exception as e:
        print(f"Error processing GPS data: {e}")

if __name__ == "__main__":
    print("GPS Geofence Checker with Telegram Notifications")
    print("===============================================")
    
    try:
        # Initialize the geofence checker
        print(f"Loading geofence from {GEOFENCE_FILE}...")
        geofence_checker = GeofenceChecker(GEOFENCE_FILE)
        
        # Initialize the Telegram notifier
        print("Initializing Telegram notifier...")
        telegram_notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        
        # Process the GPS data
        read_gps_data()
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
