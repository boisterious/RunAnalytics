"""Multi-Level Coaching Engine

Provides expert coaching insights at different time horizons:
- Short term (7 days)
- Medium term (4-12 weeks)  
- Long term (3-12 months)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class CoachingInsight:
    """Single coaching insight/recommendation"""
    
    def __init__(self, category: str, title: str, message: str, severity: str = 'info'):
        """
        Args:
            category: Category emoji + name (e.g., "🎯 Objetivos")
            title: Insight title
            message: Detailed message
            severity: 'success', 'info', 'warning', 'error'
        """
        self.category = category
        self.title = title
        self.message = message
        self.severity = severity


class ShortTermCoach:
    """Analyze last 7 days and provide weekly insights"""
    
    def __init__(self, runs: List[Dict]):
        self.runs = runs
        self.weekly_runs = self._get_recent_runs(days=7)
    
    def _get_recent_runs(self, days: int) -> List[Dict]:
        """Get runs from last N days"""
        if not self.runs:
            return []
        
        # Make cutoff_date timezone-naive
        cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=days)
        
        # Filter runs, converting timestamps to naive if needed
        recent = []
        for run in self.runs:
            run_time = run['start_time']
            # Convert to naive datetime if it's timezone-aware
            if hasattr(run_time, 'tz_localize'):
                # It's a pandas Timestamp
                run_time = run_time.tz_localize(None) if run_time.tz else run_time
            elif hasattr(run_time, 'tzinfo') and run_time.tzinfo:
                # It's a datetime with timezone
                run_time = run_time.replace(tzinfo=None)
            
            if run_time >= cutoff_date:
                recent.append(run)
        
        return recent
    
    def weekly_summary(self) -> Dict:
        """Calculate weekly summary metrics"""
        if not self.weekly_runs:
            return {}
        
        total_km = sum(run['metrics']['distance_km'] for run in self.weekly_runs)
        total_time = sum(run['metrics']['duration_minutes'] for run in self.weekly_runs)
        total_load = sum(run.get('training_load', {}).get('trimp', 0) 
                        for run in self.weekly_runs)
        
        # Session type distribution
        session_types = {}
        for run in self.weekly_runs:
            session_name = run.get('session_info', {}).get('name', 'Desconocido')
            session_types[session_name] = session_types.get(session_name, 0) + 1
        
        return {
            'total_runs': len(self.weekly_runs),
            'total_km': total_km,
            'total_time_hours': total_time / 60,
            'total_load': total_load,
            'session_types': session_types,
            'avg_km_per_run': total_km / len(self.weekly_runs) if self.weekly_runs else 0
        }
    
    def generate_recommendations(self) -> List[CoachingInsight]:
        """Generate weekly recommendations"""
        insights = []
        summary = self.weekly_summary()
        
        if not summary:
            insights.append(CoachingInsight(
                "💪 Entrenamiento",
                "Comienza tu semana",
                "No hay sesiones esta semana. ¡Es hora de empezar! Objetivo: 3-4 sesiones semanales.",
                "info"
            ))
            return insights
        
        total_runs = summary['total_runs']
        total_km = summary['total_km']
        total_load = summary['total_load']
        session_types = summary['session_types']
        
        # Volume analysis
        if total_km > 50:
            insights.append(CoachingInsight(
                "📈 Volumen",
                "Semana de alto volumen",
                f"Has acumulado {total_km:.1f} km esta semana. Excelente trabajo. "
                f"Asegúrate de incluir al menos 1 día de recuperación.",
                "success"
            ))
        elif total_km < 15 and total_runs > 0:
            insights.append(CoachingInsight(
                "📉 Volumen",
                "Volumen bajo",
                f"Solo {total_km:.1f} km esta semana. Considera aumentar gradualmente 10% por semana.",
                "warning"
            ))
        
        # Session variety
        if len(session_types) == 1:
            insights.append(CoachingInsight(
                "🔬 Variedad",
                "Falta variedad de sesiones",
                f"Todas tus sesiones son del mismo tipo. Incluye variedad: tempo, intervalos, recuperación.",
                "warning"
            ))
        elif len(session_types) >= 3:
            insights.append(CoachingInsight(
                "🎨 Variedad",
                "Excelente variedad",
                f"Has realizado {len(session_types)} tipos diferentes de sesión. ¡Perfecto para desarrollo integral!",
                "success"
            ))
        
        # Training load
        if total_load > 400:
            insights.append(CoachingInsight(
                "⚠️ Carga",
                "Carga alta esta semana",
                f"TRIMP semanal: {int(total_load)}. Esto es alto. Monitorea señales de fatiga y asegura buena recuperación.",
                "warning"
            ))
        
        # Frequency
        if total_runs < 2:
            insights.append(CoachingInsight(
                "🏃 Frecuencia",
                "Baja frecuencia",
                "Solo has entrenado 1 vez. Para progresar, apunta a 3-5 sesiones semanales.",
                "warning"
            ))
        elif total_runs >= 5:
            insights.append(CoachingInsight(
                "🏃 Frecuencia",
                "Consistencia excelente",
                f"{total_runs} sesiones esta semana. Mantienes buena consistencia.",
                "success"
            ))
        
        return insights


class MediumTermCoach:
    """Analyze last 4-12 weeks for trends"""
    
    def __init__(self, runs: List[Dict]):
        self.runs = runs
        self.monthly_runs = self._get_recent_runs(days=30)
    
    def _get_recent_runs(self, days: int) -> List[Dict]:
        """Get runs from last N days"""
        if not self.runs:
            return []
        
        # Make cutoff_date timezone-naive
        cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=days)
        
        # Filter runs, converting timestamps to naive if needed
        recent = []
        for run in self.runs:
            run_time = run['start_time']
            # Convert to naive datetime if it's timezone-aware
            if hasattr(run_time, 'tz_localize'):
                # It's a pandas Timestamp
                run_time = run_time.tz_localize(None) if run_time.tz else run_time
            elif hasattr(run_time, 'tzinfo') and run_time.tzinfo:
                # It's a datetime with timezone
                run_time = run_time.replace(tzinfo=None)
            
            if run_time >= cutoff_date:
                recent.append(run)
        
        return recent
    
    def analyze_progression(self) -> Dict:
        """Analyze progression over last month"""
        if len(self.monthly_runs) < 5:
            return {'insufficient_data': True}
        
        # Sort by date
        sorted_runs = sorted(self.monthly_runs, key=lambda x: x['start_time'])
        
        # Split into first half and second half
        mid_point = len(sorted_runs) // 2
        first_half = sorted_runs[:mid_point]
        second_half = sorted_runs[mid_point:]
        
        # Compare metrics
        def avg_metric(runs, metric_path):
            values = []
            for run in runs:
                if metric_path == 'efficiency_index':
                    val = run['metrics'].get('efficiency_index')
                    if val:
                        values.append(val)
                elif metric_path == 'pace':
                    values.append(run['metrics']['pace_min_per_km'])
                elif metric_path == 'distance':
                    values.append(run['metrics']['distance_km'])
            return np.mean(values) if values else 0
        
        ei_first = avg_metric(first_half, 'efficiency_index')
        ei_second = avg_metric(second_half, 'efficiency_index')
        
        pace_first = avg_metric(first_half, 'pace')
        pace_second = avg_metric(second_half, 'pace')
        
        dist_first = avg_metric(first_half, 'distance')
        dist_second = avg_metric(second_half, 'distance')
        
        return {
            'efficiency_trend': 'improving' if ei_second > ei_first else 'declining' if ei_second < ei_first else 'stable',
            'ei_change_pct': ((ei_second - ei_first) / ei_first * 100) if ei_first > 0 else 0,
            'pace_trend': 'improving' if pace_second < pace_first else 'declining' if pace_second > pace_first else 'stable',
            'pace_change_pct': ((pace_first - pace_second) / pace_first * 100) if pace_first > 0 else 0,
            'volume_trend': 'increasing' if dist_second > dist_first else 'decreasing' if dist_second < dist_first else 'stable'
        }
    
    def generate_recommendations(self) -> List[CoachingInsight]:
        """Generate monthly insights"""
        insights = []
        
        if len(self.monthly_runs) < 5:
            insights.append(CoachingInsight(
                "📊 Datos",
                "Necesitas más sesiones",
                "Con menos de 5 sesiones al mes, es difícil analizar tendencias. Aumenta la frecuencia.",
                "info"
            ))
            return insights
        
        progression = self.analyze_progression()
        
        # Efficiency trend
        if progression.get('efficiency_trend') == 'improving':
            change = progression.get('ei_change_pct', 0)
            insights.append(CoachingInsight(
                "📈 Progreso",
                "Mejora en eficiencia",
                f"Tu Efficiency Index ha mejorado {change:.1f}% este mes. ¡Tu sistema cardiovascular se está adaptando!",
                "success"
            ))
        elif progression.get('efficiency_trend') == 'declining':
            insights.append(CoachingInsight(
                "⚠️ Eficiencia",
                "Descenso en eficiencia",
                "Tu Efficiency Index ha bajado. Posibles causas: fatiga acumulada, necesidad de más base aeróbica (Z2).",
                "warning"
            ))
        
        # Pace trend
        if progression.get('pace_trend') == 'improving':
            change = progression.get('pace_change_pct', 0)
            insights.append(CoachingInsight(
                "⚡ Velocidad",
                "Velocidad en aumento",
                f"Tu ritmo promedio ha mejorado {change:.1f}%. Sigue así y considera añadir trabajo de velocidad.",
                "success"
            ))
        
        # Volume trend
        if progression.get('volume_trend') == 'increasing':
            insights.append(CoachingInsight(
                "📊 Volumen",
                "Aumento de kilometraje",
                "Estás aumentando volumen. Asegúrate de hacerlo gradualmente (regla 10%) para evitar lesiones.",
                "info"
            ))
        
        return insights


class LongTermCoach:
    """Analyze 3+ months for long-term trends"""
    
    def __init__(self, runs: List[Dict]):
        self.runs = runs
    
    def analyze_annual_progression(self) -> Dict:
        """Analyze long-term progression"""
        if len(self.runs) < 20:
            return {'insufficient_data': True}
        
        # Group by month
        monthly_stats = {}
        for run in self.runs:
            month_key = run['start_time'].strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'runs': [],
                    'total_km': 0,
                    'total_load': 0
                }
            monthly_stats[month_key]['runs'].append(run)
            monthly_stats[month_key]['total_km'] += run['metrics']['distance_km']
            monthly_stats[month_key]['total_load'] += run.get('training_load', {}).get('trimp', 0)
        
        # Calculate trends
        months = sorted(monthly_stats.keys())
        if len(months) < 3:
            return {'insufficient_data': True}
        
        km_trend = [monthly_stats[m]['total_km'] for m in months]
        
        return {
            'total_months': len(months),
            'avg_monthly_km': np.mean(km_trend),
            'km_trend': 'increasing' if km_trend[-1] > km_trend[0] else 'decreasing',
            'most_active_month': max(months, key=lambda m: monthly_stats[m]['total_km']),
            'total_km_period': sum(monthly_stats[m]['total_km'] for m in months)
        }
    
    def generate_recommendations(self) -> List[CoachingInsight]:
        """Generate long-term insights"""
        insights = []
        
        progression = self.analyze_annual_progression()
        
        if progression.get('insufficient_data'):
            insights.append(CoachingInsight(
                "📅 Historial",
                "Aumenta tu historial",
                "Con más sesiones acumuladas, podremos darte análisis de tendencias a largo plazo.",
                "info"
            ))
            return insights
        
        total_km = progression.get('total_km_period', 0)
        months = progression.get('total_months', 0)
        
        insights.append(CoachingInsight(
            "🏆 Logro",
            f"Acumulado en {months} meses",
            f"Has recorrido {total_km:.0f} km en los últimos {months} meses. ¡Impresionante consistencia!",
            "success"
        ))
        
        if progression.get('km_trend') == 'increasing':
            insights.append(CoachingInsight(
                "📈 Tendencia",
                "Progresión constante",
                "Tu volumen mensual está en aumento. Continúa esta tendencia de forma sostenible.",
                "success"
            ))
        
        return insights


class VirtualCoach:
    """Main coaching engine that combines all analysis levels"""
    
    def __init__(self, runs: List[Dict]):
        self.runs = runs
        self.short_term = ShortTermCoach(runs)
        self.medium_term = MediumTermCoach(runs)
        self.long_term = LongTermCoach(runs)
    
    def generate_all_insights(self) -> Dict[str, List[CoachingInsight]]:
        """Generate insights at all time horizons"""
        return {
            'short_term': self.short_term.generate_recommendations(),
            'medium_term': self.medium_term.generate_recommendations(),
            'long_term': self.long_term.generate_recommendations()
        }
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for dashboard"""
        return {
            'weekly': self.short_term.weekly_summary(),
            'monthly_progression': self.medium_term.analyze_progression(),
            'annual': self.long_term.analyze_annual_progression()
        }
