"""Session Deep Dive Module

Provides detailed analysis for individual sessions including splits,
interval detection, pacing strategy, and quality scoring.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


class SessionAnalyzer:
    """Deep dive analysis for individual sessions"""
    
    def __init__(self, run_data: Dict):
        """
        Args:
            run_data: Single run dictionary with 'data' DataFrame and 'metrics'
        """
        self.run = run_data
        self.df = run_data.get('data', pd.DataFrame())
        self.metrics = run_data.get('metrics', {})
    
    def calculate_km_splits(self) -> pd.DataFrame:
        """Calculate 1km splits automatically
        
        Returns:
            DataFrame with split data
        """
        if self.df.empty or 'distance' not in self.df.columns:
            return pd.DataFrame()
        
        total_distance = self.metrics.get('distance_km', 0)
        if total_distance < 1:
            return pd.DataFrame()
        
        splits = []
        num_km = int(total_distance)
        
        for km in range(num_km):
            # Find data points in this km
            start_dist = km * 1000  # meters
            end_dist = (km + 1) * 1000
            
            km_data = self.df[(self.df['distance'] >= start_dist) & 
                             (self.df['distance'] < end_dist)]
            
            if len(km_data) > 0:
                # Calculate split time
                if 'timestamp' in km_data.columns:
                    split_duration = (km_data['timestamp'].max() - 
                                    km_data['timestamp'].min()).total_seconds() / 60
                else:
                    split_duration = len(km_data) / 60  # Rough estimate
                
                split_info = {
                    'km': km + 1,
                    'time_min': split_duration,
                    'pace': split_duration if split_duration > 0 else 0,
                }
                
                # Add HR if available
                if 'heart_rate' in km_data.columns:
                    split_info['avg_hr'] = km_data['heart_rate'].mean()
                
                # Add elevation change
                if 'altitude' in km_data.columns:
                    elev_change = km_data['altitude'].max() - km_data['altitude'].min()
                    split_info['elevation_change'] = elev_change
                
                # Add cadence if available
                if 'cadence' in km_data.columns:
                    split_info['avg_cadence'] = km_data['cadence'].mean()
                
                splits.append(split_info)
        
        return pd.DataFrame(splits)
    
    def analyze_pacing_strategy(self) -> Dict:
        """Analyze pacing strategy (even/positive/negative split)
        
        Returns:
            Pacing analysis
        """
        splits_df = self.calculate_km_splits()
        
        if splits_df.empty or len(splits_df) < 2:
            return {'strategy': 'unknown', 'message': 'Distancia insuficiente'}
        
        # Compare first half vs second half
        mid_point = len(splits_df) // 2
        first_half_pace = splits_df.iloc[:mid_point]['pace'].mean()
        second_half_pace = splits_df.iloc[mid_point:]['pace'].mean()
        
        pace_diff_pct = ((second_half_pace - first_half_pace) / first_half_pace * 100)
        
        # Classify strategy
        if abs(pace_diff_pct) < 2:
            strategy = 'even'
            message = '✅ Even pace - estrategia ideal para la mayoría de carreras'
            quality = 'excellent'
        elif pace_diff_pct < -2:  # Second half faster
            strategy = 'negative'
            message = '🚀 Negative split - excelente, segunda mitad más rápida'
            quality = 'excellent'
        elif pace_diff_pct < 5:
            strategy = 'slight_positive'
            message = '⚡ Ligero positive split - normal en entrenamientos'
            quality = 'good'
        else:
            strategy = 'positive'
            message = '⚠️ Positive split marcado - salida demasiado rápida'
            quality = 'poor'
        
        # Pace variability
        pace_std = splits_df['pace'].std()
        pace_cv = (pace_std / splits_df['pace'].mean() * 100) if splits_df['pace'].mean() > 0 else 0
        
        return {
            'strategy': strategy,
            'message': message,
            'quality': quality,
            'first_half_pace': first_half_pace,
            'second_half_pace': second_half_pace,
            'pace_diff_pct': pace_diff_pct,
            'pace_variability': pace_cv
        }
    
    def detect_intervals(self) -> List[Dict]:
        """Detect intervals automatically based on pace/HR changes
        
        Returns:
            List of detected intervals
        """
        if self.df.empty or 'pace' not in self.df.columns:
            return []
        
        pace_data = self.df['pace'].dropna()
        if len(pace_data) < 10:
            return []
        
        # Calculate rolling statistics
        window = 10  # points
        rolling_mean = pace_data.rolling(window=window, center=True).mean()
        rolling_std = pace_data.rolling(window=window, center=True).std()
        
        # Detect significant pace changes (> 30 sec/km from baseline)
        baseline_pace = pace_data.median()
        threshold = 0.5  # 30 seconds per km
        
        intervals = []
        in_interval = False
        interval_start = None
        
        for idx, pace in pace_data.items():
            if pace < baseline_pace - threshold and not in_interval:
                # Start of fast interval
                in_interval = True
                interval_start = idx
            elif pace >= baseline_pace - threshold/2 and in_interval:
                # End of interval
                in_interval = False
                if interval_start is not None:
                    interval_data = pace_data.loc[interval_start:idx]
                    if len(interval_data) > 5:  # Minimum length
                        intervals.append({
                            'start_idx': interval_start,
                            'end_idx': idx,
                            'duration_points': len(interval_data),
                            'avg_pace': interval_data.mean(),
                            'type': 'fast'
                        })
        
        return intervals
    
    def calculate_session_quality_score(self) -> Dict:
        """Calculate overall session quality score (1-10)
        
        Based on:
        - Consistency of pace/HR
        - Absence of excessive drift
        - Biomechanical efficiency
        - Completion of intended effort
        
        Returns:
            Quality score and breakdown
        """
        score = 0
        max_score = 100
        breakdown = {}
        
        # 1. Pace consistency (30 points)
        pacing = self.analyze_pacing_strategy()
        if pacing.get('quality') == 'excellent':
            pace_points = 30
        elif pacing.get('quality') == 'good':
            pace_points = 20
        else:
            pace_points = 10
        
        score += pace_points
        breakdown['pacing'] = {'points': pace_points, 'max': 30}
        
        # 2. HR data quality (20 points)
        if 'heart_rate' in self.df.columns:
            hr_data = self.df['heart_rate'].dropna()
            if len(hr_data) > len(self.df) * 0.8:  # >80% coverage
                hr_points = 20
            elif len(hr_data) > 0:
                hr_points = 10
            else:
                hr_points = 0
        else:
            hr_points = 0
        
        score += hr_points
        breakdown['hr_data'] = {'points': hr_points, 'max': 20}
        
        # 3. Cadence consistency (20 points)
        if 'cadence' in self.df.columns:
            cadence_data = self.df['cadence'].dropna()
            if len(cadence_data) > 0:
                cadence_cv = cadence_data.std() / cadence_data.mean() * 100
                if cadence_cv < 5:  # Very consistent
                    cadence_points = 20
                elif cadence_cv < 10:
                    cadence_points = 15
                else:
                    cadence_points = 10
            else:
                cadence_points = 0
        else:
            cadence_points = 0
        
        score += cadence_points
        breakdown['cadence'] = {'points': cadence_points, 'max': 20}
        
        # 4. Data completeness (15 points)
        required_cols = ['distance', 'altitude', 'pace']
        present_cols = sum([col in self.df.columns for col in required_cols])
        completeness_points = int(present_cols / len(required_cols) * 15)
        
        score += completeness_points
        breakdown['completeness'] = {'points': completeness_points, 'max': 15}
        
        # 5. Distance achieved (15 points)
        target_distance = self.metrics.get('distance_km', 0)
        if target_distance >= 10:
            distance_points = 15
        elif target_distance >= 5:
            distance_points = 10
        else:
            distance_points = 5
        
        score += distance_points
        breakdown['distance'] = {'points': distance_points, 'max': 15}
        
        # Convert to 1-10 scale
        final_score = int(score / max_score * 10)
        
        # Quality message
        if final_score >= 9:
            message = "🏆 Sesión excelente - datos completos y ejecución perfecta"
        elif final_score >= 7:
            message = "✅ Buena sesión - bien ejecutada"
        elif final_score >= 5:
            message = "👍 Sesión aceptable - hay margen de mejora"
        else:
            message = "⚠️ Sesión mejorable - revisa ejecución y datos"
        
        return {
            'score': final_score,
            'score_100': score,
            'message': message,
            'breakdown': breakdown
        }
    
    def get_session_deep_dive(self) -> Dict:
        """Get complete deep dive analysis
        
        Returns:
            Comprehensive session analysis
        """
        return {
            'splits': self.calculate_km_splits(),
            'pacing': self.analyze_pacing_strategy(),
            'intervals': self.detect_intervals(),
            'quality': self.calculate_session_quality_score()
        }
