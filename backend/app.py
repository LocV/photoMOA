from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import cv2
import numpy as np
from PIL import Image
import base64
from datetime import datetime
from shot_detector import ShotDetector
from moa_calculator import MOACalculator

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = '../uploads'
METADATA_FILE = 'metadata.json'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize components
shot_detector = ShotDetector()
moa_calculator = MOACalculator()

def load_metadata():
    """Load metadata from JSON file"""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_metadata(metadata):
    """Save metadata to JSON file"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def add_reference_scale(image, pixels_per_inch=None):
    """Add a 1-inch reference scale to the image"""
    height, width = image.shape[:2]
    
    # Use provided pixels_per_inch or default from MOA calculator
    if pixels_per_inch is None:
        pixels_per_inch = moa_calculator.pixels_per_inch
    scale_length_pixels = int(pixels_per_inch)
    
    # Position the scale in the top-right corner
    margin = 20
    scale_start_x = width - margin - scale_length_pixels
    scale_start_y = margin + 30
    scale_end_x = scale_start_x + scale_length_pixels
    scale_end_y = scale_start_y
    
    # Draw the scale line (thick white line with black border)
    cv2.line(image, (scale_start_x, scale_start_y), (scale_end_x, scale_end_y), (0, 0, 0), 5)  # Black border
    cv2.line(image, (scale_start_x, scale_start_y), (scale_end_x, scale_end_y), (255, 255, 255), 3)  # White line
    
    # Add tick marks at the ends
    tick_height = 10
    cv2.line(image, (scale_start_x, scale_start_y - tick_height//2), (scale_start_x, scale_start_y + tick_height//2), (0, 0, 0), 3)
    cv2.line(image, (scale_end_x, scale_end_y - tick_height//2), (scale_end_x, scale_end_y + tick_height//2), (0, 0, 0), 3)
    cv2.line(image, (scale_start_x, scale_start_y - tick_height//2), (scale_start_x, scale_start_y + tick_height//2), (255, 255, 255), 2)
    cv2.line(image, (scale_end_x, scale_end_y - tick_height//2), (scale_end_x, scale_end_y + tick_height//2), (255, 255, 255), 2)
    
    # Add text label
    label = "1 inch"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    font_thickness = 2
    
    # Get text size to center it above the scale
    (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, font_thickness)
    text_x = scale_start_x + (scale_length_pixels - text_width) // 2
    text_y = scale_start_y - 10
    
    # Draw text with black border for visibility
    cv2.putText(image, label, (text_x, text_y), font, font_scale, (0, 0, 0), font_thickness + 1)  # Black border
    cv2.putText(image, label, (text_x, text_y), font, font_scale, (255, 255, 255), font_thickness)  # White text
    
    return image

@app.route('/api/upload', methods=['POST'])
def upload_target():
    """Handle target photo upload and analysis"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save the uploaded file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"target_{timestamp}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Load and process the image
        image = cv2.imread(filepath)
        if image is None:
            return jsonify({'error': 'Invalid image file'}), 400
        
        # Detect shots in the image
        shots, annotated_image = shot_detector.detect_shots(image)
        
        # Add 1-inch reference scale to the image
        annotated_image = add_reference_scale(annotated_image)
        
        # Calculate MOA if shots are detected
        moa_value = None
        if len(shots) > 0:
            moa_value = moa_calculator.calculate_moa(shots)
        
        # Save annotated image
        annotated_filename = f"annotated_{filename}"
        annotated_filepath = os.path.join(app.config['UPLOAD_FOLDER'], annotated_filename)
        cv2.imwrite(annotated_filepath, annotated_image)
        
        # Convert annotated image to base64 for frontend display
        _, buffer = cv2.imencode('.jpg', annotated_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Create metadata entry
        metadata_entry = {
            'id': timestamp,
            'filename': filename,
            'annotated_filename': annotated_filename,
            'upload_time': datetime.now().isoformat(),
            'shot_count': len(shots),
            'moa_value': moa_value,
            'shots': shots.tolist() if shots is not None else []
        }
        
        # Update metadata
        metadata = load_metadata()
        metadata.append(metadata_entry)
        save_metadata(metadata)
        
        return jsonify({
            'success': True,
            'id': timestamp,
            'shot_count': len(shots),
            'moa_value': moa_value,
            'annotated_image': f"data:image/jpeg;base64,{img_base64}",
            'shots': shots.tolist() if shots is not None else []
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get upload history"""
    try:
        metadata = load_metadata()
        metadata.sort(key=lambda entry: entry['upload_time'], reverse=True)
        return jsonify(metadata)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/image/<filename>')
def get_image(filename):
    """Serve images from uploads folder"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/update-shots/<image_id>', methods=['POST'])
def update_shots(image_id):
    """Update shots with manual selections and recalculate MOA"""
    try:
        print(f"Received update request for image_id: {image_id}")
        data = request.get_json()
        print(f"Request data: {data}")
        manual_shots = data.get('manual_shots', [])
        print(f"Manual shots: {manual_shots}")
        
        # Load current metadata
        metadata = load_metadata()
        print(f"Loaded metadata with {len(metadata)} entries")
        
        # Find the image entry
        image_entry = None
        for entry in metadata:
            if entry['id'] == image_id:
                image_entry = entry
                break
        
        if not image_entry:
            print(f"Image entry not found for id: {image_id}")
            available_ids = [entry['id'] for entry in metadata]
            print(f"Available IDs: {available_ids}")
            return jsonify({'error': f'Image not found. Available IDs: {available_ids}'}), 404
        
        print(f"Found image entry: {image_entry['filename']}")
        
        # Load the original image
        original_filepath = os.path.join(app.config['UPLOAD_FOLDER'], image_entry['filename'])
        image = cv2.imread(original_filepath)
        if image is None:
            return jsonify({'error': 'Could not load original image'}), 400
        
        # Combine auto-detected shots with manual shots
        auto_shots = np.array(image_entry['shots']) if image_entry['shots'] else np.array([])
        manual_shots_array = np.array(manual_shots) if manual_shots else np.array([])
        
        print(f"Auto shots shape: {auto_shots.shape if len(auto_shots) > 0 else 'empty'}")
        print(f"Manual shots shape: {manual_shots_array.shape if len(manual_shots_array) > 0 else 'empty'}")
        
        # Normalize shot formats to ensure all have [x, y, radius]
        if len(auto_shots) > 0:
            if auto_shots.shape[1] == 2:  # Only x, y - add default radius
                auto_shots = np.column_stack([auto_shots, np.full(len(auto_shots), 10)])
            print(f"Normalized auto shots shape: {auto_shots.shape}")
        
        if len(manual_shots_array) > 0:
            if manual_shots_array.shape[1] == 2:  # Only x, y - add default radius
                manual_shots_array = np.column_stack([manual_shots_array, np.full(len(manual_shots_array), 10)])
            print(f"Normalized manual shots shape: {manual_shots_array.shape}")
        
        # Combine all shots
        if len(auto_shots) > 0 and len(manual_shots_array) > 0:
            all_shots = np.vstack([auto_shots, manual_shots_array])
        elif len(auto_shots) > 0:
            all_shots = auto_shots
        elif len(manual_shots_array) > 0:
            all_shots = manual_shots_array
        else:
            all_shots = np.array([])
        
        print(f"Combined shots shape: {all_shots.shape if len(all_shots) > 0 else 'empty'}")
        
        # Create new annotated image with all shots
        annotated_image = image.copy()
        if len(all_shots) > 0:
            for shot in all_shots:
                x, y, radius = int(shot[0]), int(shot[1]), int(shot[2])
                # Draw circle around detected shot
                cv2.circle(annotated_image, (x, y), radius, (0, 255, 0), 2)
                # Draw center point
                cv2.circle(annotated_image, (x, y), 2, (0, 0, 255), -1)
        
        # Add 1-inch reference scale to the updated image (use calibrated scale if available)
        scale_pixels_per_inch = image_entry['calibration']['pixels_per_inch'] if 'calibration' in image_entry else None
        annotated_image = add_reference_scale(annotated_image, scale_pixels_per_inch)
        
        # Recalculate MOA with all shots using calibration if available
        moa_value = None
        if len(all_shots) > 0:
            if 'calibration' in image_entry:
                # Use calibrated pixels_per_inch
                temp_calculator = MOACalculator()
                temp_calculator.set_calibration(image_entry['calibration']['pixels_per_inch'], 100)
                moa_value = temp_calculator.calculate_moa(all_shots)
            else:
                # Use default calibration
                moa_value = moa_calculator.calculate_moa(all_shots)
        
        # Save updated annotated image
        annotated_filepath = os.path.join(app.config['UPLOAD_FOLDER'], image_entry['annotated_filename'])
        cv2.imwrite(annotated_filepath, annotated_image)
        
        # Convert annotated image to base64
        _, buffer = cv2.imencode('.jpg', annotated_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Update metadata entry
        image_entry['shot_count'] = len(all_shots)
        image_entry['moa_value'] = moa_value
        image_entry['shots'] = all_shots.tolist() if len(all_shots) > 0 else []
        image_entry['manual_shots'] = manual_shots
        image_entry['last_updated'] = datetime.now().isoformat()
        
        # Save updated metadata
        save_metadata(metadata)
        
        return jsonify({
            'success': True,
            'id': image_id,
            'shot_count': len(all_shots),
            'moa_value': moa_value,
            'annotated_image': f"data:image/jpeg;base64,{img_base64}",
            'shots': all_shots.tolist() if len(all_shots) > 0 else [],
            'manual_shots': manual_shots
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calibrate/<image_id>', methods=['POST'])
def calibrate_scale(image_id):
    """Calibrate the scale for an image using two reference points"""
    try:
        data = request.get_json()
        point1 = data.get('point1')  # [x, y]
        point2 = data.get('point2')  # [x, y]
        distance_inches = float(data.get('distance_inches', 1.0))
        
        if not point1 or not point2:
            return jsonify({'error': 'Two calibration points required'}), 400
        
        # Calculate pixel distance between the two points
        pixel_distance = ((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)**0.5
        
        if pixel_distance == 0:
            return jsonify({'error': 'Points cannot be the same'}), 400
        
        # Calculate pixels per inch
        pixels_per_inch = pixel_distance / distance_inches
        
        # Load current metadata
        metadata = load_metadata()
        
        # Find the image entry
        image_entry = None
        for entry in metadata:
            if entry['id'] == image_id:
                image_entry = entry
                break
        
        if not image_entry:
            return jsonify({'error': 'Image not found'}), 404
        
        # Update the calibration data
        image_entry['calibration'] = {
            'point1': point1,
            'point2': point2,
            'distance_inches': distance_inches,
            'pixels_per_inch': pixels_per_inch
        }
        
        # Recalculate MOA with new calibration if shots exist
        if image_entry['shots']:
            # Create a temporary MOA calculator with the new calibration
            temp_calculator = MOACalculator()
            temp_calculator.set_calibration(pixels_per_inch, 100)  # Keep 100 yards as default distance
            
            shots_array = np.array(image_entry['shots'])
            if len(shots_array) > 0:
                image_entry['moa_value'] = temp_calculator.calculate_moa(shots_array)
        
        # Regenerate annotated image with new calibrated reference scale
        original_filepath = os.path.join(app.config['UPLOAD_FOLDER'], image_entry['filename'])
        image = cv2.imread(original_filepath)
        if image is not None:
            # Create new annotated image with existing shots
            annotated_image = image.copy()
            if image_entry['shots']:
                shots_array = np.array(image_entry['shots'])
                # Ensure shots have radius values
                if len(shots_array) > 0:
                    if shots_array.shape[1] == 2:  # Only x, y - add default radius
                        shots_array = np.column_stack([shots_array, np.full(len(shots_array), 10)])
                    
                    for shot in shots_array:
                        x, y, radius = int(shot[0]), int(shot[1]), int(shot[2])
                        # Draw circle around detected shot
                        cv2.circle(annotated_image, (x, y), radius, (0, 255, 0), 2)
                        # Draw center point
                        cv2.circle(annotated_image, (x, y), 2, (0, 0, 255), -1)
            
            # Add reference scale with new calibrated pixels_per_inch
            annotated_image = add_reference_scale(annotated_image, pixels_per_inch)
            
            # Save updated annotated image
            annotated_filepath = os.path.join(app.config['UPLOAD_FOLDER'], image_entry['annotated_filename'])
            cv2.imwrite(annotated_filepath, annotated_image)
        
        # Save updated metadata
        save_metadata(metadata)
        
        return jsonify({
            'success': True,
            'pixels_per_inch': pixels_per_inch,
            'moa_value': image_entry.get('moa_value')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete/<image_id>', methods=['DELETE'])
def delete_target(image_id):
    """Delete a target and its associated files"""
    try:
        # Load current metadata
        metadata = load_metadata()
        
        # Find the image entry
        image_entry = None
        entry_index = None
        for i, entry in enumerate(metadata):
            if entry['id'] == image_id:
                image_entry = entry
                entry_index = i
                break
        
        if not image_entry:
            return jsonify({'error': 'Image not found'}), 404
        
        # Delete the actual image files
        original_filepath = os.path.join(app.config['UPLOAD_FOLDER'], image_entry['filename'])
        annotated_filepath = os.path.join(app.config['UPLOAD_FOLDER'], image_entry['annotated_filename'])
        
        # Remove files if they exist
        if os.path.exists(original_filepath):
            os.remove(original_filepath)
        if os.path.exists(annotated_filepath):
            os.remove(annotated_filepath)
        
        # Remove entry from metadata
        metadata.pop(entry_index)
        save_metadata(metadata)
        
        return jsonify({'success': True, 'message': 'Target deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'photoMOA backend'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
