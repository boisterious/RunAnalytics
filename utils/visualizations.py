"""Visualization Components for Apex Run Analytics"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Optional
import numpy as np


# Cyberpunk color scheme
COLORS = {
    'cyan': '#00FFFF',
    'lime': '#32CD32',
    'magenta': '#FF00FF',
    'yellow': '#FFFF00',
    'orange': '#FF8C00',
    'bg_dark': '#0A0E1A',
    'bg_card': '#1A1F35',
    'text': '#E0E0E0',
    'grid': '#2A2F45'
}


def create_plotly_theme() -> Dict:
    """Create custom Plotly theme for cyberpunk aesthetics"""
    return {
        'layout': {
            'paper_bgcolor': COLORS['bg_dark'],
            'plot_bgcolor': COLORS['bg_card'],
            'font': {'color': COLORS['text'], 'family': 'Inter, sans-serif'},
            'xaxis': {
                'gridcolor': COLORS['grid'],
                'zerolinecolor': COLORS['grid']
            },
            'yaxis': {
                'gridcolor': COLORS['grid'],
                'zerolinecolor': COLORS['grid']
            }
        }
    }


def create_evolution_chart(runs_df: pd.DataFrame, metric: str, title: str) -> go.Figure:
    """
    Create a time-series evolution chart for a given metric
    
    Args:
        runs_df: DataFrame with columns: start_time, [metric]
        metric: Column name to plot
        title: Chart title
        
    Returns:
        Plotly figure
    """
    # Sort by date
    df = runs_df.sort_values('start_time').copy()
    
    # Create figure
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['start_time'],
        y=df[metric],
        mode='lines+markers',
        name=title,
        line=dict(color=COLORS['cyan'], width=3),
        marker=dict(size=8, color=COLORS['lime'], line=dict(width=2, color=COLORS['cyan'])),
        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>' + title + ': %{y:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=20, color=COLORS['text'])),
        xaxis_title='Fecha',
        yaxis_title=title,
        **create_plotly_theme()['layout'],
        hovermode='x unified',
        height=400,
        legend=dict(
            font=dict(color='#FFFFFF', size=12),
            bgcolor='rgba(26, 31, 53, 0.95)',
            bordercolor='#FFFFFF',
            borderwidth=1
        )
    )
    
    return fig


def create_session_analysis_chart(trackpoints_df: pd.DataFrame) -> go.Figure:
    """
    Create multi-axis chart showing altitude, pace, and heart rate over time
    
    Args:
        trackpoints_df: DataFrame with columns: timestamp, altitude, heart_rate, distance
        
    Returns:
        Plotly figure with multiple y-axes
    """
    # Calculate pace per segment
    df = trackpoints_df.copy()
    
    # Calculate instantaneous pace (if we have distance and timestamp)
    if 'distance' in df.columns and len(df) > 1:
        df['time_diff'] = df['timestamp'].diff().dt.total_seconds() / 60  # minutes
        df['dist_diff'] = df['distance'].diff() / 1000  # km
        df['instant_pace'] = df['time_diff'] / df['dist_diff']
        # Smooth and cap outliers
        df['instant_pace'] = df['instant_pace'].rolling(window=10, min_periods=1).mean()
        df['instant_pace'] = df['instant_pace'].clip(upper=15)  # Cap at 15 min/km
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add altitude trace
    if 'altitude' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['altitude'],
                name='Altitud (m)',
                line=dict(color=COLORS['lime'], width=2),
                fill='tozeroy',
                fillcolor='rgba(50, 205, 50, 0.2)'
            ),
            secondary_y=False
        )
    
    # Add heart rate trace
    if 'heart_rate' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['heart_rate'],
                name='Pulsaciones (bpm)',
                line=dict(color=COLORS['magenta'], width=2)
            ),
            secondary_y=True
        )
    
    # Add pace trace
    if 'instant_pace' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['instant_pace'],
                name='Ritmo (min/km)',
                line=dict(color=COLORS['cyan'], width=2, dash='dot')
            ),
            secondary_y=True
        )
    
    # Update layout
    fig.update_xaxes(title_text="Tiempo")
    fig.update_yaxes(title_text="Altitud (m)", secondary_y=False, gridcolor=COLORS['grid'])
    fig.update_yaxes(title_text="BPM / Ritmo", secondary_y=True, gridcolor=COLORS['grid'])
    
    fig.update_layout(
        title="Análisis de Sesión",
        **create_plotly_theme()['layout'],
        hovermode='x unified',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color='#FFFFFF'),
            bgcolor='rgba(26, 31, 53, 0.95)',
            bordercolor='#FFFFFF',
            borderwidth=1
        )
    )
    
    return fig


def create_cadence_pace_scatter(runs_df: pd.DataFrame) -> go.Figure:
    """
    Create scatter plot showing relationship between cadence and pace
    
    Args:
        runs_df: DataFrame with columns: avg_cadence, pace_min_per_km, distance_km
        
    Returns:
        Plotly figure
    """
    # Filter out runs without cadence data
    df = runs_df[runs_df['avg_cadence'].notna()].copy()
    
    if len(df) == 0:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos de cadencia disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color=COLORS['text'])
        )
        fig.update_layout(**create_plotly_theme()['layout'], height=400)
        return fig
    
    # Create scatter plot
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['avg_cadence'],
        y=df['pace_min_per_km'],
        mode='markers',
        marker=dict(
            size=df['distance_km'] * 2,  # Size based on distance
            color=df['distance_km'],
            colorscale=[[0, COLORS['cyan']], [1, COLORS['lime']]],
            showscale=True,
            colorbar=dict(title="Distancia (km)"),
            line=dict(width=1, color=COLORS['text'])
        ),
        text=df['distance_km'].round(2).astype(str) + ' km',
        hovertemplate='<b>Cadencia:</b> %{x:.0f} spm<br>' +
                      '<b>Ritmo:</b> %{y:.2f} min/km<br>' +
                      '<b>Distancia:</b> %{text}<extra></extra>'
    ))
    
    # Add trendline
    if len(df) > 2:
        z = np.polyfit(df['avg_cadence'], df['pace_min_per_km'], 1)
        p = np.poly1d(z)
        x_trend = np.linspace(df['avg_cadence'].min(), df['avg_cadence'].max(), 100)
        
        fig.add_trace(go.Scatter(
            x=x_trend,
            y=p(x_trend),
            mode='lines',
            name='Tendencia',
            line=dict(color=COLORS['yellow'], width=2, dash='dash'),
            hoverinfo='skip'
        ))
    
    fig.update_layout(
        title="Relación Cadencia vs Ritmo",
        xaxis_title="Cadencia Media (spm)",
        yaxis_title="Ritmo (min/km)",
        **create_plotly_theme()['layout'],
        height=450,
        showlegend=False
    )
    
    # Invert y-axis (lower pace = better)
    fig.update_yaxes(autorange="reversed")
    
    return fig


def create_kpi_card_html(title: str, value: str, subtitle: str = "", icon: str = "📊") -> str:
    """
    Generate HTML for a KPI card with cyberpunk styling
    
    Args:
        title: Card title
        value: Main value to display
        subtitle: Optional subtitle
        icon: Emoji icon
        
    Returns:
        HTML string
    """
    subtitle_html = f'<div class="kpi-subtitle">{subtitle}</div>' if subtitle else ''
    
    return f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-content">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            {subtitle_html}
        </div>
    </div>
    """


def format_pace(pace_minutes: float) -> str:
    """
    Format pace from decimal minutes to min:sec format
    
    Args:
        pace_minutes: Pace in decimal minutes (e.g., 5.5)
        
    Returns:
        Formatted string (e.g., "5:30")
    """
    if pd.isna(pace_minutes) or pace_minutes == 0:
        return "N/A"
    
    minutes = int(pace_minutes)
    seconds = int((pace_minutes - minutes) * 60)
    return f"{minutes}:{seconds:02d}"


def format_duration(duration_minutes: float) -> str:
    """
    Format duration from minutes to h:mm:ss format
    
    Args:
        duration_minutes: Duration in decimal minutes
        
    Returns:
        Formatted string (e.g., "1:23:45")
    """
    if pd.isna(duration_minutes) or duration_minutes == 0:
        return "N/A"
    
    hours = int(duration_minutes // 60)
    minutes = int(duration_minutes % 60)
    seconds = int((duration_minutes % 1) * 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"
