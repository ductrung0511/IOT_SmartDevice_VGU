import requests

class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        """
        Initialize the Telegram notifier
        
        Args:
            bot_token (str): Your Telegram bot token from BotFather
            chat_id (str): Your chat ID (can be obtained from getUpdates API)
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}/"
        self.last_status = {}  # Store the last status for each device/geometry
    
    def send_message(self, message):
        """Send a message via Telegram bot"""
        url = self.base_url + "sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
            print("Telegram notification sent successfully")
            return True
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")
            return False
    
    def notify_geofence_status(self, device_id, geofence_result):
        """Send notification about geofence status with detailed distance information"""
        for geometry in geofence_result["geometries"]:
            geometry_id = geometry["geometryId"]
            distance = geometry["distance"]
            nearest_lat = geometry.get("nearestLat", "N/A")
            nearest_lon = geometry.get("nearestLon", "N/A")
            is_inside = distance < 0
            
            # Create a unique key for this device and geometry
            status_key = f"{device_id}_{geometry_id}"
            
            # Check if we have a previous status for this device/geometry
            previous_inside = self.last_status.get(status_key, None)
            status_changed = previous_inside is not None and previous_inside != is_inside
            
            # Format the distance information
            if distance == 999:
                distance_info = "well outside (more than 50m from boundary)"
            elif distance == -999:
                distance_info = "well inside (more than 50m from boundary)"
            elif distance > 0:
                distance_info = f"{distance:.2f}m outside the boundary"
            else:
                distance_info = f"{abs(distance):.2f}m inside the boundary"
            
            # Format the message with detailed information
            if status_changed:
                # Status changed notification
                if is_inside:
                    message = (
                        f"🚨 <b>ALERT: Device {device_id} has ENTERED geofence {geometry_id}</b>\n\n"
                        f"Current position: {distance_info}\n"
                        f"Nearest point on geofence: {nearest_lat}, {nearest_lon}"
                    )
                else:
                    message = (
                        f"😀 <b>ALERT: Device {device_id} has EXITED geofence {geometry_id}</b>\n\n"
                        f"Current position: {distance_info}\n"
                        f"Nearest point on geofence: {nearest_lat}, {nearest_lon}"
                    )
            else:
                # Regular status notification
                if is_inside:
                    message = (
                        f"😀 <b>Device {device_id} is inside geofence {geometry_id}</b>\n\n"
                        f"Position: {distance_info}\n"
                        f"Nearest point on geofence: {nearest_lat}, {nearest_lon}"
                    )
                else:
                    message = (
                        f"😀 <b>Device {device_id} is outside geofence {geometry_id}</b>\n\n"
                        f"Position: {distance_info}\n"
                        f"Nearest point on geofence: {nearest_lat}, {nearest_lon}"
                    )
            
            # Send the message
            self.send_message(message)
            
            # Update the last status
            self.last_status[status_key] = is_inside