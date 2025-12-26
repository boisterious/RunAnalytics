"""Training Intelligence Engine

Automatic session classification, HR zones analysis, and training load calculation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class HRZones:
    """Heart Rate Zones analyzer and calculator"""
    
    # Zone definitions as % of max HR
    ZONE_DEFINITIONS = {
        'Z1': {'min': 50, 'max': 60, 'name': 'Recuperación', 'color': '#00FF7F'},
        'Z2': {'min': 60, 'max': 70, 'name': 'Base Aeróbica', 'color': '#00BFFF'},
        'Z3': {'min': 70, 'max': 80, 'name': 'Tempo', 'color': '#FFD700'},
        'Z4': {'min': 80, 'max': 90, 'name': 'Umbral', 'color': '#FFA500'},
        'Z5': {'min': 90, 'max': 100, 'name': 'VO2max', 'color': '#FF4444'}
    }
    
    def __init__(self, age: Optional[int] = None, max_hr_override: Optional[int] = None):
        """
        Initialize HR Zones calculator
        
        Args:
            age: Runner's age (optional, for estimation)
            max_hr_override: Manual max HR if known (overrides age estimation)
        """
        self.age = age
        self.max_hr_override = max_hr_override
        self.max_hr = None
    
    def estimate_max_hr(self, observed_max: Optional[float] = None) -> int:
        """Estimate maximum heart rate
        
        Args:
            observed_max: Maximum HR observed in data
            
        Returns:
            Estimated max HR
        """
        if self.max_hr_override:
            self.max_hr = self.max_hr_override
        elif observed_max and observed_max > 150:  # Sanity check
            # Use observed max + 5 bpm buffer
            self.max_hr = int(observed_max + 5)
        elif self.age:
            # Traditional formula: 220 - age
            self.max_hr = 220 - self.age
        else:
            # Default to observed or 185 as fallback
            self.max_hr = int(observed_max) if observed_max else 185
        
        return self.max_hr
    
    def calculate_zones(self, max_hr: Optional[int] = None) -> Dict[str, Dict]:
        """Calculate HR zones based on max HR
        
        Args:
            max_hr: Maximum heart rate (uses stored if not provided)
            
        Returns:
            Dictionary with zone boundaries
        """
        if max_hr:
            self.max_hr = max_hr
        elif not self.max_hr:
            raise ValueError("Max HR not set. Call estimate_max_hr() first.")
        
        zones = {}
        for zone_id, zone_def in self.ZONE_DEFINITIONS.items():
            zones[zone_id] = {
                'name': zone_def['name'],
                'min_hr': int(self.max_hr * zone_def['min'] / 100),
                'max_hr': int(self.max_hr * zone_def['max'] / 100),
                'min_pct': zone_def['min'],
                'max_pct': zone_def['max'],
                'color': zone_def['color']
            }
        
        return zones
    
    def classify_hr(self, hr_value: float, zones: Dict = None) -> str:
        """Classify a single HR value into a zone
        
        Args:
            hr_value: Heart rate value
            zones: Pre-calculated zones (optional)
            
        Returns:
            Zone ID (Z1-Z5)
        """
        if zones is None:
            zones = self.calculate_zones()
        
        for zone_id, zone_info in zones.items():
            if zone_info['min_hr'] <= hr_value <= zone_info['max_hr']:
                return zone_id
        
        # Edge cases
        if hr_value < zones['Z1']['min_hr']:
            return 'Z1'
        return 'Z5'
    
    def analyze_distribution(self, hr_data: pd.Series) -> Dict:
        """Analyze time spent in each HR zone
        
        Args:
            hr_data: Series of heart rate values
            
        Returns:
            Dictionary with time/percentage in each zone
        """
        if hr_data.empty or hr_data.isna().all():
            return {}
        
        # Estimate max HR from data
        observed_max = hr_data.max()
        self.estimate_max_hr(observed_max)
        zones = self.calculate_zones()
        
        # Classify each HR value
        total_points = len(hr_data.dropna())
        distribution = {}
        
        for zone_id in self.ZONE_DEFINITIONS.keys():
            zone_info = zones[zone_id]
            count = ((hr_data >= zone_info['min_hr']) & 
                    (hr_data <= zone_info['max_hr'])).sum()
            
            distribution[zone_id] = {
                'name': zone_info['name'],
                'count': count,
                'percentage': (count / total_points * 100) if total_points > 0 else 0,
                'color': zone_info['color']
            }
        
        return distribution


class SessionClassifier:
    """Classify running sessions into training types"""
    
    SESSION_TYPES = {
        'recovery': {'name': 'Recuperación', 'emoji': '🟢', 'color': '#00FF7F'},
        'easy': {'name': 'Rodaje Suave', 'emoji': '🔵', 'color': '#00BFFF'},
        'tempo': {'name': 'Tempo Run', 'emoji': '🟡', 'color': '#FFD700'},
        'threshold': {'name': 'Umbral', 'emoji': '🟠', 'color': '#FFA500'},
        'intervals': {'name': 'Intervalos', 'emoji': '🔴', 'color': '#FF4444'},
        'long_run': {'name': 'Tirada Larga', 'emoji': '🏃', 'color': '#9370DB'},
        'fartlek': {'name': 'Fartlek', 'emoji': '⚡', 'color': '#FF69B4'},
        'race': {'name': 'Carrera', 'emoji': '🏆', 'color': '#FFD700'}
    }
    
    def __init__(self):
        self.hr_zones = HRZones()
    
    def classify(self, run_data: Dict) -> str:
        """Classify a running session
        
        Args:
            run_data: Dictionary with run metrics and data
            
        Returns:
            Session type ID
        """
        metrics = run_data.get('metrics', {})
        df = run_data.get('data', pd.DataFrame())
        
        distance_km = metrics.get('distance_km', 0)
        duration_min = metrics.get('duration_minutes', 0)
        pace = metrics.get('pace_min_per_km', 0)
        
        # Analyze pace variability if data available
        pace_variability = 0
        if 'pace' in df.columns and not df['pace'].empty:
            pace_std = df['pace'].std()
            pace_mean = df['pace'].mean()
            pace_variability = (pace_std / pace_mean) if pace_mean > 0 else 0
        
        # Analyze HR distribution if available
        hr_distribution = {}
        dominant_zone = None
        if 'heart_rate' in df.columns and not df['heart_rate'].dropna().empty:
            hr_distribution = self.hr_zones.analyze_distribution(df['heart_rate'])
            # Find dominant zone
            if hr_distribution:
                dominant_zone = max(hr_distribution.items(), 
                                  key=lambda x: x[1]['percentage'])[0]
        
        # Classification logic
        
        # Long run: > 90 min or > 15 km
        if duration_min > 90 or distance_km > 15:
            return 'long_run'
        
        # Race: High pace variability and high HR zones
        if pace_variability > 0.15 and dominant_zone in ['Z4', 'Z5']:
            return 'race'
        
        # Intervals: Very high pace variability
        if pace_variability > 0.20:
            return 'intervals'
        
        # Fartlek: Moderate-high pace variability
        if pace_variability > 0.12:
            return 'fartlek'
        
        # Use HR zones if available
        if dominant_zone:
            if dominant_zone == 'Z1':
                return 'recovery'
            elif dominant_zone == 'Z2':
                return 'easy'
            elif dominant_zone == 'Z3':
                return 'tempo'
            elif dominant_zone in ['Z4', 'Z5']:
                return 'threshold'
        
        # Fallback to duration-based
        if duration_min < 30:
            return 'recovery'
        elif duration_min > 60:
            return 'easy'
        
        return 'easy'  # Default
    
    def get_session_info(self, session_type: str) -> Dict:
        """Get display info for session type
        
        Args:
            session_type: Session type ID
            
        Returns:
            Dictionary with name, emoji, color
        """
        return self.SESSION_TYPES.get(session_type, 
                                     {'name': 'Desconocido', 'emoji': '❓', 'color': '#808080'})


class TrainingLoadCalculator:
    """Calculate training load metrics (TRIMP, TSS)"""
    
    def calculate_trimp(self, duration_minutes: float, avg_hr: float, 
                       max_hr: int, gender: str = 'male') -> float:
        """Calculate TRIMP (TRaining IMPulse)
        
        Args:
            duration_minutes: Duration in minutes
            avg_hr: Average heart rate
            max_hr: Maximum heart rate
            gender: 'male' or 'female'
            
        Returns:
            TRIMP score
        """
        if not avg_hr or avg_hr == 0 or not max_hr or max_hr == 0:
            return 0
        
        try:
            # Calculate HR reserve ratio
            hr_ratio = (avg_hr / max_hr)
            
            # Gender-specific multiplier
            if gender == 'male':
                multiplier = 0.64 * np.exp(1.92 * hr_ratio)
            else:  # female
                multiplier = 0.86 * np.exp(1.67 * hr_ratio)
            
            trimp = duration_minutes * hr_ratio * multiplier
            return trimp
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error calculating TRIMP: {e}")
            return 0
    
    def calculate_tss_estimate(self, duration_minutes: float, 
                               intensity_factor: float) -> float:
        """Estimate TSS (Training Stress Score) for running
        
        Args:
            duration_minutes: Duration in minutes
            intensity_factor: Normalized intensity (0-1)
            
        Returns:
            Estimated TSS
        """
        # TSS formula: (duration_hours × IF² × 100)
        duration_hours = duration_minutes / 60
        tss = duration_hours * (intensity_factor ** 2) * 100
        
        return tss
    
    def calculate_acute_chronic_ratio(self, recent_loads: List[float], 
                                     all_loads: List[float]) -> float:
        """Calculate acute:chronic load ratio
        
        Args:
            recent_loads: Training load from last 7 days
            all_loads: Training load from last 42 days (6 weeks)
            
        Returns:
            Ratio (typically 0.8-1.5 is safe)
        """
        if not recent_loads or not all_loads:
            return 0
        
        acute_load = np.mean(recent_loads) if recent_loads else 0
        chronic_load = np.mean(all_loads) if all_loads else 0
        
        if chronic_load == 0:
            return 0
        
        ratio = acute_load / chronic_load
        
        return ratio


def calculate_session_load(run_data: Dict, max_hr: int = 185) -> Dict:
    """Calculate training load for a single session
    
    Args:
        run_data: Run data dictionary with metrics
        max_hr: Maximum heart rate
        
    Returns:
        Dictionary with load metrics
    """
    metrics = run_data.get('metrics', {})
    
    duration = metrics.get('duration_minutes', 0)
    avg_hr = metrics.get('avg_heart_rate', 0)
    distance_km = metrics.get('distance_km', 0)
    
    calculator = TrainingLoadCalculator()
    
    # Calculate TRIMP
    trimp = calculator.calculate_trimp(duration, avg_hr, max_hr)
    
    # Estimate intensity factor from HR
    intensity_factor = (avg_hr / max_hr) if avg_hr and max_hr else 0.7
    
    # Estimate TSS
    tss = calculator.calculate_tss_estimate(duration, intensity_factor)
    
    return {
        'trimp': trimp,
        'tss': tss,
        'duration': duration,
        'distance': distance_km,
        'intensity_factor': intensity_factor
    }
