import cv2
import numpy as np
from typing import Tuple, List

class ShotDetector:
    def __init__(self):
        # Create blob detector parameters for dark blobs (light backgrounds)
        self.blob_params_dark = cv2.SimpleBlobDetector_Params()
        self.blob_params_dark.filterByColor = True
        self.blob_params_dark.blobColor = 0  # Dark blobs
        self.blob_params_dark.filterByArea = True
        self.blob_params_dark.minArea = 100
        self.blob_params_dark.maxArea = 5000
        self.blob_params_dark.filterByCircularity = True
        self.blob_params_dark.minCircularity = 0.1
        self.blob_params_dark.filterByConvexity = True
        self.blob_params_dark.minConvexity = 0.1
        self.blob_params_dark.filterByInertia = True
        self.blob_params_dark.minInertiaRatio = 0.1
        
        # Create blob detector parameters for light blobs (dark backgrounds)
        self.blob_params_light = cv2.SimpleBlobDetector_Params()
        self.blob_params_light.filterByColor = True
        self.blob_params_light.blobColor = 255  # Light blobs
        self.blob_params_light.filterByArea = True
        self.blob_params_light.minArea = 100
        self.blob_params_light.maxArea = 5000
        self.blob_params_light.filterByCircularity = True
        self.blob_params_light.minCircularity = 0.1
        self.blob_params_light.filterByConvexity = True
        self.blob_params_light.minConvexity = 0.1
        self.blob_params_light.filterByInertia = True
        self.blob_params_light.minInertiaRatio = 0.1
        
        # Create detectors
        self.blob_detector_dark = cv2.SimpleBlobDetector_create(self.blob_params_dark)
        self.blob_detector_light = cv2.SimpleBlobDetector_create(self.blob_params_light)
        
        # Other parameters
        self.min_distance_between_shots = 50  # Minimum distance between shots
        
    def detect_shots(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect shot holes in a target image using multiple detection methods
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Tuple of (shot_positions, annotated_image)
        """
        # Create a copy for annotation
        annotated_image = image.copy()
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Get all candidate shots from different methods
        all_shots = []
        
        # Method 1: Blob detection (best for circular dark spots)
        blob_shots = self._detect_shots_blob(gray)
        all_shots.extend(blob_shots)
        
        # Method 2: Contour-based detection with improved filtering
        contour_shots = self._detect_shots_contour(gray)
        all_shots.extend(contour_shots)
        
        # Method 3: Hough Circle detection
        hough_shots = self._detect_shots_hough(gray)
        all_shots.extend(hough_shots)
        
        # Method 4: Template matching for typical bullet holes
        template_shots = self._detect_shots_template(gray)
        all_shots.extend(template_shots)
        
        # Filter and validate all candidates
        shot_positions = self._validate_and_filter_shots(gray, all_shots)
        
        # Draw annotations
        for i, (x, y) in enumerate(shot_positions):
            # Draw circle around detected shot
            cv2.circle(annotated_image, (x, y), 15, (0, 255, 0), 3)
            # Draw center point
            cv2.circle(annotated_image, (x, y), 3, (0, 0, 255), -1)
            # Draw shot number
            cv2.putText(annotated_image, str(i+1), (x-10, y-20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        return np.array(shot_positions), annotated_image
    
    def _filter_close_shots(self, shot_positions: List[List[int]]) -> List[List[int]]:
        """
        Filter out shots that are too close to each other, keeping the first one
        """
        if len(shot_positions) < 2:
            return shot_positions
        
        filtered_shots = []
        for shot in shot_positions:
            is_too_close = False
            for existing_shot in filtered_shots:
                distance = np.sqrt((shot[0] - existing_shot[0])**2 + (shot[1] - existing_shot[1])**2)
                if distance < self.min_distance_between_shots:
                    is_too_close = True
                    break
            
            if not is_too_close:
                filtered_shots.append(shot)
        
        return filtered_shots
    
    def _detect_shots_hough(self, gray: np.ndarray) -> List[List[int]]:
        """
        Alternative shot detection using Hough Circle Transform with less sensitivity
        """
        shots = []
        
        # Apply more aggressive blur for Hough detection
        blurred = cv2.GaussianBlur(gray, (9, 9), 0)
        
        # Apply Hough Circle Transform with stricter parameters
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,  # Increased minimum distance between circles
            param1=60,   # Increased edge threshold
            param2=40,   # Increased accumulator threshold
            minRadius=8, # Increased minimum radius
            maxRadius=40 # Decreased maximum radius
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                # More restrictive filtering based on radius
                if 8 <= r <= 40:
                    shots.append([x, y])
        
        return shots
    
    def _is_likely_shot_hole(self, gray: np.ndarray, cx: int, cy: int, contour) -> bool:
        """
        Additional validation to check if a detected region is likely a shot hole
        based on intensity and shape characteristics
        """
        # Create a mask for the contour
        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.fillPoly(mask, [contour], 255)
        
        # Get the mean intensity inside the contour
        mean_intensity = cv2.mean(gray, mask=mask)[0]
        
        # Get the mean intensity of the surrounding area
        # Create a larger mask around the contour
        kernel = np.ones((20, 20), np.uint8)
        dilated_mask = cv2.dilate(mask, kernel, iterations=1)
        surrounding_mask = cv2.subtract(dilated_mask, mask)
        
        # Ensure we don't go outside image boundaries
        h, w = gray.shape
        if cx - 30 >= 0 and cx + 30 < w and cy - 30 >= 0 and cy + 30 < h:
            surrounding_intensity = cv2.mean(gray, mask=surrounding_mask)[0]
            
            # Shot holes should be significantly darker than surrounding area
            intensity_ratio = mean_intensity / surrounding_intensity if surrounding_intensity > 0 else 1
            
            # Shot hole should be at least 20% darker than surrounding area
            if intensity_ratio > 0.8:
                return False
        
        # Additional check: shot holes should have relatively low absolute intensity
        # (they should be dark regions, not light ones)
        if mean_intensity > 180:  # Too bright to be a shot hole
            return False
        
        return True
    
    def _detect_shots_blob(self, gray: np.ndarray) -> List[List[int]]:
        """
        Detect shots using blob detection for both light and dark backgrounds with enhanced preprocessing
        """
        shots = []
        
        # Enhance contrast for better detection
        enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        
        # Detect dark blobs (for light backgrounds)
        dark_keypoints = self.blob_detector_dark.detect(enhanced)
        shots.extend([[int(kp.pt[0]), int(kp.pt[1])] for kp in dark_keypoints])
        
        # Also try with inverted image for better light background detection
        inverted = cv2.bitwise_not(gray)
        dark_keypoints_inv = self.blob_detector_dark.detect(inverted)
        shots.extend([[int(kp.pt[0]), int(kp.pt[1])] for kp in dark_keypoints_inv])
        
        # Detect light blobs (for dark backgrounds)
        light_keypoints = self.blob_detector_light.detect(enhanced)
        shots.extend([[int(kp.pt[0]), int(kp.pt[1])] for kp in light_keypoints])
        
        return shots
    
    def _detect_shots_contour(self, gray: np.ndarray) -> List[List[int]]:
        """
        Detect shots using contour analysis with improved filtering
        """
        shots = []
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Use adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Apply morphological operations
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Filter by area
            area = cv2.contourArea(contour)
            if area < 100 or area > 5000:
                continue
            
            # Filter by circularity
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < 0.3:  # More lenient for contours
                continue
            
            # Get center
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                shots.append([cx, cy])
        
        return shots
    
    def _detect_shots_template(self, gray: np.ndarray) -> List[List[int]]:
        """
        Detect shots using template matching for both light and dark holes
        """
        shots = []
        template_size = 20
        
        # Template 1: Dark circle on white background (for light backgrounds)
        template_dark = np.ones((template_size, template_size), dtype=np.uint8) * 255
        cv2.circle(template_dark, (template_size//2, template_size//2), template_size//4, 0, -1)
        
        # Template 2: Light circle on dark background (for dark backgrounds)
        template_light = np.zeros((template_size, template_size), dtype=np.uint8)
        cv2.circle(template_light, (template_size//2, template_size//2), template_size//4, 255, -1)
        
        # Match dark template
        result_dark = cv2.matchTemplate(gray, template_dark, cv2.TM_CCOEFF_NORMED)
        locations_dark = np.where(result_dark >= 0.5)
        
        for pt in zip(*locations_dark[::-1]):
            x = pt[0] + template_size // 2
            y = pt[1] + template_size // 2
            shots.append([x, y])
        
        # Match light template
        result_light = cv2.matchTemplate(gray, template_light, cv2.TM_CCOEFF_NORMED)
        locations_light = np.where(result_light >= 0.5)
        
        for pt in zip(*locations_light[::-1]):
            x = pt[0] + template_size // 2
            y = pt[1] + template_size // 2
            shots.append([x, y])
        
        return shots
    
    def _validate_and_filter_shots(self, gray: np.ndarray, shot_candidates: List[List[int]]) -> List[List[int]]:
        """
        Validate and filter shot candidates - look for both light and dark holes
        """
        if not shot_candidates:
            return []
        
        validated_shots = []
        
        for shot in shot_candidates:
            x, y = shot
            
            # Check if shot is within image bounds
            h, w = gray.shape
            if x < 20 or x >= w - 20 or y < 20 or y >= h - 20:
                continue
            
            # Get region and surrounding area
            region = gray[y-10:y+10, x-10:x+10]
            surrounding = gray[y-20:y+20, x-20:x+20]
            
            if region.size == 0 or surrounding.size == 0:
                continue
            
            region_mean = np.mean(region)
            surrounding_mean = np.mean(surrounding)
            
            if surrounding_mean == 0:
                continue
            
            # Calculate contrast ratio
            contrast_ratio = region_mean / surrounding_mean
            
            # Check for either type of hole:
            # 1. Dark hole on light background (ratio < 0.7)
            # 2. Light hole on dark background (ratio > 1.3)
            is_dark_hole = contrast_ratio < 0.7 and region_mean < 150
            is_light_hole = contrast_ratio > 1.3 and region_mean > 100
            
            # Accept if it's either type of hole with good contrast
            if is_dark_hole or is_light_hole:
                validated_shots.append([x, y])
        
        # Remove duplicates and shots too close together
        filtered_shots = self._filter_close_shots(validated_shots)
        
        return filtered_shots
