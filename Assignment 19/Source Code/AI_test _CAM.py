from roboflow import Roboflow
import cv2
import os
import requests
import time
import threading
import queue
import numpy as np
from collections import Counter

# Set a timeout for API requests
requests.adapters.DEFAULT_TIMEOUT = 15  # Reduced timeout for faster failure recovery

# Global variables for threading
frame_queue = queue.Queue(maxsize=1)  # Only keep the latest frame
result_queue = queue.Queue(maxsize=1)  # Only keep the latest result
processing_active = True

def initialize_model():
    """Initialize the Roboflow model"""
    try:
        print("Connecting to Roboflow...")
        # Initialize Roboflow with your API key
        rf = Roboflow(api_key="2Wxvb1TBqXbPnB3hujVr")
        
        # Load your project and model version
        project = rf.workspace().project("bottles-detection-real")
        model = project.version(3).model
        print("Successfully connected to Roboflow!")
        return model
    except Exception as e:
        print(f"Error connecting to Roboflow: {e}")
        return None

def process_frames(model):
    """Process frames in a separate thread"""
    global processing_active
    
    # Set up temp directory for saving frames
    temp_dir = "temp_frames"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # Create multiple temp files to avoid file access conflicts
    temp_frame_paths = [
        os.path.join(temp_dir, f"temp_frame_{i}.jpg") for i in range(3)
    ]
    current_temp_idx = 0
    
    # Track processing speed
    process_count = 0
    start_time = time.time()
    
    while processing_active:
        try:
            # Get the latest frame from the queue, non-blocking
            try:
                frame = frame_queue.get(block=False)
            except queue.Empty:
                # No new frame available, sleep briefly and try again
                time.sleep(0.01)
                continue
            
            # Use the next temp file in rotation
            temp_frame_path = temp_frame_paths[current_temp_idx]
            current_temp_idx = (current_temp_idx + 1) % len(temp_frame_paths)
            
            # Save current frame to temp file with lower quality for speed
            cv2.imwrite(temp_frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            
            # Run inference on the saved frame
            try:
                result = model.predict(temp_frame_path, confidence=40, overlap=30).json()
                
                # Put the result in the queue, replacing any old result
                try:
                    # Clear the queue first
                    while not result_queue.empty():
                        result_queue.get_nowait()
                    # Add new result
                    result_queue.put((frame, result))
                except Exception as e:
                    print(f"Error updating result: {e}")
                
                # Track processing speed
                process_count += 1
                
            except requests.exceptions.Timeout:
                print("API request timed out, continuing...")
            except Exception as e:
                print(f"Error in prediction: {e}")
                
        except Exception as e:
            print(f"Error in processing thread: {e}")
            time.sleep(0.1)  # Avoid tight loop on error
    
    # Clean up temp files
    try:
        for path in temp_frame_paths:
            if os.path.exists(path):
                os.remove(path)
        os.rmdir(temp_dir)
    except Exception as e:
        print(f"Error cleaning up temp files: {e}")

class PredictionSmoother:
    """Class to smooth predictions and reduce flickering"""
    def __init__(self, history_size=3, iou_threshold=0.3, confidence_threshold=0.4):
        self.history_size = history_size
        self.iou_threshold = iou_threshold
        self.confidence_threshold = confidence_threshold
        self.prediction_history = []
        
    def update(self, predictions):
        """Add new predictions to history"""
        self.prediction_history.append(predictions)
        if len(self.prediction_history) > self.history_size:
            self.prediction_history.pop(0)
    
    def get_smoothed_predictions(self):
        """Get smoothed predictions based on history"""
        if not self.prediction_history:
            return []
        
        # Flatten all predictions from history
        all_preds = []
        for preds in self.prediction_history:
            for pred in preds:
                if pred['confidence'] >= self.confidence_threshold:
                    all_preds.append(pred)
        
        if not all_preds:
            return []
        
        # Group similar predictions
        grouped_preds = []
        used_indices = set()
        
        for i, pred in enumerate(all_preds):
            if i in used_indices:
                continue
                
            group = [pred]
            used_indices.add(i)
            
            for j, other_pred in enumerate(all_preds):
                if j in used_indices or j == i:
                    continue
                
                if (pred['class'] == other_pred['class'] and 
                    self._calculate_iou(pred, other_pred) >= self.iou_threshold):
                    group.append(other_pred)
                    used_indices.add(j)
            
            # Average the group
            if group:
                avg_pred = self._average_predictions(group)
                grouped_preds.append(avg_pred)
        
        return grouped_preds
    
    def _calculate_iou(self, box1, box2):
        """Calculate IoU between two bounding boxes"""
        # Convert from center format to corner format
        x1_1, y1_1 = box1['x'] - box1['width']/2, box1['y'] - box1['height']/2
        x2_1, y2_1 = box1['x'] + box1['width']/2, box1['y'] + box1['height']/2
        
        x1_2, y1_2 = box2['x'] - box2['width']/2, box2['y'] - box2['height']/2
        x2_2, y2_2 = box2['x'] + box2['width']/2, box2['y'] + box2['height']/2
        
        # Calculate intersection area
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        intersection_area = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Calculate union area
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = box1_area + box2_area - intersection_area
        
        if union_area <= 0:
            return 0.0
            
        return intersection_area / union_area
    
    def _average_predictions(self, predictions):
        """Average a group of similar predictions"""
        avg_x = sum(p['x'] for p in predictions) / len(predictions)
        avg_y = sum(p['y'] for p in predictions) / len(predictions)
        avg_width = sum(p['width'] for p in predictions) / len(predictions)
        avg_height = sum(p['height'] for p in predictions) / len(predictions)
        avg_confidence = sum(p['confidence'] for p in predictions) / len(predictions)
        
        # Use the most common class
        classes = [p['class'] for p in predictions]
        class_counts = {}
        for c in classes:
            class_counts[c] = class_counts.get(c, 0) + 1
        most_common_class = max(class_counts.items(), key=lambda x: x[1])[0]
        
        return {
            'x': avg_x,
            'y': avg_y,
            'width': avg_width,
            'height': avg_height,
            'confidence': avg_confidence,
            'class': most_common_class
        }

def run_bottle_detection():
    """Run real-time bottle detection using webcam"""
    global processing_active
    
    # First, verify OpenCV installation
    print(f"OpenCV version: {cv2.__version__}")
    if not hasattr(cv2, 'VideoCapture'):
        print("ERROR: Your OpenCV installation doesn't have VideoCapture functionality.")
        print("Please reinstall OpenCV with: pip install opencv-contrib-python")
        return
    
    # Initialize model
    model = initialize_model()
    if model is None:
        print("Exiting due to connection issues.")
        return
    
    # Try to open the camera
    print("Trying to open camera...")
    try:
        cap = cv2.VideoCapture(0)
    except Exception as e:
        print(f"Error opening camera: {e}")
        return
    
    if not cap.isOpened():
        print("Could not open camera. Please check your camera connection.")
        return
    
    # Set camera properties for higher FPS
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Lower resolution for speed
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)  # Request 30 FPS
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffering
    
    print("Camera initialized. Press 'q' to quit.")
    
    # Initialize prediction smoother with shorter history for faster response
    smoother = PredictionSmoother(history_size=3, iou_threshold=0.3)
    
    # Start processing thread
    processing_thread = threading.Thread(target=process_frames, args=(model,))
    processing_thread.daemon = True
    processing_thread.start()
    
    frame_count = 0
    fps_start_time = time.time()
    fps = 0
    last_predictions = []
    
    try:
        while True:
            # Read frame from webcam
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            frame_count += 1
            
            # Calculate FPS
            if frame_count % 10 == 0:
                current_time = time.time()
                elapsed = current_time - fps_start_time
                if elapsed > 0:
                    fps = 10 / elapsed
                fps_start_time = current_time
            
            # Update the frame queue (replace old frame with new one)
            try:
                # Clear the queue first
                while not frame_queue.empty():
                    frame_queue.get_nowait()
                # Add new frame
                frame_queue.put(frame.copy())
            except Exception as e:
                print(f"Error updating frame queue: {e}")
            
            # Check if we have a result to display
            display_frame = frame.copy()
            try:
                if not result_queue.empty():
                    _, result = result_queue.get_nowait()
                    
                    # Update prediction history
                    predictions = result.get('predictions', [])
                    smoother.update(predictions)
                    
                    # Get smoothed predictions
                    last_predictions = smoother.get_smoothed_predictions()
            except Exception as e:
                print(f"Error processing result: {e}")
            
            # Count objects by class
            object_counts = Counter([pred['class'] for pred in last_predictions])
            total_objects = len(last_predictions)
            
            # Draw the smoothed predictions
            for pred in last_predictions:
                x, y, w, h = pred['x'], pred['y'], pred['width'], pred['height']
                label = pred['class']
                conf = pred['confidence']
                
                x1 = int(x - w / 2)
                y1 = int(y - h / 2)
                x2 = int(x + w / 2)
                y2 = int(y + h / 2)
                
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(display_frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Add object counts to the frame
            y_offset = 30
            cv2.putText(display_frame, f"Total Objects: {total_objects}", (10, y_offset), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Display count for each object type
            for i, (obj_class, count) in enumerate(object_counts.items()):
                y_offset += 30
                cv2.putText(display_frame, f"{obj_class}: {count}", (10, y_offset), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Display the frame
            try:
                cv2.imshow('Bottle Detection', display_frame)
            except Exception as e:
                print(f"Error displaying frame: {e}")
                break
            
            # Check for key press to exit (use a short wait time for higher responsiveness)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Clean up
        processing_active = False
        if processing_thread.is_alive():
            processing_thread.join(timeout=1.0)
        
        if cap is not None:
            cap.release()
        
        try:
            cv2.destroyAllWindows()
        except Exception as e:
            print(f"Error destroying windows: {e}")

if __name__ == "__main__":
    run_bottle_detection()
