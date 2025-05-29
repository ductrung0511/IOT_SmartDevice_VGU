from roboflow import Roboflow
import cv2
import os
import requests
import time

# Set a timeout for API requests
requests.adapters.DEFAULT_TIMEOUT = 30

def initialize_model(max_retries=3, retry_delay=5):
    """Initialize the Roboflow model with retry logic"""
    for attempt in range(max_retries):
        try:
            print(f"Connecting to Roboflow (attempt {attempt+1}/{max_retries})...")
            # Initialize Roboflow with your API key
            rf = Roboflow(api_key="2Wxvb1TBqXbPnB3hujVr")
            
            # Load your project and model version
            project = rf.workspace().project("bottles-detection-real")
            model = project.version(3).model
            print("Successfully connected to Roboflow!")
            return model
        except requests.exceptions.Timeout:
            print(f"Connection timed out. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        except Exception as e:
            print(f"Error connecting to Roboflow: {e}")
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    print("Failed to connect to Roboflow after multiple attempts.")
    return None

def process_single_image(image_path, output_path=None):
    """Process a single image file without using GUI components"""
    # Initialize model
    model = initialize_model()
    if model is None:
        print("Exiting due to connection issues.")
        return
    
    try:
        print(f"Processing {os.path.basename(image_path)}...")
        
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Failed to read image: {image_path}")
            return
        
        # Run inference
        result = model.predict(image_path, confidence=40, overlap=30).json()
        
        # Draw predictions
        detection_count = 0
        for pred in result.get('predictions', []):
            detection_count += 1
            x, y, w, h = pred['x'], pred['y'], pred['width'], pred['height']
            label = pred['class']
            conf = pred['confidence']
            
            x1 = int(x - w / 2)
            y1 = int(y - h / 2)
            x2 = int(x + w / 2)
            y2 = int(y + h / 2)
            
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(image, f"{label} {conf:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        print(f"Found {detection_count} objects in the image.")
        
        # Save the output image
        if output_path:
            cv2.imwrite(output_path, image)
            print(f"Saved result to {output_path}")
        else:
            # If no output path is provided, create one based on the input filename
            base_dir = os.path.dirname(image_path)
            base_name = os.path.basename(image_path)
            output_path = os.path.join(base_dir, f"detected_{base_name}")
            cv2.imwrite(output_path, image)
            print(f"Saved result to {output_path}")
            
    except requests.exceptions.Timeout:
        print(f"API request timed out for {image_path}")
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def process_folder(input_folder, output_folder=None):
    """Process all images in the input folder"""
    # Create output folder if specified and doesn't exist
    if output_folder and not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Get all image files in the input folder
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_paths = []
    
    for ext in image_extensions:
        image_paths.extend([os.path.join(input_folder, f) for f in os.listdir(input_folder) 
                           if f.lower().endswith(ext)])
    
    if not image_paths:
        print(f"No images found in {input_folder}")
        return
    
    print(f"Found {len(image_paths)} images to process.")
    
    # Initialize model only once for all images
    model = initialize_model()
    if model is None:
        print("Exiting due to connection issues.")
        return
    
    for img_path in image_paths:
        try:
            base_name = os.path.basename(img_path)
            output_path = os.path.join(output_folder, f"detected_{base_name}") if output_folder else None
            
            print(f"Processing {base_name}...")
            
            # Read the image
            image = cv2.imread(img_path)
            if image is None:
                print(f"Failed to read image: {img_path}")
                continue
            
            # Run inference
            result = model.predict(img_path, confidence=40, overlap=30).json()
            
            # Draw predictions
            detection_count = 0
            for pred in result.get('predictions', []):
                detection_count += 1
                x, y, w, h = pred['x'], pred['y'], pred['width'], pred['height']
                label = pred['class']
                conf = pred['confidence']
                
                x1 = int(x - w / 2)
                y1 = int(y - h / 2)
                x2 = int(x + w / 2)
                y2 = int(y + h / 2)
                
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(image, f"{label} {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            print(f"Found {detection_count} objects in {base_name}.")
            
            # Save the output image
            if output_path:
                cv2.imwrite(output_path, image)
                print(f"Saved result to {output_path}")
            else:
                # If no output path is provided, create one based on the input filename
                base_dir = os.path.dirname(img_path)
                output_path = os.path.join(base_dir, f"detected_{base_name}")
                cv2.imwrite(output_path, image)
                print(f"Saved result to {output_path}")
                
        except requests.exceptions.Timeout:
            print(f"API request timed out for {img_path}")
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

if __name__ == "__main__":
    # Choose whether to process a single image or a folder
    process_mode = "single"  # Change to "folder" to process multiple images
    
    if process_mode == "folder":
        # Specify your input and output file paths
        input_image = "20250525_145015.jpg"  # Change this to your image file path
        output_image = "detected_20250525_145015.jpg"  # Change this to your desired output path
        
        process_single_image(input_image, output_image)
    else:
        # Specify your input and output folders
        input_folder = "input_images"  # Change this to your folder with images
        output_folder = "output_images"  # Change this to where you want to save results
        
        process_folder(input_folder, output_folder)

