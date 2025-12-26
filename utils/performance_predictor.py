"""Performance Predictor Module

Predicts race times for different distances and compares with age/gender standards.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


class PerformancePredictor:
    """Predict race times and compare with standards"""
    
    # Riegel formula exponent (typical value for trained runners)
    RIEGEL_EXPONENT = 1.06
    
    # Age/gender standards (approximate times in minutes for each distance)
    # Based on recreational runner averages
    STANDARDS = {
        'male': {
            '20-29': {'5K': 25, '10K': 52, '21K': 115, '42K': 245},
            '30-39': {'5K': 26, '10K': 54, '21K': 120, '42K': 255},
            '40-49': {'5K': 28, '10K': 58, '21K': 128, '42K': 270},
            '50-59': {'5K': 30, '10K': 63, '21K': 138, '42K': 290},
            '60+': {'5K': 33, '10K': 69, '21K': 152, '42K': 320}
        },
        'female': {
            '20-29': {'5K': 29, '10K': 60, '21K': 132, '42K': 280},
            '30-39': {'5K': 30, '10K': 62, '21K': 137, '42K': 290},
            '40-49': {'5K': 32, '10K': 67, '21K': 147, '42K': 310},
            '50-59': {'5K': 35, '10K': 73, '21K': 160, '42K': 340},
            '60+': {'5K': 38, '10K': 80, '21K': 175, '42K': 370}
        }
    }
    
    def __init__(self, runs: List[Dict]):
        self.runs = runs
    
    def predict_race_time(self, base_distance_km: float, base_time_min: float, 
                         target_distance_km: float) -> float:
        """Predict race time using Riegel formula
        
        T2 = T1 * (D2/D1)^1.06
        
        Args:
            base_distance_km: Known distance in km
            base_time_min: Time for known distance in minutes
            target_distance_km: Target distance to predict
            
        Returns:
            Predicted time in minutes
        """
        predicted_time = base_time_min * ((target_distance_km / base_distance_km) ** self.RIEGEL_EXPONENT)
        return predicted_time
    
    def get_best_performances(self) -> Dict:
        """Get best performances at different distances
        
        Returns:
            Dictionary with best times per distance
        """
        from utils.metrics import PersonalRecords
        
        pr_detector = PersonalRecords(self.runs)
        pbs = pr_detector.detect_pbs()
        
        # Convert to our format
        best_performances = {}
        distance_map = {
            '1K': 1.0,
            '3K': 3.0,
            '5K': 5.0,
            '10K': 10.0,
            '15K': 15.0,
            '21K': 21.097,
            '42K': 42.195
        }
        
        for dist_label, pb_data in pbs.items():
            if dist_label in distance_map:
                best_performances[dist_label] = {
                    'distance_km': distance_map[dist_label],
                    'time_min': pb_data['duration'],
                    'pace': pb_data['pace'],
                    'date': pb_data['date']
                }
        
        return best_performances
    
    def predict_all_distances(self) -> Dict:
        """Predict times for all standard race distances
        
        Returns:
            Predictions for 5K, 10K, 21K, 42K
        """
        best_perfs = self.get_best_performances()
        
        if not best_perfs:
            return {}
        
        # Use best available performance as base
        # Prefer 10K or 5K as base for predictions
        base_perf = None
        for preferred_dist in ['10K', '5K', '15K', '21K']:
            if preferred_dist in best_perfs:
                base_perf = best_perfs[preferred_dist]
                break
        
        if not base_perf:
            # Use any available
            base_perf = list(best_perfs.values())[0]
        
        # Target distances
        targets = {
            '5K': 5.0,
            '10K': 10.0,
            '21K': 21.097,
            '42K': 42.195
        }
        
        predictions = {}
        for dist_label, dist_km in targets.items():
            predicted_time = self.predict_race_time(
                base_perf['distance_km'],
                base_perf['time_min'],
                dist_km
            )
            
            # Convert to pace
            pace = predicted_time / dist_km
            
            predictions[dist_label] = {
                'time_min': predicted_time,
                'time_str': self._format_time(predicted_time),
                'pace': pace,
                'pace_str': self._format_pace(pace)
            }
        
        return predictions
    
    def compare_with_standards(self, age: int, gender: str = 'male') -> Dict:
        """Compare current performance with age/gender standards
        
        Args:
            age: Runner's age
            gender: 'male' or 'female'
            
        Returns:
            Comparison with standards
        """
        # Determine age group
        if age < 30:
            age_group = '20-29'
        elif age < 40:
            age_group = '30-39'
        elif age < 50:
            age_group = '40-49'
        elif age < 60:
            age_group = '50-59'
        else:
            age_group = '60+'
        
        standards = self.STANDARDS.get(gender, self.STANDARDS['male']).get(age_group, {})
        
        # Get predictions
        predictions = self.predict_all_distances()
        
        comparisons = {}
        for dist, standard_time in standards.items():
            if dist in predictions:
                predicted_time = predictions[dist]['time_min']
                diff_pct = ((predicted_time - standard_time) / standard_time * 100)
                
                if diff_pct < -10:
                    level = 'excellent'
                    message = '¡Muy por encima del promedio!'
                elif diff_pct < 0:
                    level = 'good'
                    message = 'Por encima del promedio'
                elif diff_pct < 10:
                    level = 'average'
                    message = 'En el promedio'
                else:
                    level = 'below'
                    message = 'Potencial de mejora'
                
                comparisons[dist] = {
                    'your_time': predictions[dist]['time_str'],
                    'standard_time': self._format_time(standard_time),
                    'diff_pct': diff_pct,
                    'level': level,
                    'message': message
                }
        
        return comparisons
    
    def suggest_race_goals(self, age: int = 35, gender: str = 'male') -> List[str]:
        """Suggest realistic race goals
        
        Returns:
            List of goal suggestions
        """
        suggestions = []
        
        predictions = self.predict_all_distances()
        if not predictions:
            return ["Necesitas más datos para predicciones"]
        
        # Suggest improvement targets
        for dist, pred in predictions.items():
            time_min = pred['time_min']
            
            # 5% improvement goal
            target_5pct = time_min * 0.95
            target_10pct = time_min * 0.90
            
            suggestions.append(
                f"**{dist}**: Actual {pred['time_str']} → "
                f"Objetivo conservador: {self._format_time(target_5pct)} (-5%) | "
                f"Objetivo ambicioso: {self._format_time(target_10pct)} (-10%)"
            )
        
        return suggestions
    
    def _format_time(self, minutes: float) -> str:
        """Format time as HH:MM:SS"""
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        secs = int((minutes % 1) * 60)
        
        if hours > 0:
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"
    
    def _format_pace(self, pace_min_per_km: float) -> str:
        """Format pace as MM:SS/km"""
        mins = int(pace_min_per_km)
        secs = int((pace_min_per_km % 1) * 60)
        return f"{mins}:{secs:02d}/km"
    
    def get_performance_summary(self, age: int = 35, gender: str = 'male') -> Dict:
        """Get complete performance analysis
        
        Returns:
            Summary with predictions, comparisons, goals
        """
        return {
            'predictions': self.predict_all_distances(),
            'standards_comparison': self.compare_with_standards(age, gender),
            'goal_suggestions': self.suggest_race_goals(age, gender)
        }
