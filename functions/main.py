from firebase_functions import https_fn
from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, storage, firestore
import os
import json
import cv2
import numpy as np
from PIL import Image
import base64
from datetime import datetime
from shot_detector import ShotDetector
from moa_calculator import MOACalculator
import tempfile
import io

# Global variables for Firebase services (initialized lazily)
db = None
bucket = None

def get_firebase_services():
    """Initialize Firebase services lazily"""
    global db, bucket
    if db is None:
        # Initialize Firebase Admin SDK if not already done
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        
        # Initialize Firestore and Storage
        db = firestore.client()
        # Use the specific storage bucket
        bucket = storage.bucket('bulletbaseai.firebasestorage.app')
    
    return db, bucket

# Initialize components
shot_detector = ShotDetector()
moa_calculator = MOACalculator()

def load_metadata():
    """Load metadata from Firestore"""
    try:
        db, bucket = get_firebase_services()
        docs = db.collection('targets').stream()
        metadata = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            metadata.append(data)
        return metadata
    except Exception as e:
        print(f"Error loading metadata: {e}")
        return []

def save_metadata(metadata_entry):
    """Save single metadata entry to Firestore"""
    try:
        db, bucket = get_firebase_services()
        doc_ref = db.collection('targets').document(metadata_entry['id'])
        doc_ref.set(metadata_entry)
        return True
    except Exception as e:
        print(f"Error saving metadata: {e}")
        return False

def update_metadata(image_id, updates):
    """Update specific fields in metadata"""
    try:
        db, bucket = get_firebase_services()
        doc_ref = db.collection('targets').document(image_id)
        doc_ref.update(updates)
        return True
    except Exception as e:
        print(f"Error updating metadata: {e}")
        return False
def delete_metadata(image_id):
    """Delete metadata entry from Firestore"""
    try:
        db, bucket = get_firebase_services()
        db.collection('targets').document(image_id).delete()
        return True
    except Exception as e:
        print(f"Error deleting metadata: {e}")
        return False

def upload_to_storage(file_data, filename):
    """Upload file to Firebase Storage"""
    try:
        db, bucket = get_firebase_services()
        blob = bucket.blob(f"uploads/{filename}")
        blob.upload_from_string(file_data)
        blob.make_public()
        return blob.public_url
    except Exception as e:
        print(f"Error uploading to storage: {e}")
        return None

def download_from_storage(filename):
    """Download file from Firebase Storage"""
    try:
        db, bucket = get_firebase_services()
        blob = bucket.blob(f"uploads/{filename}")
        return blob.download_as_bytes()
    except Exception as e:
        print(f"Error downloading from storage: {e}")
        return None

def delete_from_storage(filename):
    """Delete file from Firebase Storage"""
    try:
        db, bucket = get_firebase_services()
        blob = bucket.blob(f"uploads/{filename}")
        blob.delete()
        return True
    except Exception as e:
        print(f"Error deleting from storage: {e}")
        return False

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

@https_fn.on_request()
def api(request: https_fn.Request):
    """Main Firebase Function that handles all PhotoMOA API requests"""
    
    # Handle CORS
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    
    # Set CORS headers for actual requests
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }
    
    try:
        path = request.path
        method = request.method
        
        # Remove leading /api if present (due to Firebase routing)
        if path.startswith('/api/'):
            path = path[4:]  # Remove '/api'
        
        # Route requests based on path and method
        if path.startswith('/upload') and method == 'POST':
            return handle_upload(request, headers)
        elif path.startswith('/history') and method == 'GET':
            return handle_history(request, headers)
        elif path.startswith('/update-shots/') and method == 'POST':
            image_id = path.split('/update-shots/')[1]
            return handle_update_shots(request, image_id, headers)
        elif path.startswith('/calibrate/') and method == 'POST':
            image_id = path.split('/calibrate/')[1]
            return handle_calibrate(request, image_id, headers)
        elif path.startswith('/delete/') and method == 'DELETE':
            image_id = path.split('/delete/')[1]
            return handle_delete(request, image_id, headers)
        elif path.startswith('/image/') and method == 'GET':
            filename = path.split('/image/')[1]
            return handle_get_image(request, filename, headers)
        elif path.startswith('/health') and method == 'GET':
            return handle_health(request, headers)
        else:
            return jsonify({'error': 'Endpoint not found'}), 404, headers
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500, headers

