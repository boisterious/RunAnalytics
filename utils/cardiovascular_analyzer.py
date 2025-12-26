"""Cardiovascular Analysis Module

Advanced cardiovascular metrics including cardiac drift, HR-pace coupling,
and aerobic decoupling analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


class CardiovascularAnalyzer:
    """Analyze cardiovascular metrics and efficiency"""
    
    def __init__(self, runs: List[Dict]):
        self.runs = runs
    
    def analyze_cardiac_drift(self, run: Dict) -> Dict:
        """Analyze cardiac drift within a single session
        
        Cardiac drift = increase in HR over time at steady effort
        
        Args:
            run: Single run data
            
        Returns:
            Drift analysis metrics
        """
        df = run.get('data')
        if df is None or 'heart_rate' not in df.columns:
            return {'has_data': False}
        
        hr_data = df['heart_rate'].dropna()
        if len(hr_data) < 20:  # Need enough data points
            return {'has_data': False}
        
        # Split into first and second half
        mid_point = len(hr_data) // 2
        first_half_hr = hr_data.iloc[:mid_point].mean()
        second_half_hr = hr_data.iloc[mid_point:].mean()
        
        # Calculate drift percentage
        drift_pct = ((second_half_hr - first_half_hr) / first_half_hr * 100) if first_half_hr > 0 else 0
        
        # Interpretation
        if drift_pct < 3:
            severity = 'excellent'
            message = 'Excelente control cardiovascular'
        elif drift_pct < 5:
            severity = 'good'
            message = 'Deriva normal para sesión'
        elif drift_pct < 8:
            severity = 'moderate'
            message = 'Deriva moderada, monitoriza hidratación'
        else:
            severity = 'high'
            message = 'Deriva alta, posible deshidratación o fatiga'
        
        return {
            'has_data': True,
            'first_half_hr': first_half_hr,
            'second_half_hr': second_half_hr,
            'drift_pct': drift_pct,
            'severity': severity,
            'message': message
        }
    
    def analyze_hr_pace_coupling(self, run: Dict) -> Dict:
        """Analyze HR-Pace coupling (efficiency metric)
        
        Good coupling = HR and pace move together proportionally
        
        Args:
            run: Single run data
            
        Returns:
            Coupling analysis
        """
        df = run.get('data')
        if df is None or 'heart_rate' not in df.columns or 'pace' not in df.columns:
            return {'has_data': False}
        
        # Get clean data
        clean_data = df[['heart_rate', 'pace']].dropna()
        if len(clean_data) < 20:
            return {'has_data': False}
        
        # Calculate coefficient of variation for each
        hr_cv = clean_data['heart_rate'].std() / clean_data['heart_rate'].mean() * 100
        pace_cv = clean_data['pace'].std() / clean_data['pace'].mean() * 100
        
        # Coupling ratio (lower is better - means HR more stable relative to pace changes)
        coupling_ratio = hr_cv / pace_cv if pace_cv > 0 else 0
        
        # Correlation
        correlation = clean_data['heart_rate'].corr(clean_data['pace'])
        
        # Interpretation
        if coupling_ratio < 0.5:
            efficiency = 'excellent'
            message = 'Excelente eficiencia cardiovascular'
        elif coupling_ratio < 1.0:
            efficiency = 'good'
            message = 'Buena eficiencia cardiovascular'
        elif coupling_ratio < 1.5:
            efficiency = 'moderate'
            message = 'Eficiencia moderada'
        else:
            efficiency = 'poor'
            message = 'Eficiencia cardiovascular baja, trabaja base aeróbica'
        
        return {
            'has_data': True,
            'hr_cv': hr_cv,
            'pace_cv': pace_cv,
            'coupling_ratio': coupling_ratio,
            'correlation': correlation,
            'efficiency': efficiency,
            'message': message
        }
    
    def analyze_aerobic_decoupling(self, run: Dict) -> Dict:
        """Analyze aerobic decoupling
        
        Compares HR/Pace efficiency between first and second half
        
        Args:
            run: Single run data
            
        Returns:
            Decoupling analysis
        """
        df = run.get('data')
        if df is None or 'heart_rate' not in df.columns or 'pace' not in df.columns:
            return {'has_data': False}
        
        clean_data = df[['heart_rate', 'pace']].dropna()
        if len(clean_data) < 20:
            return {'has_data': False}
        
        # Split into halves
        mid_point = len(clean_data) // 2
        first_half = clean_data.iloc[:mid_point]
        second_half = clean_data.iloc[mid_point:]
        
        # Calculate HR/Pace ratio for each half
        first_ratio = first_half['heart_rate'].mean() / first_half['pace'].mean()
        second_ratio = second_half['heart_rate'].mean() / second_half['pace'].mean()
        
        # Decoupling percentage
        decoupling_pct = ((second_ratio - first_ratio) / first_ratio * 100) if first_ratio > 0 else 0
        
        # Interpretation
        if abs(decoupling_pct) < 5:
            status = 'excellent'
            message = 'Excelente base aeróbica, sin desacoplamiento'
        elif abs(decoupling_pct) < 10:
            status = 'good'
            message = 'Buen acoplamiento aeróbico'
        else:
            status = 'poor'
            message = 'Desacoplamiento alto, necesitas más volumen Z2'
        
        return {
            'has_data': True,
            'first_half_ratio': first_ratio,
            'second_half_ratio': second_ratio,
            'decoupling_pct': decoupling_pct,
            'status': status,
            'message': message
        }
    
    def get_cardiovascular_insights(self) -> List[str]:
        """Generate cardiovascular insights across all runs
        
        Returns:
            List of insights
        """
        insights = []
        
        # Analyze recent runs for patterns
        recent_runs = sorted(self.runs, key=lambda x: x['start_time'], reverse=True)[:10]
        
        drift_issues = 0
        decoupling_issues = 0
        good_efficiency = 0
        
        for run in recent_runs:
            drift = self.analyze_cardiac_drift(run)
            if drift.get('has_data'):
                if drift['severity'] in ['moderate', 'high']:
                    drift_issues += 1
            
            decoupling = self.analyze_aerobic_decoupling(run)
            if decoupling.get('has_data'):
                if decoupling['status'] == 'poor':
                    decoupling_issues += 1
            
            coupling = self.analyze_hr_pace_coupling(run)
            if coupling.get('has_data'):
                if coupling['efficiency'] in ['excellent', 'good']:
                    good_efficiency += 1
        
        # Generate insights
        if drift_issues >= 3:
            insights.append(
                "⚠️ **Deriva cardíaca alta**: Detectada en varias sesiones recientes. "
                "Mejora hidratación pre-durante carrera y monitoriza temperatura ambiente."
            )
        
        if decoupling_issues >= 3:
            insights.append(
                "🏃 **Desacoplamiento aeróbico**: Necesitas más base aeróbica. "
                "Aumenta volumen en Z2 (conversacional) para mejorar eficiencia."
            )
        
        if good_efficiency >= 5:
            insights.append(
                "✅ **Excelente eficiencia cardiovascular**: Mantiene buena relación FC-Ritmo. "
                "Tu sistema cardiovascular responde bien al esfuerzo."
            )
        
        if not insights:
            insights.append(
                "📊 Necesitas más datos de FC para análisis cardiovascular completo."
            )
        
        return insights
    
    def get_cardiovascular_summary(self) -> Dict:
        """Get comprehensive cardiovascular analysis
        
        Returns:
            Complete cardiovascular metrics
        """
        # Analyze recent run
        recent_run = sorted(self.runs, key=lambda x: x['start_time'], reverse=True)[0] if self.runs else None
        
        return {
            'recent_drift': self.analyze_cardiac_drift(recent_run) if recent_run else {},
            'recent_coupling': self.analyze_hr_pace_coupling(recent_run) if recent_run else {},
            'recent_decoupling': self.analyze_aerobic_decoupling(recent_run) if recent_run else {},
            'insights': self.get_cardiovascular_insights()
        }
