"""Running Metrics Calculation Engine"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from geopy.distance import geodesic


class RunningMetrics:
    """Calculate advanced running metrics from trackpoint data"""
    
    # Standard race distances in meters (with tolerance for matching)
    STANDARD_DISTANCES = {
        '1K': 1000,
        '3K': 3000,
        '5K': 5000,
        '10K': 10000,
        '15K': 15000,
        '21K': 21097.5,  # Half marathon
        '42K': 42195     # Marathon
    }
    
    DISTANCE_TOLERANCE = 0.02  # 2% tolerance for PB matching
    
    def __init__(self, trackpoints_df: pd.DataFrame):
        """
        Initialize with trackpoint data
        
        Args:
            trackpoints_df: DataFrame with columns: timestamp, lat, lon, altitude, heart_rate, cadence
        """
        self.df = trackpoints_df.copy()
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare and clean data for calculations"""
        # Ensure timestamp is datetime
        if 'timestamp' in self.df.columns:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            self.df = self.df.sort_values('timestamp').reset_index(drop=True)
            
        # Ensure cumulative distance column exists - use FAST vectorized Haversine
        if 'distance' not in self.df.columns and 'lat' in self.df.columns and 'lon' in self.df.columns:
            self.df['distance'] = self._calculate_cumulative_distance_fast()
    
    def _calculate_cumulative_distance_fast(self) -> np.ndarray:
        """Calculate cumulative distance using vectorized Haversine formula (FAST)"""
        lat = self.df['lat'].values
        lon = self.df['lon'].values
        
        # Handle NaN values
        valid_mask = ~(np.isnan(lat) | np.isnan(lon))
        
        if valid_mask.sum() < 2:
            return np.zeros(len(self.df))
        
        # Convert to radians
        lat_rad = np.radians(lat)
        lon_rad = np.radians(lon)
        
        # Calculate differences
        dlat = np.diff(lat_rad)
        dlon = np.diff(lon_rad)
        
        # Haversine formula (vectorized)
        a = np.sin(dlat / 2) ** 2 + np.cos(lat_rad[:-1]) * np.cos(lat_rad[1:]) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))  # Clip to avoid NaN from sqrt
        
        # Earth radius in meters
        R = 6371000
        segment_distances = R * c
        
        # Handle NaN in segment distances (from invalid lat/lon)
        segment_distances = np.nan_to_num(segment_distances, nan=0.0)
        
        # Cumulative sum
        cumulative = np.zeros(len(self.df))
        cumulative[1:] = np.cumsum(segment_distances)
        
        return cumulative
    
    def calculate_distance(self) -> float:
        """
        Calculate total distance using Haversine formula
        
        Returns:
            Total distance in meters
        """
        if 'lat' not in self.df.columns or 'lon' not in self.df.columns:
            # Fallback to distance column if available
            if 'distance' in self.df.columns:
                return self.df['distance'].max()
            return 0.0
        
        total_distance = 0.0
        
        for i in range(1, len(self.df)):
            if pd.notna(self.df.loc[i, 'lat']) and pd.notna(self.df.loc[i-1, 'lat']):
                point1 = (self.df.loc[i-1, 'lat'], self.df.loc[i-1, 'lon'])
                point2 = (self.df.loc[i, 'lat'], self.df.loc[i, 'lon'])
                
                # Calculate distance in meters
                distance = geodesic(point1, point2).meters
                total_distance += distance
        
        return total_distance
    
    def calculate_elevation_gain(self) -> float:
        """
        Calculate positive elevation gain (D+)
        
        Returns:
            Elevation gain in meters
        """
        if 'altitude' not in self.df.columns:
            return 0.0
        
        elevation_gain = 0.0
        
        for i in range(1, len(self.df)):
            if pd.notna(self.df.loc[i, 'altitude']) and pd.notna(self.df.loc[i-1, 'altitude']):
                diff = self.df.loc[i, 'altitude'] - self.df.loc[i-1, 'altitude']
                if diff > 0:
                    elevation_gain += diff
        
        return elevation_gain
    
    def calculate_duration(self) -> float:
        """
        Calculate total duration in minutes
        
        Returns:
            Duration in minutes
        """
        if 'timestamp' not in self.df.columns or len(self.df) < 2:
            return 0.0
        
        duration = (self.df['timestamp'].max() - self.df['timestamp'].min()).total_seconds() / 60
        return duration
    
    def calculate_pace(self, distance_meters: float, duration_minutes: float) -> float:
        """
        Calculate pace in min/km
        
        Args:
            distance_meters: Distance in meters
            duration_minutes: Duration in minutes
            
        Returns:
            Pace in min/km
        """
        if distance_meters == 0:
            return 0.0
        
        distance_km = distance_meters / 1000
        pace = duration_minutes / distance_km
        return pace
    
    def calculate_gap(self, distance_meters: float, elevation_gain: float) -> float:
        """
        Calculate Grade Adjusted Pace distance
        Formula: adjusted_distance = distance + (elevation_gain * 10)
        
        Args:
            distance_meters: Actual distance in meters
            elevation_gain: Positive elevation gain in meters
            
        Returns:
            Adjusted distance in meters
        """
        return distance_meters + (elevation_gain * 10)

    def calculate_fastest_segment(self, target_distance_meters: float) -> Optional[Dict]:
        """
        Calculate fastest segment for a given distance using sliding window
        
        Args:
            target_distance_meters: Target distance in meters
            
        Returns:
            Dictionary with duration (min) and pace (min/km) or None
        """
        if 'distance' not in self.df.columns or 'timestamp' not in self.df.columns:
            return None
            
        # Need cumulative distance
        if self.df['distance'].max() < target_distance_meters:
            return None
            
        # Use sliding window over the dataframe
        # This is an approximation: we look for the window where distance >= target
        # and minimize time.
        
        # Optimization: Resample or use efficient rolling
        # Since points are irregular, we can't use simple rolling.
        # We'll use a two-pointer approach for O(N)
        
        n = len(self.df)
        min_duration = float('inf')
        found = False
        
        left = 0
        current_dist = 0.0
        
        # Pre-calculate distances between points to avoid repeated geopy calls
        # Assuming 'distance' column is cumulative total distance
        distances = self.df['distance'].values
        timestamps = self.df['timestamp'].values
        
        for right in range(n):
            dist_diff = distances[right] - distances[left]
            
            while dist_diff >= target_distance_meters:
                # We found a valid segment
                found = True
                duration_sec = (timestamps[right] - timestamps[left]).astype('timedelta64[s]').astype(float)
                if duration_sec > 0:
                    min_duration = min(min_duration, duration_sec)
                
                # Try to shrink window from left
                left += 1
                if left > right:
                    break
                dist_diff = distances[right] - distances[left]
                
        if not found:
            return None
            
        duration_min = min_duration / 60
        pace = duration_min / (target_distance_meters / 1000)
        
        return {
            'duration_minutes': duration_min,
            'pace_min_per_km': pace
        }
    
    def calculate_efficiency_index(self, distance_meters: float, duration_minutes: float, 
                                   avg_heart_rate: Optional[float] = None) -> Optional[float]:
        """
        Calculate Efficiency Index (EI)
        Formula: (meters / minutes) / avg_heart_rate
        
        Args:
            distance_meters: Distance in meters
            duration_minutes: Duration in minutes
            avg_heart_rate: Average heart rate (optional, will calculate if not provided)
            
        Returns:
            Efficiency Index or None if heart rate not available
        """
        if avg_heart_rate is None:
            avg_heart_rate = self.get_average_heart_rate()
        
        if avg_heart_rate is None or avg_heart_rate == 0 or duration_minutes == 0:
            return None
        
        speed = distance_meters / duration_minutes
        ei = speed / avg_heart_rate
        return ei
    
    def get_average_heart_rate(self) -> Optional[float]:
        """Get average heart rate from trackpoints"""
        if 'heart_rate' not in self.df.columns:
            return None
        
        hr_data = self.df['heart_rate'].dropna()
        if len(hr_data) == 0:
            return None
        
        return hr_data.mean()
    
    def get_average_cadence(self) -> Optional[float]:
        """Get average cadence from trackpoints"""
        if 'cadence' not in self.df.columns:
            return None
        
        cadence_data = self.df['cadence'].dropna()
        if len(cadence_data) == 0:
            return None
        
        return cadence_data.mean()
    
    def get_max_heart_rate(self) -> Optional[float]:
        """Get maximum heart rate"""
        if 'heart_rate' not in self.df.columns:
            return None
        
        hr_data = self.df['heart_rate'].dropna()
        if len(hr_data) == 0:
            return None
        
        return hr_data.max()
    
    def calculate_all_metrics(self) -> Dict:
        """
        Calculate all metrics for a run
        
        Returns:
            Dictionary with all calculated metrics
        """
        distance = self.calculate_distance()
        duration = self.calculate_duration()
        elevation_gain = self.calculate_elevation_gain()
        avg_hr = self.get_average_heart_rate()
        avg_cadence = self.get_average_cadence()
        max_hr = self.get_max_heart_rate()
        
        pace = self.calculate_pace(distance, duration)
        gap_distance = self.calculate_gap(distance, elevation_gain)
        gap_pace = self.calculate_pace(gap_distance, duration)
        
        ei = self.calculate_efficiency_index(distance, duration, avg_hr)
        gap_ei = self.calculate_efficiency_index(gap_distance, duration, avg_hr)
        
        # Calculate best efforts for standard distances
        best_efforts = {}
        for name, dist_meters in self.STANDARD_DISTANCES.items():
            # Only calculate if run is long enough
            if distance >= dist_meters:
                effort = self.calculate_fastest_segment(dist_meters)
                if effort:
                    best_efforts[name] = effort
        
        return {
            'distance_km': distance / 1000,
            'distance_meters': distance,
            'duration_minutes': duration,
            'elevation_gain': elevation_gain,
            'pace_min_per_km': pace,
            'gap_distance_meters': gap_distance,
            'gap_pace_min_per_km': gap_pace,
            'avg_heart_rate': avg_hr,
            'max_heart_rate': max_hr,
            'avg_cadence': avg_cadence,
            'efficiency_index': ei,
            'gap_efficiency_index': gap_ei,
            'best_efforts': best_efforts
        }


