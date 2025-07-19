import numpy as np
from typing import List, Tuple
from scipy.spatial.distance import pdist

class MOACalculator:
    def __init__(self):
        # Default assumptions - these could be made configurable
        self.pixels_per_inch = 100  # Default assumption, could be calibrated
        self.target_distance_yards = 100  # Default shooting distance
        
    def calculate_moa(self, shot_positions: np.ndarray) -> float:
        """
        Calculate MOA (Minute of Angle) for a group of shots
        
        Args:
            shot_positions: Array of shot positions in pixels [[x1,y1], [x2,y2], ...]
            
        Returns:
            MOA value as float
        """
        if len(shot_positions) < 2:
            return 0.0
        
        # Calculate the extreme spread (maximum distance between any two shots)
        distances = pdist(shot_positions)
        max_distance_pixels = np.max(distances)
        
        # Convert pixels to inches
        max_distance_inches = max_distance_pixels / self.pixels_per_inch
        
        # Calculate MOA
        # MOA = (group_size_inches / distance_yards) * 95.5
        # The factor 95.5 converts from the ratio to MOA
        moa = (max_distance_inches / self.target_distance_yards) * 95.5
        
        return round(moa, 2)
    
    def calculate_center_to_center_moa(self, shot_positions: np.ndarray) -> float:
        """
        Calculate center-to-center MOA (distance from group center to furthest shot)
        
        Args:
            shot_positions: Array of shot positions in pixels
            
        Returns:
            Center-to-center MOA value
        """
        if len(shot_positions) < 2:
            return 0.0
        
        # Calculate group center
        center = np.mean(shot_positions, axis=0)
        
        # Calculate distances from center to each shot
        distances_from_center = np.sqrt(np.sum((shot_positions - center)**2, axis=1))
        
        # Get maximum distance from center
        max_distance_from_center = np.max(distances_from_center)
        
        # Convert to inches and then to MOA
        max_distance_inches = max_distance_from_center / self.pixels_per_inch
        moa = (max_distance_inches / self.target_distance_yards) * 95.5
        
        return round(moa, 2)
    
    def get_group_statistics(self, shot_positions: np.ndarray) -> dict:
        """
        Get comprehensive statistics for a shot group
        
        Args:
            shot_positions: Array of shot positions in pixels
            
        Returns:
            Dictionary with group statistics
        """
        if len(shot_positions) < 2:
            return {
                'shot_count': len(shot_positions),
                'extreme_spread_moa': 0.0,
                'center_to_center_moa': 0.0,
                'group_center': [0, 0],
                'group_size_inches': 0.0
            }
        
        # Calculate group center
        center = np.mean(shot_positions, axis=0)
        
        # Calculate extreme spread
        distances = pdist(shot_positions)
        max_distance_pixels = np.max(distances)
        extreme_spread_moa = self.calculate_moa(shot_positions)
        
        # Calculate center-to-center MOA
        center_to_center_moa = self.calculate_center_to_center_moa(shot_positions)
        
        # Convert group size to inches
        group_size_inches = max_distance_pixels / self.pixels_per_inch
        
        return {
            'shot_count': len(shot_positions),
            'extreme_spread_moa': extreme_spread_moa,
            'center_to_center_moa': center_to_center_moa,
            'group_center': center.tolist(),
            'group_size_inches': round(group_size_inches, 2)
        }
    
    def set_calibration(self, pixels_per_inch: float, target_distance_yards: int):
        """
        Set calibration parameters
        
        Args:
            pixels_per_inch: Number of pixels per inch in the image
            target_distance_yards: Distance to target in yards
        """
        self.pixels_per_inch = pixels_per_inch
        self.target_distance_yards = target_distance_yards
