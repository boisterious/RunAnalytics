"""Enhanced Visualizations

Additional visualization utilities including trend lines, calendar heatmaps,
and multi-session comparators.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def add_trend_line(fig: go.Figure, x_data: list, y_data: list, 
                   name: str = 'Tendencia') -> go.Figure:
    """Add trend line to existing figure with direction indicator
    
    Args:
        fig: Plotly figure
        x_data: X axis data  
        y_data: Y axis data
        name: Trend line name
        
    Returns:
        Figure with trend line added
    """
    if len(y_data) < 2:
        return fig
    
    # Linear regression
    x_numeric = list(range(len(y_data)))
    z = np.polyfit(x_numeric, y_data, 1)
    p = np.poly1d(z)
    
    trend_y = [p(x) for x in x_numeric]
    
    # Determine trend direction
    slope = z[0]
    if slope > 0:
        trend_text = f"↗ Tendencia: +{slope:.3f}/sesión"
        line_color = 'rgba(0, 255, 127, 0.6)'  # Green for improving
    elif slope < 0:
        trend_text = f"↘ Tendencia: {slope:.3f}/sesión"
        line_color = 'rgba(255, 68, 68, 0.6)'  # Red for declining
    else:
        trend_text = "→ Estable"
        line_color = 'rgba(255,255,255,0.4)'
    
    fig.add_trace(go.Scatter(
        x=x_data,
        y=trend_y,
        mode='lines',
        name=trend_text,
        line=dict(dash='dash', color=line_color, width=2),
        hovertemplate=f'{trend_text}<extra></extra>'
    ))
    
    return fig


def create_calendar_heatmap(runs: List[Dict], metric: str = 'distance') -> go.Figure:
    """Create GitHub-style calendar heatmap
    
    Args:
        runs: List of run dictionaries
        metric: Metric to display ('distance', 'duration', 'load')
        
    Returns:
        Plotly heatmap figure
    """
    if not runs:
        return go.Figure()
    
    # Prepare data
    daily_data = {}
    for run in runs:
        date = run['start_time'].date()
        metrics = run['metrics']
        
        if metric == 'distance':
            value = metrics.get('distance_km', 0)
        elif metric == 'duration':
            value = metrics.get('duration_minutes', 0)
        elif metric == 'load':
            value = run.get('training_load', {}).get('trimp', 0)
        else:
            value = metrics.get('distance_km', 0)
        
        if date in daily_data:
            daily_data[date] += value
        else:
            daily_data[date] = value
    
    # Create date range
    if daily_data:
        min_date = min(daily_data.keys())
        max_date = max(daily_data.keys())
        
        # Create DataFrame for heatmap
        dates = pd.date_range(min_date, max_date, freq='D')
        values = [daily_data.get(d.date(), 0) for d in dates]
        
        metric_labels = {
            'distance': 'km',
            'duration': 'min',
            'load': 'TRIMP'
        }
        
        fig = go.Figure()
        
        # Bar chart version
        fig.add_trace(go.Bar(
            x=dates,
            y=values,
            marker=dict(
                color=values,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title=metric_labels.get(metric, metric))
            ),
            hovertemplate='%{x|%d/%m/%Y}<br>%{y:.1f} ' + metric_labels.get(metric, '') + '<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Calendario de Entrenamiento ({metric_labels.get(metric, metric)})',
            xaxis_title='Fecha',
            yaxis_title=metric_labels.get(metric, metric),
            paper_bgcolor='#0E1117',
            plot_bgcolor='#262730',
            font=dict(color='#FAFAFA'),
            height=300,
            legend=dict(
                font=dict(color='#FFFFFF'),
                bgcolor='rgba(26, 31, 53, 0.95)',
                bordercolor='#FFFFFF',
                borderwidth=1
            )
        )
        
        return fig
    
    return go.Figure()


def create_load_chart(runs: List[Dict]) -> go.Figure:
    """Create acute vs chronic load chart
    
    Args:
        runs: List of runs with training_load
        
    Returns:
        Load comparison chart
    """
    if not runs:
        return go.Figure()
    
    # Sort by date
    sorted_runs = sorted(runs, key=lambda x: x['start_time'])
    
    dates = []
    acute_loads = []
    chronic_loads = []
    ratios = []
    
    for i, run in enumerate(sorted_runs):
        date = run['start_time']
        dates.append(date)
        
        # Calculate acute load (last 7 days)
        acute_window = [r for r in sorted_runs[max(0, i-7):i+1]]
        acute_load = sum(r.get('training_load', {}).get('trimp', 0) for r in acute_window)
        acute_loads.append(acute_load)
        
        # Calculate chronic load (last 42 days)
        chronic_window = [r for r in sorted_runs[max(0, i-42):i+1]]
        chronic_load = sum(r.get('training_load', {}).get('trimp', 0) for r in chronic_window) / 6  # Weekly average
        chronic_loads.append(chronic_load)
        
        # Ratio
        ratio = acute_load / chronic_load if chronic_load > 0 else 0
        ratios.append(ratio)
    
    fig = go.Figure()
    
    # Acute load
    fig.add_trace(go.Scatter(
        x=dates,
        y=acute_loads,
        mode='lines',
        name='Carga Aguda (7d)',
        line=dict(color='#FF6B6B', width=2)
    ))
    
    # Chronic load
    fig.add_trace(go.Scatter(
        x=dates,
        y=chronic_loads,
        mode='lines',
        name='Carga Crónica (42d)',
        line=dict(color='#4ECDC4', width=2)
    ))
    
    # Add risk zones
    y_max = max(max(acute_loads), max(chronic_loads)) if acute_loads and chronic_loads else 100
    
    fig.add_hrect(
        y0=0, y1=y_max,
        fillcolor='rgba(0, 255, 127, 0.1)',
        layer='below', line_width=0,
        annotation_text='Zona Segura',
        annotation_position='top left'
    )
    
    fig.update_layout(
        title='Carga de Entrenamiento: Aguda vs Crónica',
        xaxis_title='Fecha',
        yaxis_title='TRIMP',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#262730',
        font=dict(color='#FAFAFA'),
        height=400,
        hovermode='x unified',
        legend=dict(
            font=dict(color='#FFFFFF'),
            bgcolor='rgba(26, 31, 53, 0.95)',
            bordercolor='#FFFFFF',
            borderwidth=1
        )
    )
    
    return fig


def create_session_comparator(selected_runs: List[Dict]) -> go.Figure:
    """Compare multiple sessions side-by-side
    
    Args:
        selected_runs: List of runs to compare
        
    Returns:
        Multi-session comparison chart
    """
    if not selected_runs or len(selected_runs) < 2:
        return go.Figure()
    
    fig = go.Figure()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    
    for idx, run in enumerate(selected_runs[:5]):  # Max 5 runs
        df = run.get('data', pd.DataFrame())
        if df.empty or 'distance' not in df.columns:
            continue
        
        # Normalize distance to km
        distance_km = df['distance'] / 1000
        
        # Plot pace if available
        if 'pace' in df.columns:
            label = f"{run['start_time'].strftime('%d/%m')} - {run['filename'][:20]}"
            
            fig.add_trace(go.Scatter(
                x=distance_km,
                y=df['pace'],
                mode='lines',
                name=label,
                line=dict(color=colors[idx % len(colors)], width=2)
            ))
    
    fig.update_layout(
        title='Comparación de Sesiones',
        xaxis_title='Distancia (km)',
        yaxis_title='Ritmo (min/km)',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#262730',
        font=dict(color='#FAFAFA'),
        height=400,
        yaxis=dict(autorange='reversed'),  # Lower pace is better
        hovermode='x unified',
        legend=dict(
            font=dict(color='#FFFFFF'),
            bgcolor='rgba(26, 31, 53, 0.95)',
            bordercolor='#FFFFFF',
            borderwidth=1
        )
    )
    
    return fig


def create_hr_zones_distribution_chart(runs: List[Dict]) -> go.Figure:
    """Create stacked bar chart showing HR zones distribution
    
    Args:
        runs: List of runs with hr_zones data
        
    Returns:
        Stacked bar chart
    """
    if not runs:
        return go.Figure()
    
    # Prepare data
    runs_with_zones = [r for r in runs if r.get('hr_zones')]
    
    if not runs_with_zones:
        return go.Figure()
    
    dates = []
    zone_data = {'Z1': [], 'Z2': [], 'Z3': [], 'Z4': [], 'Z5': []}
    
    for run in runs_with_zones[-20:]:  # Last 20 runs
        dates.append(run['start_time'].strftime('%d/%m'))
        
        hr_zones = run.get('hr_zones', {})
        for zone_id in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']:
            zone_data[zone_id].append(hr_zones.get(zone_id, {}).get('percentage', 0))
    
    fig = go.Figure()
    
    zone_colors = {
        'Z1': '#00FF7F',
        'Z2': '#00BFFF',
        'Z3': '#FFD700',
        'Z4': '#FFA500',
        'Z5': '#FF4444'
    }
    
    for zone_id in ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']:
        fig.add_trace(go.Bar(
            name=zone_id,
            x=dates,
            y=zone_data[zone_id],
            marker_color=zone_colors[zone_id]
        ))
    
    fig.update_layout(
        title='Distribución de Zonas FC por Sesión',
        xaxis_title='Sesión',
        yaxis_title='Tiempo (%)',
        barmode='stack',
        paper_bgcolor='#0E1117',
        plot_bgcolor='#262730',
        font=dict(color='#FAFAFA'),
        height=400,
        legend=dict(
            font=dict(color='#FFFFFF'),
            bgcolor='rgba(26, 31, 53, 0.95)',
            bordercolor='#FFFFFF',
            borderwidth=1
        )
    )
    
    return fig
