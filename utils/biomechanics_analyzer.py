"""Biomechanics Analysis Module

Analyzes running biomechanics including cadence patterns, stride length,
and running economy to provide technique improvement suggestions.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


class BiomechanicsAnalyzer:
    """Analyze running biomechanics and technique"""
    
    # Optimal cadence range (steps per minute)
    OPTIMAL_CADENCE_MIN = 170
    OPTIMAL_CADENCE_MAX = 190
    OPTIMAL_CADENCE_TARGET = 180
    
    def __init__(self, runs: List[Dict]):
        self.runs = runs
    
    def analyze_cadence_patterns(self) -> Dict:
        """Analyze cadence patterns across different paces
        
        Returns:
            Analysis of cadence by pace zones
        """
        cadence_by_pace = {
            'easy': {'paces': [], 'cadences': [], 'range': (6.5, 999)},  # > 6:30/km
            'moderate': {'paces': [], 'cadences': [], 'range': (5.0, 6.5)},  # 5:00-6:30/km
            'tempo': {'paces': [], 'cadences': [], 'range': (4.0, 5.0)},  # 4:00-5:00/km
            'fast': {'paces': [], 'cadences': [], 'range': (0, 4.0)}  # < 4:00/km
        }
        
        for run in self.runs:
            metrics = run['metrics']
            pace = metrics.get('pace_min_per_km', 0)
            cadence = metrics.get('avg_cadence', 0)
            
            if pace > 0 and cadence > 0:
                # Classify into pace zone
                for zone_name, zone_data in cadence_by_pace.items():
                    min_pace, max_pace = zone_data['range']
                    if min_pace <= pace < max_pace:
                        zone_data['paces'].append(pace)
                        zone_data['cadences'].append(cadence)
                        break
        
        # Calculate statistics for each zone
        result = {}
        for zone_name, zone_data in cadence_by_pace.items():
            if zone_data['cadences']:
                result[zone_name] = {
                    'avg_cadence': np.mean(zone_data['cadences']),
                    'avg_pace': np.mean(zone_data['paces']),
                    'cadence_std': np.std(zone_data['cadences']),
                    'count': len(zone_data['cadences']),
                    'optimal': self.OPTIMAL_CADENCE_MIN <= np.mean(zone_data['cadences']) <= self.OPTIMAL_CADENCE_MAX
                }
        
        return result
    
    def analyze_stride_length(self) -> Dict:
        """Analyze stride length patterns
        
        Stride length (meters) = (speed_m/min) / (cadence_spm)
        
        Returns:
            Analysis of stride length by pace
        """
        stride_analysis = []
        
        for run in self.runs:
            metrics = run['metrics']
            pace = metrics.get('pace_min_per_km', 0)
            cadence = metrics.get('avg_cadence', 0)
            
            if pace > 0 and cadence > 0:
                # Convert pace to speed (m/min)
                speed_m_per_min = 1000 / pace
                
                # Calculate stride length
                stride_length = speed_m_per_min / cadence
                
                stride_analysis.append({
                    'pace': pace,
                    'cadence': cadence,
                    'stride_length': stride_length,
                    'speed': speed_m_per_min
                })
        
        if not stride_analysis:
            return {}
        
        df = pd.DataFrame(stride_analysis)
        
        return {
            'avg_stride_length': df['stride_length'].mean(),
            'stride_length_std': df['stride_length'].std(),
            'correlation_pace_stride': df['pace'].corr(df['stride_length']),
            'data': df
        }
    
    def analyze_running_economy(self) -> Dict:
        """Analyze running economy (cadence vs velocity relationship)
        
        Returns:
            Economics metrics and efficiency indicators
        """
        economy_data = []
        
        for run in self.runs:
            metrics = run['metrics']
            pace = metrics.get('pace_min_per_km', 0)
            cadence = metrics.get('avg_cadence', 0)
            hr = metrics.get('avg_heart_rate', 0)
            efficiency_index = metrics.get('efficiency_index', 0)
            
            if pace > 0 and cadence > 0:
                speed_km_h = 60 / pace  # Convert pace to km/h
                
                # Running economy score: higher is better
                # Combines cadence efficiency with cardiovascular efficiency
                economy_score = 0
                
                # Cadence component (optimal = 180 spm)
                cadence_diff = abs(cadence - self.OPTIMAL_CADENCE_TARGET)
                cadence_efficiency = max(0, 100 - (cadence_diff / 2))  # 0-100 scale
                
                economy_data.append({
                    'pace': pace,
                    'cadence': cadence,
                    'speed': speed_km_h,
                    'hr': hr,
                    'ei': efficiency_index,
                    'cadence_efficiency': cadence_efficiency
                })
        
        if not economy_data:
            return {}
        
        df = pd.DataFrame(economy_data)
        
        # Calculate overall economy score
        avg_cadence_eff = df['cadence_efficiency'].mean()
        
        return {
            'avg_cadence_efficiency': avg_cadence_eff,
            'cadence_consistency': 100 - df['cadence'].std(),  # Lower std = more consistent
            'speed_cadence_correlation': df['speed'].corr(df['cadence']) if len(df) > 1 else 0,
            'overall_economy_score': avg_cadence_eff
        }
    
    def get_biomechanics_recommendations(self) -> List[str]:
        """Generate biomechanics improvement recommendations
        
        Returns:
            List of actionable recommendations
        """
        recommendations = []
        
        # Analyze cadence patterns
        cadence_patterns = self.analyze_cadence_patterns()
        
        if cadence_patterns:
            # Check overall cadence across all zones
            all_cadences = []
            for zone_data in cadence_patterns.values():
                if zone_data.get('avg_cadence'):
                    all_cadences.append(zone_data['avg_cadence'])
            
            if all_cadences:
                avg_overall_cadence = np.mean(all_cadences)
                
                if avg_overall_cadence < self.OPTIMAL_CADENCE_MIN:
                    diff = self.OPTIMAL_CADENCE_TARGET - avg_overall_cadence
                    recommendations.append(
                        f"👟 **Cadencia baja**: Tu cadencia promedio es {avg_overall_cadence:.0f} spm. "
                        f"Objetivo: {self.OPTIMAL_CADENCE_TARGET} spm (+{diff:.0f} pasos/min). "
                        f"Beneficios: menos impacto, mejor economía."
                    )
                elif avg_overall_cadence > self.OPTIMAL_CADENCE_MAX:
                    recommendations.append(
                        f"⚡ **Cadencia alta**: {avg_overall_cadence:.0f} spm. "
                        f"Esto es avanzado pero puede ser ineficiente. Monitoriza fatiga muscular."
                    )
                else:
                    recommendations.append(
                        f"✅ **Cadencia óptima**: {avg_overall_cadence:.0f} spm está en el rango ideal "
                        f"({self.OPTIMAL_CADENCE_MIN}-{self.OPTIMAL_CADENCE_MAX} spm)."
                    )
                
                # Check cadence variation by pace
                for zone_name, zone_data in cadence_patterns.items():
                    if zone_data.get('avg_cadence') and zone_data['avg_cadence'] < 165:
                        zone_label = {
                            'easy': 'ritmo suave',
                            'moderate': 'ritmo moderado',
                            'tempo': 'tempo',
                            'fast': 'ritmo rápido'
                        }.get(zone_name, zone_name)
                        
                        recommendations.append(
                            f"📊 **{zone_label.title()}**: Cadencia {zone_data['avg_cadence']:.0f} spm. "
                            f"Practica con metrónomo a 175-180 spm en este ritmo."
                        )
        
        # Analyze stride length
        stride_analysis = self.analyze_stride_length()
        
        if stride_analysis and stride_analysis.get('avg_stride_length'):
            avg_stride = stride_analysis['avg_stride_length']
            
            # Typical stride length for efficient running: 1.0-1.3 meters at easy pace
            if avg_stride > 1.4:
                recommendations.append(
                    f"⚠️ **Overstriding detectado**: Zancada promedio {avg_stride:.2f}m es larga. "
                    f"Reduce longitud, aumenta cadencia para menor impacto articular."
                )
            elif avg_stride < 0.85:
                recommendations.append(
                    f"🏃 **Zancada corta**: {avg_stride:.2f}m. "
                    f"Si tu cadencia es baja, trabaja extensión de cadera para mejor impulso."
                )
        
        # Running economy
        economy = self.analyze_running_economy()
        
        if economy and economy.get('overall_economy_score'):
            score = economy['overall_economy_score']
            
            if score >= 85:
                recommendations.append(
                    f"💎 **Excelente economía**: Score {score:.0f}/100. "
                    f"Tu técnica es muy eficiente, mantén este patrón."
                )
            elif score < 70:
                recommendations.append(
                    f"🔧 **Mejora técnica**: Score economía {score:.0f}/100. "
                    f"Trabaja drills de técnica: skipping, talones al glúteo, elevación de rodillas."
                )
        
        if not recommendations:
            recommendations.append(
                "📊 Necesitas añadir más sesiones con datos de cadencia para análisis biomecánico."
            )
        
        return recommendations
    
    def get_biomechanics_summary(self) -> Dict:
        """Get comprehensive biomechanics analysis summary
        
        Returns:
            Complete biomechanics analysis
        """
        return {
            'cadence_patterns': self.analyze_cadence_patterns(),
            'stride_length': self.analyze_stride_length(),
            'running_economy': self.analyze_running_economy(),
            'recommendations': self.get_biomechanics_recommendations()
        }