def handle_upload(request, headers):
    """Handle target photo upload and analysis"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400, headers
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400, headers
        
        # Generate timestamp and filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"target_{timestamp}_{file.filename}"
        annotated_filename = f"annotated_{filename}"
        
        # Read image data
        image_data = file.read()
        
        # Convert to OpenCV format
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'error': 'Invalid image file'}), 400, headers
        
        # Detect shots in the image
        shots, annotated_image = shot_detector.detect_shots(image)
        
        # Add 1-inch reference scale to the image
        annotated_image = add_reference_scale(annotated_image)
        
        # Calculate MOA if shots are detected
        moa_value = None
        if len(shots) > 0:
            moa_value = moa_calculator.calculate_moa(shots)
        
        # Upload original image to storage
        upload_to_storage(image_data, filename)
        
        # Upload annotated image to storage
        _, buffer = cv2.imencode('.jpg', annotated_image)
        annotated_image_data = buffer.tobytes()
        upload_to_storage(annotated_image_data, annotated_filename)
        
        # Convert annotated image to base64 for frontend display
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
        
        # Save metadata to Firestore
        save_metadata(metadata_entry)
        
        return jsonify({
            'success': True,
            'id': timestamp,
            'shot_count': len(shots),
            'moa_value': moa_value,
            'annotated_image': f"data:image/jpeg;base64,{img_base64}",
            'shots': shots.tolist() if shots is not None else []
        }), 200, headers
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500, headers

def handle_history(request, headers):
    """Get upload history"""
    try:
        metadata = load_metadata()
        metadata.sort(key=lambda entry: entry['upload_time'], reverse=True)
        return jsonify(metadata), 200, headers
    except Exception as e:
        return jsonify({'error': str(e)}), 500, headers

def handle_update_shots(request, image_id, headers):
    """Update shots with manual selections and recalculate MOA"""
    try:
        data = request.get_json()
        manual_shots = data.get('manual_shots', [])
        
        # Get metadata from Firestore
        db, bucket = get_firebase_services()
        doc_ref = db.collection('targets').document(image_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Image not found'}), 404, headers
        
        image_entry = doc.to_dict()
        
        # Download original image from storage
        image_data = download_from_storage(image_entry['filename'])
        if image_data is None:
            return jsonify({'error': 'Could not load original image'}), 400, headers
        
        # Convert to OpenCV format
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Combine auto-detected shots with manual shots
        auto_shots = np.array(image_entry['shots']) if image_entry['shots'] else np.array([])
        manual_shots_array = np.array(manual_shots) if manual_shots else np.array([])
        
        # Normalize shot formats
        if len(auto_shots) > 0 and auto_shots.shape[1] == 2:
            auto_shots = np.column_stack([auto_shots, np.full(len(auto_shots), 10)])
        
        if len(manual_shots_array) > 0 and manual_shots_array.shape[1] == 2:
            manual_shots_array = np.column_stack([manual_shots_array, np.full(len(manual_shots_array), 10)])
        
        # Combine all shots
        if len(auto_shots) > 0 and len(manual_shots_array) > 0:
            all_shots = np.vstack([auto_shots, manual_shots_array])
        elif len(auto_shots) > 0:
            all_shots = auto_shots
        elif len(manual_shots_array) > 0:
            all_shots = manual_shots_array
        else:
            all_shots = np.array([])
        
        # Create new annotated image
        annotated_image = image.copy()
        if len(all_shots) > 0:
            for shot in all_shots:
                x, y, radius = int(shot[0]), int(shot[1]), int(shot[2])
                cv2.circle(annotated_image, (x, y), radius, (0, 255, 0), 2)
                cv2.circle(annotated_image, (x, y), 2, (0, 0, 255), -1)
        
        # Add reference scale
        scale_pixels_per_inch = image_entry.get('calibration', {}).get('pixels_per_inch')
        annotated_image = add_reference_scale(annotated_image, scale_pixels_per_inch)
        
        # Recalculate MOA
        moa_value = None
        if len(all_shots) > 0:
            if 'calibration' in image_entry:
                temp_calculator = MOACalculator()
                temp_calculator.set_calibration(image_entry['calibration']['pixels_per_inch'], 100)
                moa_value = temp_calculator.calculate_moa(all_shots)
            else:
                moa_value = moa_calculator.calculate_moa(all_shots)
        
        # Upload updated annotated image
        _, buffer = cv2.imencode('.jpg', annotated_image)
        annotated_image_data = buffer.tobytes()
        upload_to_storage(annotated_image_data, image_entry['annotated_filename'])
        
        # Convert to base64
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Update metadata
        updates = {
            'shot_count': len(all_shots),
            'moa_value': moa_value,
            'shots': all_shots.tolist() if len(all_shots) > 0 else [],
            'manual_shots': manual_shots,
            'last_updated': datetime.now().isoformat()
        }
        update_metadata(image_id, updates)
        
        return jsonify({
            'success': True,
            'id': image_id,
            'shot_count': len(all_shots),
            'moa_value': moa_value,
            'annotated_image': f"data:image/jpeg;base64,{img_base64}",
            'shots': all_shots.tolist() if len(all_shots) > 0 else [],
            'manual_shots': manual_shots
        }), 200, headers
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500, headers

def handle_calibrate(request, image_id, headers):
    """Calibrate the scale for an image using two reference points"""
    try:
        data = request.get_json()
        point1 = data.get('point1')
        point2 = data.get('point2')
        distance_inches = float(data.get('distance_inches', 1.0))
        
        if not point1 or not point2:
            return jsonify({'error': 'Two calibration points required'}), 400, headers
        
        # Calculate pixels per inch
        pixel_distance = ((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)**0.5
        if pixel_distance == 0:
            return jsonify({'error': 'Points cannot be the same'}), 400, headers
        
        pixels_per_inch = pixel_distance / distance_inches
        
        # Get metadata from Firestore
        db, bucket = get_firebase_services()
        doc_ref = db.collection('targets').document(image_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Image not found'}), 404, headers
        
        image_entry = doc.to_dict()
        
        # Update calibration data
        calibration_data = {
            'point1': point1,
            'point2': point2,
            'distance_inches': distance_inches,
            'pixels_per_inch': pixels_per_inch
        }
        
        # Recalculate MOA if shots exist
        new_moa_value = image_entry.get('moa_value')
        if image_entry.get('shots'):
            temp_calculator = MOACalculator()
            temp_calculator.set_calibration(pixels_per_inch, 100)
            shots_array = np.array(image_entry['shots'])
            if len(shots_array) > 0:
                new_moa_value = temp_calculator.calculate_moa(shots_array)
        
        # Regenerate annotated image with new calibration
        image_data = download_from_storage(image_entry['filename'])
        if image_data:
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            annotated_image = image.copy()
            if image_entry.get('shots'):
                shots_array = np.array(image_entry['shots'])
                if len(shots_array) > 0:
                    if shots_array.shape[1] == 2:
                        shots_array = np.column_stack([shots_array, np.full(len(shots_array), 10)])
                    
                    for shot in shots_array:
                        x, y, radius = int(shot[0]), int(shot[1]), int(shot[2])
                        cv2.circle(annotated_image, (x, y), radius, (0, 255, 0), 2)
                        cv2.circle(annotated_image, (x, y), 2, (0, 0, 255), -1)
            
            # Add reference scale with new calibration
            annotated_image = add_reference_scale(annotated_image, pixels_per_inch)
            
            # Upload updated annotated image
            _, buffer = cv2.imencode('.jpg', annotated_image)
            annotated_image_data = buffer.tobytes()
            upload_to_storage(annotated_image_data, image_entry['annotated_filename'])
        
        # Update metadata
        updates = {
            'calibration': calibration_data,
            'moa_value': new_moa_value
        }
        update_metadata(image_id, updates)
        
        return jsonify({
            'success': True,
            'pixels_per_inch': pixels_per_inch,
            'moa_value': new_moa_value
        }), 200, headers
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500, headers

def handle_delete(request, image_id, headers):
    """Delete a target and its associated files"""
    try:
        # Get metadata from Firestore
        db, bucket = get_firebase_services()
        doc_ref = db.collection('targets').document(image_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({'error': 'Image not found'}), 404, headers
        
        image_entry = doc.to_dict()
        
        # Delete files from storage
        delete_from_storage(image_entry['filename'])
        delete_from_storage(image_entry['annotated_filename'])
        
        # Delete metadata from Firestore
        delete_metadata(image_id)
        
        return jsonify({'success': True, 'message': 'Target deleted successfully'}), 200, headers
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500, headers

def handle_get_image(request, filename, headers):
    """Serve images from storage"""
    try:
        # For Firebase, we'll redirect to the public URL
        db, bucket = get_firebase_services()
        blob = bucket.blob(f"uploads/{filename}")
        if not blob.exists():
            return jsonify({'error': 'Image not found'}), 404, headers
        
        blob.make_public()
        return jsonify({'url': blob.public_url}), 200, headers
        
    except Exception as e:
        return jsonify({'error': str(e)}), 404, headers

def handle_health(request, headers):
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'photoMOA Firebase backend'}), 200, headers