class PersonalRecords:
    """Detect and manage personal records across multiple runs"""
    
    def __init__(self, runs: List[Dict]):
        """
        Initialize with list of runs
        
        Args:
            runs: List of run dictionaries with 'metrics' key
        """
        self.runs = runs
    
    def detect_pbs(self) -> Dict[str, Dict]:
        """
        Detect personal bests at standard distances
        
        Returns:
            Dictionary mapping distance names to best run info
        """
        pbs = {}
        
        for distance_name, distance_meters in RunningMetrics.STANDARD_DISTANCES.items():
            best_run = self._find_best_at_distance(distance_meters)
            if best_run:
                pbs[distance_name] = best_run
        
        return pbs
    
    def _find_best_at_distance(self, target_distance: float) -> Optional[Dict]:
        """
        Find the best (fastest) run at a given distance
        
        Args:
            target_distance: Target distance in meters
            
        Returns:
            Dictionary with best run info or None
        """
        # Find distance name
        dist_name = None
        for name, meters in RunningMetrics.STANDARD_DISTANCES.items():
            if meters == target_distance:
                dist_name = name
                break
        
        if not dist_name:
            return None
            
        valid_runs = []
        
        for run in self.runs:
            metrics = run.get('metrics', {})
            best_efforts = metrics.get('best_efforts', {})
            
            # Check if this run has a best effort for this distance
            if dist_name in best_efforts:
                effort = best_efforts[dist_name]
                valid_runs.append({
                    'run': run,
                    'pace': effort['pace_min_per_km'],
                    'duration': effort['duration_minutes'],
                    'date': run.get('start_time')
                })
            
            # Fallback for old data: Check total distance match
            # This handles cases where best_efforts wasn't calculated yet
            elif 'distance_meters' in metrics:
                distance = metrics['distance_meters']
                tolerance = target_distance * RunningMetrics.DISTANCE_TOLERANCE
                if (target_distance - tolerance) <= distance <= (target_distance + tolerance):
                     valid_runs.append({
                        'run': run,
                        'pace': metrics.get('pace_min_per_km', float('inf')),
                        'duration': metrics.get('duration_minutes', 0),
                        'date': run.get('start_time')
                    })
        
        if not valid_runs:
            return None
        
        # Find run with best (lowest) pace
        best = min(valid_runs, key=lambda x: x['pace'])
        
        return {
            'filename': best['run'].get('filename', 'Unknown'),
            'date': best['date'],
            'pace': best['pace'],
            'duration': best['duration'],
            'distance': target_distance / 1000 # Use target distance for display
        }
