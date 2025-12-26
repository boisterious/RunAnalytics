"""Terrain Analysis Module

Classifies running sessions by terrain profile and analyzes performance
across different elevation patterns.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


class TerrainClassifier:
    """Classify terrain profiles and analyze performance by elevation"""
    
    # Terrain profiles based on elevation gain per km
    TERRAIN_PROFILES = {
        'flat': {
            'name': 'Llano',
            'emoji': '➡️',
            'gain_per_km_min': 0,
            'gain_per_km_max': 10,
            'color': '#00FF7F'
        },
        'rolling': {
            'name': 'Ondulado',
            'emoji': '〰️',
            'gain_per_km_min': 10,
            'gain_per_km_max': 30,
            'color': '#00BFFF'
        },
        'hilly': {
            'name': 'Montañoso',
            'emoji': '⛰️',
            'gain_per_km_min': 30,
            'gain_per_km_max': 60,
            'color': '#FFD700'
        },
        'mountain': {
            'name': 'Alta Montaña',
            'emoji': '🏔️',
            'gain_per_km_min': 60,
            'gain_per_km_max': 999,
            'color': '#FF6B6B'
        }
    }
    
    def classify_terrain(self, run: Dict) -> str:
        """Classify a run by its terrain profile
        
        Args:
            run: Run data dictionary with metrics
            
        Returns:
            Terrain type ID ('flat', 'rolling', 'hilly', 'mountain')
        """
        metrics = run.get('metrics', {})
        distance_km = metrics.get('distance_km', 0)
        elevation_gain = metrics.get('elevation_gain', 0)
        
        if distance_km == 0:
            return 'flat'
        
        gain_per_km = elevation_gain / distance_km
        
        # Classify based on gain per km
        for terrain_id, profile in self.TERRAIN_PROFILES.items():
            if profile['gain_per_km_min'] <= gain_per_km < profile['gain_per_km_max']:
                return terrain_id
        
        return 'flat'
    
    def get_terrain_info(self, terrain_id: str) -> Dict:
        """Get display information for terrain type
        
        Args:
            terrain_id: Terrain type ID
            
        Returns:
            Dictionary with name, emoji, color
        """
        return self.TERRAIN_PROFILES.get(terrain_id, self.TERRAIN_PROFILES['flat'])


class TerrainAnalyzer:
    """Analyze performance across different terrain types"""
    
    def __init__(self, runs: List[Dict]):
        self.runs = runs
        self.classifier = TerrainClassifier()
    
    def analyze_terrain_distribution(self) -> Dict:
        """Analyze distribution of training across terrain types
        
        Returns:
            Dictionary with terrain distribution statistics
        """
        terrain_stats = {}
        total_km = 0
        
        for run in self.runs:
            terrain_type = run.get('terrain_type')
            if not terrain_type:
                terrain_type = self.classifier.classify_terrain(run)
                run['terrain_type'] = terrain_type
            
            terrain_info = self.classifier.get_terrain_info(terrain_type)
            
            if terrain_type not in terrain_stats:
                terrain_stats[terrain_type] = {
                    'name': terrain_info['name'],
                    'emoji': terrain_info['emoji'],
                    'color': terrain_info['color'],
                    'count': 0,
                    'total_km': 0,
                    'avg_pace': [],
                    'avg_gap': [],
                    'avg_hr': []
                }
            
            metrics = run['metrics']
            terrain_stats[terrain_type]['count'] += 1
            terrain_stats[terrain_type]['total_km'] += metrics.get('distance_km', 0)
            terrain_stats[terrain_type]['avg_pace'].append(metrics.get('pace_min_per_km', 0))
            terrain_stats[terrain_type]['avg_gap'].append(metrics.get('gap_pace_min_per_km', 0))
            
            if metrics.get('avg_heart_rate'):
                terrain_stats[terrain_type]['avg_hr'].append(metrics['avg_heart_rate'])
            
            total_km += metrics.get('distance_km', 0)
        
        # Calculate averages
        for terrain_type, stats in terrain_stats.items():
            if stats['avg_pace']:
                stats['avg_pace_value'] = np.mean(stats['avg_pace'])
            if stats['avg_gap']:
                stats['avg_gap_value'] = np.mean(stats['avg_gap'])
            if stats['avg_hr']:
                stats['avg_hr_value'] = np.mean(stats['avg_hr'])
            
            stats['km_percentage'] = (stats['total_km'] / total_km * 100) if total_km > 0 else 0
        
        return terrain_stats
    
    def analyze_gap_effectiveness(self) -> Dict:
        """Analyze GAP effectiveness across terrains
        
        Returns:
            Analysis of how well GAP normalizes effort across terrains
        """
        terrain_gap_analysis = {}
        
        for run in self.runs:
            terrain_type = run.get('terrain_type', self.classifier.classify_terrain(run))
            metrics = run['metrics']
            
            pace = metrics.get('pace_min_per_km', 0)
            gap = metrics.get('gap_pace_min_per_km', 0)
            
            if pace > 0 and gap > 0:
                # GAP adjustment = difference between pace and GAP
                gap_adjustment = pace - gap  # Positive means uphill slowed you down
                
                if terrain_type not in terrain_gap_analysis:
                    terrain_gap_analysis[terrain_type] = {
                        'gap_adjustments': [],
                        'pace_gap_diff': []
                    }
                
                terrain_gap_analysis[terrain_type]['gap_adjustments'].append(gap_adjustment)
                terrain_gap_analysis[terrain_type]['pace_gap_diff'].append(
                    (pace - gap) / pace * 100 if pace > 0 else 0
                )
        
        # Calculate averages
        result = {}
        for terrain_type, data in terrain_gap_analysis.items():
            if data['gap_adjustments']:
                result[terrain_type] = {
                    'avg_adjustment': np.mean(data['gap_adjustments']),
                    'avg_diff_pct': np.mean(data['pace_gap_diff']),
                    'name': self.classifier.get_terrain_info(terrain_type)['name']
                }
        
        return result
    
    def get_terrain_recommendations(self) -> List[str]:
        """Generate terrain-based training recommendations
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        terrain_dist = self.analyze_terrain_distribution()
        
        if not terrain_dist:
            return ["Añade más entrenamientos para análisis de terreno"]
        
        # Calculate percentages
        total_sessions = sum(stats['count'] for stats in terrain_dist.values())
        
        # Check for terrain imbalance
        flat_pct = terrain_dist.get('flat', {}).get('count', 0) / total_sessions * 100 if total_sessions > 0 else 0
        mountain_pct = (terrain_dist.get('hilly', {}).get('count', 0) + 
                       terrain_dist.get('mountain', {}).get('count', 0)) / total_sessions * 100 if total_sessions > 0 else 0
        
        if flat_pct > 80:
            recommendations.append(
                "⛰️ **Falta desnivel**: El 80%+ de tus entrenamientos son en llano. "
                "Añade al menos 1 sesión semanal con pendientes para desarrollar potencia."
            )
        
        if mountain_pct > 60:
            recommendations.append(
                "➡️ **Mucho desnivel**: Más del 60% de tus kms son en montaña. "
                "Incluye sesiones en llano para trabajar velocidad pura."
            )
        
        if flat_pct >= 20 and flat_pct <= 40 and mountain_pct >= 20 and mountain_pct <= 40:
            recommendations.append(
                "✅ **Balance perfecto**: Tienes una buena distribución entre llano y desnivel. "
                "Esto desarrolla capacidades completas."
            )
        
        # Analyze GAP effectiveness
        gap_analysis = self.analyze_gap_effectiveness()
        
        if 'mountain' in gap_analysis or 'hilly' in gap_analysis:
            mountain_data = gap_analysis.get('mountain') or gap_analysis.get('hilly')
            if mountain_data and mountain_data['avg_diff_pct'] > 15:
                recommendations.append(
                    f"🏔️ **Subidas impactan ritmo**: En terreno montañoso, tu ritmo se ralentiza ~{mountain_data['avg_diff_pct']:.0f}%. "
                    f"Trabaja fuerza específica en cuestas."
                )
        
        return recommendations
    
    def get_terrain_summary(self) -> Dict:
        """Get comprehensive terrain analysis summary
        
        Returns:
            Summary with distribution, GAP analysis, and recommendations
        """
        return {
            'distribution': self.analyze_terrain_distribution(),
            'gap_effectiveness': self.analyze_gap_effectiveness(),
            'recommendations': self.get_terrain_recommendations()
        }


def classify_all_runs(runs: List[Dict]) -> List[Dict]:
    """Classify terrain for all runs that don't have it
    
    Args:
        runs: List of run dictionaries
        
    Returns:
        Same list with terrain_type added to each run
    """
    classifier = TerrainClassifier()
    
    for run in runs:
        if 'terrain_type' not in run:
            run['terrain_type'] = classifier.classify_terrain(run)
            run['terrain_info'] = classifier.get_terrain_info(run['terrain_type'])
    
    return runs
