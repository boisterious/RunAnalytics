"""
Apex Run Analytics - Premium Running Data Analysis Platform
Analyze TCX files with advanced metrics: GAP, Efficiency Index, and Personal Records
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from datetime import datetime
import numpy as np
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from pathlib import Path

# Add utils to path
sys.path.append(str(Path(__file__).parent))

from utils.tcx_parser import parse_tcx_files
from utils.metrics import RunningMetrics, PersonalRecords
from utils.visualizations import (
    create_evolution_chart, create_session_analysis_chart,
    create_cadence_pace_scatter, create_kpi_card_html,
    format_pace, format_duration, COLORS
)
from utils.persistence import (
    load_runs_history, save_runs_history, merge_runs, 
    clear_history, get_history_stats
)
from utils.ui_helpers import (
    create_metric_tooltip, create_expandable_help, METRICS_GUIDE
)
from utils.training_analyzer import (
    SessionClassifier, HRZones, TrainingLoadCalculator, calculate_session_load
)
from utils.coaching_engine import VirtualCoach, CoachingInsight
from utils.terrain_analyzer import TerrainAnalyzer, classify_all_runs
from utils.biomechanics_analyzer import BiomechanicsAnalyzer
from utils.cardiovascular_analyzer import CardiovascularAnalyzer
from utils.performance_predictor import PerformancePredictor
from utils.session_analyzer import SessionAnalyzer
from utils.enhanced_visualizations import (
    add_trend_line, create_calendar_heatmap, create_load_chart,
    create_session_comparator, create_hr_zones_distribution_chart
)


# Page configuration
st.set_page_config(
    page_title="Apex Run Analytics",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# Load custom CSS
def load_css():
    """Load custom CSS for premium dark mode"""
    css_path = Path(__file__).parent / "styles" / "custom.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()


# Initialize session state and load history
if 'runs' not in st.session_state:
    # Load historical data on first run
    st.session_state.runs = load_runs_history()
    
    # Recalculate metrics for loaded history to ensure consistency and add new features
    if st.session_state.runs:
        from utils.training_analyzer import calculate_session_load
        from utils.metrics import RunningMetrics
        
        # 1. Recalculate metrics (Best Efforts) - ONLY if not already present in saved data
        needs_metrics_update = False
        for run in st.session_state.runs:
            # Check if best_efforts is missing or empty
            if 'best_efforts' not in run.get('metrics', {}) or not run['metrics'].get('best_efforts'):
                needs_metrics_update = True
                break
        
        if needs_metrics_update:
            logger.info("Recalculating metrics (Best Efforts) for runs missing this data...")
            for i, run in enumerate(st.session_state.runs):
                # Only recalculate if best_efforts is missing
                if 'best_efforts' not in run.get('metrics', {}) or not run['metrics'].get('best_efforts'):
                    if 'data' in run and not run['data'].empty:
                        metrics_calculator = RunningMetrics(run['data'])
                        new_metrics = metrics_calculator.calculate_all_metrics()
                        
                        if new_metrics.get('avg_heart_rate') is None and run['metrics'].get('avg_heart_rate'):
                            new_metrics['avg_heart_rate'] = run['metrics']['avg_heart_rate']
                        
                        run['metrics'].update(new_metrics)
            logger.info("Metrics recalculation completed.")
            # Save updated runs to persist best_efforts
            save_runs_history(st.session_state.runs)
        else:
            logger.info("Skipping metrics recalculation (best_efforts already exists in data).")
        
        # 2. Recalculate TRIMP - ONLY if not already present in saved data
        needs_trimp_update = False
        for run in st.session_state.runs:
            if 'training_load' not in run or not run.get('training_load'):
                needs_trimp_update = True
                break
        
        if needs_trimp_update:
            all_max_hrs = [r.get('max_hr_estimated', 0) for r in st.session_state.runs if r.get('max_hr_estimated')]
            global_max_hr = max(all_max_hrs) if all_max_hrs else 185
            if global_max_hr < 170: global_max_hr = 185
            
            logger.info(f"Recalculating TRIMP for runs missing this data (Max HR: {global_max_hr})...")
            
            for i, run in enumerate(st.session_state.runs):
                if 'training_load' not in run or not run.get('training_load'):
                    try:
                        run['training_load'] = calculate_session_load(run, max_hr=global_max_hr)
                    except Exception as e:
                        logger.error(f"Error calculating load for run {i}: {e}")
                        run['training_load'] = {'trimp': 0, 'tss': 0}
            
            logger.info("TRIMP calculation completed.")
            # Save updated runs to persist training_load
            save_runs_history(st.session_state.runs)
        else:
            logger.info("Skipping TRIMP recalculation (training_load already exists in data).")
if 'runs_df' not in st.session_state:
    st.session_state.runs_df = None
if 'history_loaded' not in st.session_state:
    st.session_state.history_loaded = False

# Generate runs_df from loaded history
if st.session_state.runs and st.session_state.runs_df is None:
    summary_data = []
    for run in st.session_state.runs:
        metrics = run['metrics']
        summary_data.append({
            'filename': run['filename'],
            'start_time': run['start_time'],
            'distance_km': metrics['distance_km'],
            'duration_minutes': metrics['duration_minutes'],
            'pace_min_per_km': metrics['pace_min_per_km'],
            'elevation_gain': metrics['elevation_gain'],
            'gap_pace_min_per_km': metrics['gap_pace_min_per_km'],
            'avg_heart_rate': metrics['avg_heart_rate'],
            'max_heart_rate': metrics['max_heart_rate'],
            'avg_cadence': metrics['avg_cadence'],
            'efficiency_index': metrics['efficiency_index'],
            'gap_efficiency_index': metrics['gap_efficiency_index']
        })
    st.session_state.runs_df = pd.DataFrame(summary_data)


# Custom header
st.markdown("""
<div class="main-header">
    <h1 class="main-title">⚡ Apex Run Analytics</h1>
    <p class="main-subtitle">Advanced Performance Metrics • GAP • Efficiency Index • Personal Records</p>
</div>
""", unsafe_allow_html=True)


# File upload section
st.markdown("## 📁 Cargar Archivos TCX")

# Display history stats
history_stats = get_history_stats()
if history_stats['total_runs'] > 0:
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("📚 Entrenamientos en Historial", history_stats['total_runs'])
    with col_info2:
        if history_stats['date_range']:
            earliest = history_stats['date_range']['earliest'].strftime('%d/%m/%Y')
            st.metric("📅 Primera Sesión", earliest)
    with col_info3:
        if history_stats['date_range']:
            latest = history_stats['date_range']['latest'].strftime('%d/%m/%Y')
            st.metric("🏃 Última Sesión", latest)
    
    # Export/Import section
    st.markdown("---")
    st.markdown("### 💾 Gestión de Datos")
    
    col_export, col_import = st.columns(2)
    
    with col_export:
        # Download history as JSON
        if st.session_state.runs:
            import json
            # Prepare data for export (exclude heavy data_dict to reduce size)
            export_data = []
            for run in st.session_state.runs:
                run_export = {k: v for k, v in run.items() if k != 'data'}
                # Also exclude data_dict if present (very large)
                if 'data_dict' in run_export:
                    del run_export['data_dict']
                export_data.append(run_export)
            
            json_str = json.dumps(export_data, indent=2, default=str)
            
            st.download_button(
                label="📥 Descargar Historial",
                data=json_str,
                file_name=f"mi_historial_running_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                help="Descarga tu historial como JSON. Guarda este archivo para restaurar tus datos más tarde.",
                use_container_width=True
            )
        else:
            st.info("No hay historial para descargar")
    
    with col_import:
        # Upload history JSON
        uploaded_json = st.file_uploader(
            "📤 Cargar Historial",
            type=['json'],
            help="Sube un archivo JSON de historial previamente descargado",
            key="json_uploader"
        )
        
        if uploaded_json:
            try:
                import json
                imported_data = json.load(uploaded_json)
                
                if isinstance(imported_data, list) and len(imported_data) > 0:
                    # Validate structure
                    if 'metrics' in imported_data[0] and 'start_time' in imported_data[0]:
                        # Convert to proper format and add empty data DataFrame
                        for run in imported_data:
                            if 'data' not in run:
                                run['data'] = pd.DataFrame()
                        
                        col_add, col_replace = st.columns(2)
                        with col_add:
                            if st.button("➕ Añadir", key="add_json", use_container_width=True):
                                st.session_state.runs = merge_runs(st.session_state.runs, imported_data)
                                save_runs_history(st.session_state.runs)
                                st.success(f"✅ Añadidos {len(imported_data)} entrenamientos")
                                st.rerun()
                        with col_replace:
                            if st.button("🔄 Reemplazar", key="replace_json", use_container_width=True):
                                st.session_state.runs = imported_data
                                save_runs_history(st.session_state.runs)
                                st.success(f"✅ Cargados {len(imported_data)} entrenamientos")
                                st.rerun()
                    else:
                        st.error("❌ Formato de JSON no válido")
                else:
                    st.error("❌ El archivo no contiene datos válidos")
            except Exception as e:
                st.error(f"❌ Error al leer JSON: {str(e)}")
    
    st.markdown("---")
    
    # Clear history button
    if st.button("🗑️ Limpiar Historial", help="Eliminar todos los datos guardados"):
        if clear_history():
            st.session_state.runs = []
            st.session_state.runs_df = None
            st.session_state.trimp_calculated = False # Reset cache
            st.session_state.metrics_calculated = False # Reset cache
            st.success("✅ Historial limpiado exitosamente")
            st.rerun()

st.markdown("### 📁 Cargar Nuevos Entrenamientos")
uploaded_files = st.file_uploader(
    "Arrastra y suelta tus archivos .tcx aquí",
    type=['tcx'],
    accept_multiple_files=True,
    help="Sube uno o varios archivos TCX de tus entrenamientos"
)

if uploaded_files:
    # Show file counter
    st.info(f"📂 **{len(uploaded_files)} archivo(s) seleccionado(s)**")
    
    # Add or replace mode
    col1, col2 = st.columns(2)
    with col1:
        add_mode = st.button("➕ Añadir al Historial", type="primary", use_container_width=True,
                            help="Añadir estos archivos a tu historial existente")
    with col2:
        replace_mode = st.button("🔄 Reemplazar Todo", use_container_width=True,
                                help="Borrar historial y cargar solo estos archivos")
    
    if add_mode or replace_mode:
        # Progress bar
        progress_text = "Procesando archivos TCX..."
        progress_bar = st.progress(0, text=progress_text)
        
        # Parse TCX files with progress
        new_runs = []
        for i, uploaded_file in enumerate(uploaded_files):
            progress_bar.progress((i) / len(uploaded_files), 
                                text=f"Procesando {uploaded_file.name}... ({i+1}/{len(uploaded_files)})")
            
            # Parse single file
            parsed = parse_tcx_files([uploaded_file])
            if parsed:
                new_runs.extend(parsed)
        
        progress_bar.progress(1.0, text="Calculando métricas...")
        
        if new_runs:
            # Calculate metrics for each run
            classifier = SessionClassifier()
            
            for run in new_runs:
                df = run['data']
                metrics_calculator = RunningMetrics(df)
                run['metrics'] = metrics_calculator.calculate_all_metrics()
                
                # Add training intelligence
                # Classify session type
                run['session_type'] = classifier.classify(run)
                run['session_info'] = classifier.get_session_info(run['session_type'])
                
                # Analyze HR zones if HR data available
                if 'heart_rate' in df.columns and not df['heart_rate'].dropna().empty:
                    hr_analyzer = HRZones()
                    run['hr_zones'] = hr_analyzer.analyze_distribution(df['heart_rate'])
                    run['max_hr_estimated'] = hr_analyzer.max_hr
                else:
                    run['hr_zones'] = {}
                    run['max_hr_estimated'] = None
                
                # Calculate training load
                # Calculate training load
                # Use a default max_hr of 185 if no history, or update later
                # ideally we should use the user's max HR. For now, we'll use a safe default 
                # and then update if we find a higher one in the history.
                current_max_hr = 185
                if run.get('max_hr_estimated') and run['max_hr_estimated'] > current_max_hr:
                    current_max_hr = run['max_hr_estimated']
                
                run['training_load'] = calculate_session_load(run, max_hr=current_max_hr)
            
            # Merge or replace based on user choice
            if add_mode:
                st.session_state.runs = merge_runs(st.session_state.runs, new_runs)
            else:  # replace_mode
                st.session_state.runs = new_runs
            
            # Recalculate TRIMP for ALL runs using the global Max HR
            # This ensures consistent load calculation across history
            all_max_hrs = [r.get('max_hr_estimated', 0) for r in st.session_state.runs if r.get('max_hr_estimated')]
            global_max_hr = max(all_max_hrs) if all_max_hrs else 185
            # Enforce a minimum reasonable Max HR to avoid inflation
            if global_max_hr < 170: 
                global_max_hr = 185
            
            for run in st.session_state.runs:
                run['training_load'] = calculate_session_load(run, max_hr=global_max_hr)
            
            
            # Save to disk
            st.session_state.trimp_calculated = True # Mark as calculated after processing new files
            st.session_state.metrics_calculated = True # Mark as calculated
            if save_runs_history(st.session_state.runs):
                # Create summary DataFrame
                summary_data = []
                for run in st.session_state.runs:
                    metrics = run['metrics']
                    summary_data.append({
                        'filename': run['filename'],
                        'start_time': run['start_time'],
                        'distance_km': metrics['distance_km'],
                        'duration_minutes': metrics['duration_minutes'],
                        'pace_min_per_km': metrics['pace_min_per_km'],
                        'elevation_gain': metrics['elevation_gain'],
                        'gap_pace_min_per_km': metrics['gap_pace_min_per_km'],
                        'avg_heart_rate': metrics['avg_heart_rate'],
                        'max_heart_rate': metrics['max_heart_rate'],
                        'avg_cadence': metrics['avg_cadence'],
                        'efficiency_index': metrics['efficiency_index'],
                        'gap_efficiency_index': metrics['gap_efficiency_index']
                    })
                
                st.session_state.runs_df = pd.DataFrame(summary_data)
                
                progress_bar.empty()
                
                # Success message
                if add_mode:
                    st.success(f"✅ {len(new_runs)} entrenamientos añadidos. Total: {len(st.session_state.runs)}")
                else:
                    st.success(f"✅ {len(new_runs)} entrenamientos cargados y guardados exitosamente!")
                
                # Auto-scroll to summary
                st.markdown(
                    '<script>setTimeout(function(){document.getElementById("resumen-general").scrollIntoView({behavior: "smooth"});}, 500);</script>',
                    unsafe_allow_html=True
                )
            else:
                st.error("⚠️ Archivos procesados pero hubo un error al guardar el historial")
        else:
            progress_bar.empty()
            st.error("❌ No se pudieron procesar los archivos. Verifica que sean archivos TCX válidos.")


# Main dashboard (only show if data is loaded)
if st.session_state.runs:

    st.markdown("---")
    
    # Overview Section - KPI Cards (with anchor for auto-scroll)
    st.markdown('<div id="resumen-general"></div>', unsafe_allow_html=True)
    st.markdown("## 📊 Resumen General")
    
    runs_df = st.session_state.runs_df
    
    # Calculate overview metrics
    total_km = runs_df['distance_km'].sum()
    total_runs = len(runs_df)
    best_pace = runs_df['pace_min_per_km'].min()
    best_ei = runs_df['efficiency_index'].max() if runs_df['efficiency_index'].notna().any() else None
    max_hr = runs_df['max_heart_rate'].max() if runs_df['max_heart_rate'].notna().any() else None
    
    # Display KPI cards in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            create_kpi_card_html(
                "Total Kilómetros",
                f"{total_km:.1f} km",
                f"{total_runs} entrenamientos",
                "🏃"
            ),
            unsafe_allow_html=True
        )
        st.markdown("<p style='color: #B0B0B0; font-size: 0.85rem; margin-top: 0.5rem;'>💡 El volumen total es la base del progreso. Intenta aumentar 10% por semana máximo.</p>", unsafe_allow_html=True)
        
        st.markdown(
            create_kpi_card_html(
                "Mejor Ritmo",
                format_pace(best_pace),
                "min/km",
                "⚡"
            ),
            unsafe_allow_html=True
        )
        st.markdown("<p style='color: #B0B0B0; font-size: 0.85rem; margin-top: 0.5rem;'>📊 Tu mejor ritmo indica tu velocidad pura. Mejóralo con intervalos y tempo runs.</p>", unsafe_allow_html=True)
    
    with col2:
        if best_ei:
            st.markdown(
                create_kpi_card_html(
                    "Mejor Efficiency Index",
                    f"{best_ei:.3f}",
                    "m/min/bpm",
                    "💎"
                ),
                unsafe_allow_html=True
            )
            st.markdown("<p style='color: #B0B0B0; font-size: 0.85rem; margin-top: 0.5rem;'>❤️ Mayor EI = tu corazón trabaja menos al mismo ritmo. Se mejora con Z2 (rodajes fáciles).</p>", unsafe_allow_html=True)
        
        if max_hr:
            st.markdown(
                create_kpi_card_html(
                    "Frecuencia Cardíaca Máxima",
                    f"{int(max_hr)} bpm",
                    "Pico registrado",
                    "❤️"
                ),
                unsafe_allow_html=True
            )
            st.markdown("<p style='color: #B0B0B0; font-size: 0.85rem; margin-top: 0.5rem;'>📈 Sirve para calcular tus zonas de entrenamiento (Z1-Z5).</p>", unsafe_allow_html=True)
    
    # Help section for metrics
    with st.expander("❓ ¿Qué significan estas métricas?"):
        col_help1, col_help2 = st.columns(2)
        
        with col_help1:
            st.markdown(create_metric_tooltip('efficiency_index'), unsafe_allow_html=True)
            st.markdown(create_metric_tooltip('cadence'), unsafe_allow_html=True)
        
        with col_help2:
            st.markdown(create_metric_tooltip('gap'), unsafe_allow_html=True)
            st.markdown(create_metric_tooltip('heart_rate_zones'), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Training Intelligence Section
    st.markdown("## 🎯 Inteligencia de Entrenamiento")
    
    # Calculate session type distribution
    session_types = {}
    hr_zones_aggregate = {'Z1': 0, 'Z2': 0, 'Z3': 0, 'Z4': 0, 'Z5': 0}
    total_load = 0
    
    for run in st.session_state.runs:
        # Session types
        session_type = run.get('session_type', 'unknown')
        session_info = run.get('session_info', {})
        session_name = session_info.get('name', 'Desconocido')
        
        if session_name not in session_types:
            session_types[session_name] = {
                'count': 0,
                'emoji': session_info.get('emoji', '❓'),
                'color': session_info.get('color', '#808080')
            }
        session_types[session_name]['count'] += 1
        
        # HR zones aggregate
        hr_zones = run.get('hr_zones', {})
        for zone_id, zone_data in hr_zones.items():
            if zone_id in hr_zones_aggregate:
                hr_zones_aggregate[zone_id] += zone_data.get('percentage', 0)
        
        # Training load
        training_load = run.get('training_load', {})
        total_load += training_load.get('trimp', 0)
    
    col_int1, col_int2 = st.columns(2)
    
    with col_int1:
        st.markdown("### 🏃 Distribución de Sesiones")
        
        if session_types:
            import plotly.graph_objects as go
            
            # Create pie chart for session types
            labels = [f"{info['emoji']} {name}" for name, info in session_types.items()]
            values = [info['count'] for info in session_types.values()]
            colors = [info['color'] for info in session_types.values()]
            
            fig_sessions = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker=dict(colors=colors),
                hole=0.3,
                textinfo='label+percent',
                textfont=dict(color='white')
            )])
            
            fig_sessions.update_layout(
                paper_bgcolor=COLORS['bg_dark'],
                plot_bgcolor=COLORS['bg_card'],
                font=dict(color=COLORS['text']),
                height=350,
                showlegend=False,
                legend=dict(
                    font=dict(color='#FFFFFF', size=12),
                    bgcolor='rgba(26, 31, 53, 0.95)',
                    bordercolor='#FFFFFF',
                    borderwidth=1
                )
            )
            
            st.plotly_chart(fig_sessions, use_container_width=True)
        else:
            st.info("No hay información de tipos de sesión")
    
    with col_int2:
        st.markdown("### ❤️ Zonas de Frecuencia Cardíaca")
        
        # Check if we have any HR data
        has_hr_data = any(run.get('hr_zones') for run in st.session_state.runs)
        
        if has_hr_data:
            import plotly.graph_objects as go
            
            # Normalize percentages
            total_hr = sum(hr_zones_aggregate.values())
            if total_hr > 0:
                hr_zones_normalized = {
                    zone: (value / len(st.session_state.runs)) 
                    for zone, value in hr_zones_aggregate.items()
                }
            else:
                hr_zones_normalized = hr_zones_aggregate
            
            # Create bar chart for HR zones
            zone_colors = {
                'Z1': '#00FF7F',
                'Z2': '#00BFFF',
                'Z3': '#FFD700',
                'Z4': '#FFA500',
                'Z5': '#FF4444'
            }
            
            fig_zones = go.Figure(data=[go.Bar(
                x=list(hr_zones_normalized.keys()),
                y=list(hr_zones_normalized.values()),
                marker=dict(color=[zone_colors[z] for z in hr_zones_normalized.keys()]),
                text=[f"{v:.1f}%" for v in hr_zones_normalized.values()],
                textposition='auto',
            )])
            
            fig_zones.update_layout(
                xaxis_title="Zona",
                yaxis_title="Tiempo Promedio (%)",
                paper_bgcolor=COLORS['bg_dark'],
                plot_bgcolor=COLORS['bg_card'],
                font=dict(color=COLORS['text']),
                height=350,
                showlegend=False,
                legend=dict(
                    font=dict(color='#FFFFFF', size=12),
                    bgcolor='rgba(26, 31, 53, 0.95)',
                    bordercolor='#FFFFFF',
                    borderwidth=1
                )
            )
            
            st.plotly_chart(fig_zones, use_container_width=True)
        else:
            st.info("No hay datos de frecuencia cardíaca disponibles")
    
    # Training Load Summary - Now with ACTIONABLE metrics
    st.markdown("### 💪 Carga de Entrenamiento")
    
    # Calculate Acute (7 days) and Chronic (28 days / 4 weeks) loads
    from datetime import timedelta
    now = pd.Timestamp.now()  # Use pandas Timestamp for compatibility
    
    def get_days_ago(run_start_time):
        """Safely calculate days since run, handling timezone differences"""
        try:
            start = pd.Timestamp(run_start_time)
            # Make both timezone-naive for comparison
            if start.tz is not None:
                start = start.tz_localize(None)
            now_naive = pd.Timestamp.now()
            return (now_naive - start).days
        except:
            return 9999  # Exclude if can't calculate
    
    acute_window = [r for r in st.session_state.runs 
                    if r.get('start_time') and get_days_ago(r['start_time']) <= 7]
    chronic_window = [r for r in st.session_state.runs 
                      if r.get('start_time') and get_days_ago(r['start_time']) <= 28]
    
    acute_load = sum(r.get('training_load', {}).get('trimp', 0) for r in acute_window)
    chronic_load = sum(r.get('training_load', {}).get('trimp', 0) for r in chronic_window)
    
    # Chronic load is weekly average over 4 weeks
    chronic_weekly_avg = chronic_load / 4 if chronic_load > 0 else 0
    
    # Calculate ratio (Acute / Chronic weekly average)
    ratio = acute_load / chronic_weekly_avg if chronic_weekly_avg > 0 else 0
    
    if acute_load > 0 or chronic_load > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Carga Aguda (7 días)", 
                f"{int(acute_load)}", 
                delta=f"{len(acute_window)} sesiones",
                help="TRIMP acumulado en los últimos 7 días. Indica tu fatiga reciente."
            )
        
        with col2:
            st.metric(
                "Carga Crónica (semanal)", 
                f"{int(chronic_weekly_avg)}", 
                delta=f"Promedio 4 semanas",
                help="Promedio semanal de TRIMP de las últimas 4 semanas. Indica tu 'fitness' base."
            )
        
        with col3:
            # Color-code the ratio
            if 0.8 <= ratio <= 1.3:
                ratio_status = "✅ Óptimo"
                ratio_color = "normal"
            elif ratio > 1.5:
                ratio_status = "🔴 Alto riesgo"
                ratio_color = "inverse"
            elif ratio > 1.3:
                ratio_status = "🟡 Cuidado"
                ratio_color = "off"
            else:
                ratio_status = "🔵 Bajo"
                ratio_color = "off"
            
            st.metric(
                "Ratio Aguda/Crónica", 
                f"{ratio:.2f}",
                delta=ratio_status,
                delta_color=ratio_color,
                help="0.8-1.3 = zona óptima de progreso. >1.5 = riesgo de lesión. <0.8 = desentrenamiento."
            )
        
        # Actionable interpretation
        if ratio > 1.5:
            st.warning("⚠️ Tu ratio está alto. Has aumentado la carga demasiado rápido. Considera reducir volumen o intensidad esta semana.")
        elif ratio > 1.3:
            st.info("📈 Estás en fase de sobrecarga controlada. Monitoriza cómo te sientes y no aumentes más esta semana.")
        elif 0.8 <= ratio <= 1.3:
            st.success("👍 Estás en la zona óptima de progreso. Tu cuerpo se está adaptando bien.")
        elif ratio < 0.8 and ratio > 0:
            st.info("📉 Tu carga reciente es baja respecto a tu fitness. Puedes aumentar volumen gradualmente.")
    else:
        st.info("ℹ️ No hay datos suficientes de Frecuencia Cardíaca para calcular la carga. Asegúrate de subir archivos TCX con datos de pulsaciones.")
    
    # Updated Glossary - now matches what's displayed
    with st.expander("📖 ¿Qué significan estos términos?"):
        st.markdown("""  
        **📊 Métricas de Carga (las que ves arriba):**
        
        - **Carga Aguda**: TRIMP total de los últimos 7 días. Refleja tu fatiga reciente.
        - **Carga Crónica**: Promedio semanal de TRIMP de las últimas 4 semanas. Refleja tu "fitness" o capacidad de trabajo.
        - **Ratio Aguda/Crónica**: La métrica clave para prevenir lesiones:
          - **0.8-1.3** = Zona óptima: estás progresando de forma segura
          - **>1.3** = Sobrecarga: estás aumentando más rápido de lo recomendado
          - **>1.5** = Peligro: riesgo significativo de lesión
          - **<0.8** = Desentrenamiento: podrías aumentar la carga
        
        **🏃 Tipos de Entrenamiento:**
        
        - **Tempo Run**: Ritmo "cómodamente duro" 20-40 min.
        - **Umbral**: El ritmo más rápido que puedes mantener ~1 hora.
        - **Fartlek**: Alternas ritmos rápidos/lentos sin estructura fija.
        - **Intervalos**: Repeticiones a alta intensidad con recuperación.
        
        **❤️ Zonas FC:**
        
        - **Z1-Z2** (fácil): Resistencia base. 80% de tu volumen aquí.
        - **Z3** (tempo): Ritmo sostenido.
        - **Z4** (umbral): Duro pero controlado.
        - **Z5** (VO2max): Esfuerzo máximo, solo intervalos cortos.
        """)
    
    st.markdown("---")
    
    # Evolution Charts
    st.markdown("## 📈 Evolución Temporal")
    
    tab1, tab2, tab3 = st.tabs(["Efficiency Index", "Ritmo", "GAP vs Ritmo Normal"])
    
    with tab1:
        if runs_df['efficiency_index'].notna().any():
            fig_ei = create_evolution_chart(
                runs_df[runs_df['efficiency_index'].notna()],
                'efficiency_index',
                'Efficiency Index'
            )
            # Add trend line to show visual progression
            clean_df = runs_df[runs_df['efficiency_index'].notna()]
            fig_ei = add_trend_line(fig_ei, clean_df['start_time'].tolist(), clean_df['efficiency_index'].tolist())
            st.plotly_chart(fig_ei, use_container_width=True)
        else:
            st.info("No hay datos de pulsaciones disponibles para calcular el Efficiency Index")
    
    with tab2:
        fig_pace = create_evolution_chart(runs_df, 'pace_min_per_km', 'Ritmo (min/km)')
        # Add trend line to show visual progression
        fig_pace = add_trend_line(fig_pace, runs_df['start_time'].tolist(), runs_df['pace_min_per_km'].tolist())
        st.plotly_chart(fig_pace, use_container_width=True)
    
    with tab3:
        # Compare GAP pace vs normal pace
        comparison_df = runs_df[['start_time', 'pace_min_per_km', 'gap_pace_min_per_km']].copy()
        
        import plotly.graph_objects as go
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=comparison_df['start_time'],
            y=comparison_df['pace_min_per_km'],
            mode='lines+markers',
            name='Ritmo Normal',
            line=dict(color=COLORS['cyan'], width=2),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=comparison_df['start_time'],
            y=comparison_df['gap_pace_min_per_km'],
            mode='lines+markers',
            name='GAP (Ajustado por Desnivel)',
            line=dict(color=COLORS['lime'], width=2),
            marker=dict(size=8)
        ))
        
        # Add trend line for Normal Pace (cyan dashed)
        # fig = add_trend_line(fig, comparison_df['start_time'].tolist(), comparison_df['pace_min_per_km'].tolist())
        
        # Manual trend line for Normal Pace to enforce Cyan color
        x_numeric_pace = list(range(len(comparison_df['pace_min_per_km'])))
        z_pace = np.polyfit(x_numeric_pace, comparison_df['pace_min_per_km'].tolist(), 1)
        p_pace = np.poly1d(z_pace)
        trend_y_pace = [p_pace(x) for x in x_numeric_pace]
        
        fig.add_trace(go.Scatter(
            x=comparison_df['start_time'],
            y=trend_y_pace,
            mode='lines',
            name=f'Tendencia Ritmo ({z_pace[0]:+.3f}/sesión)',
            line=dict(dash='dash', color='rgba(0, 255, 255, 0.6)', width=2),
            hovertemplate=f'Tendencia Ritmo<extra></extra>'
        ))
        
        # Add trend line for GAP (lime dashed) 
        import numpy as np
        x_numeric = list(range(len(comparison_df['gap_pace_min_per_km'])))
        z = np.polyfit(x_numeric, comparison_df['gap_pace_min_per_km'].tolist(), 1)
        p = np.poly1d(z)
        trend_y_gap = [p(x) for x in x_numeric]
        
        fig.add_trace(go.Scatter(
            x=comparison_df['start_time'],
            y=trend_y_gap,
            mode='lines',
            name=f'Tendencia GAP ({z[0]:+.3f}/sesión)',
            line=dict(dash='dash', color='rgba(127, 255, 0, 0.6)', width=2),
            hovertemplate=f'Tendencia GAP<extra></extra>'
        ))
        
        fig.update_layout(
            title="Comparación: Ritmo vs GAP",
            xaxis_title="Fecha",
            yaxis_title="Ritmo (min/km)",
            paper_bgcolor=COLORS['bg_dark'],
            plot_bgcolor=COLORS['bg_card'],
            font=dict(color=COLORS['text']),
            hovermode='x unified',
            height=400,
            legend=dict(
                font=dict(color='#FFFFFF', size=12),  # Leyenda en blanco
                bgcolor='rgba(26, 31, 53, 0.95)',  # Fondo oscuro sólido para mejor visibilidad
                bordercolor='#FFFFFF',
                borderwidth=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add explanation
        st.markdown('''
        <p style='color: #B0B0B0; font-size: 0.9rem;'><strong>💡 Interpretación:</strong></p>
        <ul style='color: #B0B0B0; font-size: 0.85rem;'>
            <li>Si la <span style='color: #7FFF00;'>línea GAP</span> mejora más rápido que <span style='color: #00FFFF;'>Ritmo Normal</span> → Estás mejorando en subidas/terreno técnico</li>
            <li>Si ambas mejoran similar → Mejora general balanceada</li>
            <li>Una diferencia grande entre líneas → Entrenas en terreno muy desnivelado</li>
        </ul>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Biomechanics Analysis
    st.markdown("## 🔬 Análisis Biomecánico")
    st.markdown("<p style='color: #B0B0B0; font-size: 0.9rem;'>Esta gráfica muestra la relación entre tu <strong>cadencia</strong> (pasos por minuto) y tu <strong>ritmo</strong>. Una buena técnica mantiene cadencia alta (170-190 spm) incluso a ritmos lentos.</p>", unsafe_allow_html=True)
    
    
    fig_scatter = create_cadence_pace_scatter(runs_df)
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.markdown("<p style='color: #B0B0B0; font-size: 0.85rem;'><strong>💡 Qué buscar:</strong> Puntos más arriba = mejor (más cadencia). Si tus puntos están dispersos, considera trabajar en mantener cadencia más constante.</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
   # Personal Records
    st.markdown("## 🏆 Récords Personales")
    st.markdown("<p style='color: #B0B0B0; font-size: 0.9rem;'>Tus mejores tiempos en distancias estándar. 💡 Compite contra ti mismo, no contra otros.</p>", unsafe_allow_html=True)
    
    pr_detector = PersonalRecords(st.session_state.runs)
    pbs = pr_detector.detect_pbs()
    
    if pbs:
        # Wrap in container with max width to prevent stretching
        st.markdown("<div style='max-width: 1000px; margin: 0 auto;'>", unsafe_allow_html=True)
        
        # Organize in rows to show all distances nicely
        st.markdown("### 🏃 Distancias Cortas (1K - 5K)")
        short_dist = {k: v for k, v in pbs.items() if k in ['1K', '3K', '5K']}
        if short_dist:
            # Create fixed-width columns with spacers
            cols = st.columns(3) # Use 3 columns for better spacing
            for idx, (distance, pb_data) in enumerate(short_dist.items()):
                with cols[idx % 3]:
                    st.markdown(f"<div style='background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; text-align: center;'>", unsafe_allow_html=True)
                    st.markdown(f"#### {distance}")
                    st.metric("Ritmo", format_pace(pb_data['pace']))
                    st.metric("Tiempo", format_duration(pb_data['duration']))
                    st.markdown(f"<p style='color: #B0B0B0; font-size: 0.8rem;'>📅 {pb_data['date'].strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("### 🏃 Distancias Medias/Largas (10K - Marathon)")
        long_dist = {k: v for k, v in pbs.items() if k in ['10K', '15K', '21K', '42K']}
        if long_dist:
            # Create fixed-width columns with spacers
            cols = st.columns(3)
            for idx, (distance, pb_data) in enumerate(long_dist.items()):
                with cols[idx % 3]:
                    st.markdown(f"<div style='background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; text-align: center;'>", unsafe_allow_html=True)
                    st.markdown(f"#### {distance}")
                    st.metric("Ritmo", format_pace(pb_data['pace']))
                    st.metric("Tiempo", format_duration(pb_data['duration']))
                    st.markdown(f"<p style='color: #B0B0B0; font-size: 0.8rem;'>📅 {pb_data['date'].strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("ℹ️ No se detectaron récords. Sube más entrenamientos o asegúrate de completar distancias estándar (1K, 3K, 5K, 10K, 15K, 21K, 42K)")
    
    st.markdown("---")
    
    # Virtual Coach Section
    st.markdown("## 🧠 Tu Coach Virtual")
    st.markdown("*Recomendaciones personalizadas basadas en tus datos*")

    # Generate coaching insights  
    coach = VirtualCoach(st.session_state.runs)
    all_insights = coach.generate_all_insights()
    summary_stats = coach.get_summary_stats()
    
    # Create tabs
    tab_week, tab_month, tab_long = st.tabs([
        "📅 Esta Semana",
        "📊 Este Mes",
        "📈 Tendencia General"
    ])
    
    # Helper function for cards
    def display_insight_card(insight):
        severity_colors = {
            'success': '#00FF7F',
            'info': '#00BFFF',
            'warning': '#FFA500',
            'error': '#FF4444'
        }
        border_color = severity_colors.get(insight.severity, '#00BFFF')
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(0, 255, 255, 0.1) 0%, rgba(0, 200, 255, 0.05) 100%);
                    border-left: 4px solid {border_color}; border-radius: 8px; padding: 1.2rem; margin: 1rem 0;">
            <span style="color: #00FFFF; font-weight: 600;">{insight.category}</span>
            <h4 style="margin: 0.5rem 0; color: #FFF;">{insight.title}</h4>
            <p style="margin: 0; color: #B0B0B0;">{insight.message}</p>
        </div>
        """, unsafe_allow_html=True)

    with tab_week:
        st.markdown("### 📅 Análisis Semanal")
        weekly_stats = summary_stats.get('weekly', {})
        if weekly_stats:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Sesiones", weekly_stats.get('total_runs', 0))
            with col2:
                st.metric("Kilómetros", f"{weekly_stats.get('total_km', 0):.1f} km")
            with col3:
                st.metric("Horas", f"{weekly_stats.get('total_time_hours', 0):.1f} h")
            with col4:
                trimp_value = int(weekly_stats.get('total_load', 0))
                st.metric("TRIMP", f"{trimp_value}")
                st.markdown("<p style='color: #888; font-size: 0.7rem;'>Carga de entrenamiento</p>", unsafe_allow_html=True)
        
        for insight in all_insights.get('short_term', []):
            display_insight_card(insight)

    with tab_month:
        st.markdown("### 📋 Análisis Mensual")
        st.markdown("<p style='color: #B0B0B0; font-size: 0.85rem;'>Comparación: últimas 2 semanas vs 2 semanas anteriores</p>", unsafe_allow_html=True)
        monthly_prog = summary_stats.get('monthly_progression', {})
        if not monthly_prog.get('insufficient_data'):
            col1, col2 = st.columns(2)
            with col1:
                ei_trend = monthly_prog.get('efficiency_trend', 'stable')
                ei_change = monthly_prog.get('ei_change_pct', 0)
                # Translate trend
                trend_es = {'improving': 'Mejorando', 'declining': 'Declinando', 'stable': 'Estable'}.get(ei_trend, ei_trend.title())
                st.metric("Efficiency Index", trend_es, f"{ei_change:+.1f}%")
                st.markdown("<p style='color: #888; font-size: 0.7rem;'>% cambio últimas 2 vs 2 anteriores</p>", unsafe_allow_html=True)
            with col2:
                pace_trend = monthly_prog.get('pace_trend', 'stable')
                pace_change = monthly_prog.get('pace_change_pct', 0)
                trend_es = {'improving': 'Mejorando', 'declining': 'Declinando', 'stable': 'Estable'}.get(pace_trend, pace_trend.title())
                st.metric("Ritmo", trend_es, f"{pace_change:+.1f}%")
        
        for insight in all_insights.get('medium_term', []):
            display_insight_card(insight)

    with tab_long:
        st.markdown("### 🎯 Progreso a Largo Plazo")
        annual_stats = summary_stats.get('annual', {})
        if not annual_stats.get('insufficient_data'):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Meses activos", annual_stats.get('total_months', 0))
            with col2:
                st.metric("Km acumulados", f"{annual_stats.get('total_km_period', 0):.0f} km")
        
        for insight in all_insights.get('long_term', []):
            display_insight_card(insight)
    
    st.markdown("---")
    
    # AI-Powered Complete Analysis
    st.markdown("## 🤖 Informe Completo con IA")
    st.markdown("<p style='color: #B0B0B0; font-size: 0.9rem;'>Análisis personalizado generado por IA basado en TODOS tus datos</p>", unsafe_allow_html=True)
    
    # Check for API key
    api_key = None
    try:
        api_key = st.secrets.get("groq", {}).get("api_key")
    except:
        pass
    
    if not api_key:
        st.warning("⚠️ API Key de Groq no configurada. Configúrala en `.streamlit/secrets.toml`")
        with st.expander("📖 Cómo obtener tu API Key gratuita"):
            st.markdown("""
            1. Ve a [Groq Console](https://console.groq.com/keys)
            2. Crea una cuenta o inicia sesión
            3. Haz clic en "Create API Key"
            4. Copia la clave y añádela a `.streamlit/secrets.toml`:
            ```toml
            [groq]
            api_key = "TU_API_KEY_AQUI"
            ```
            5. Reinicia la app
            """)
    else:
        # Personalization form
        st.markdown("### ⚙️ Personaliza tu Plan")
        st.markdown("<p style='color: #B0B0B0; font-size: 0.85rem;'>Ajusta estos parámetros para un plan adaptado a tu situación</p>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            running_days = st.slider(
                "🏃 Días de running por semana",
                min_value=2,
                max_value=6,
                value=4,
                help="¿Cuántos días puedes dedicar exclusivamente a correr?"
            )
            
            other_sports = st.selectbox(
                "💪 ¿Haces otros deportes/actividades?",
                options=[
                    "No, solo running",
                    "Sí, fuerza/gimnasio 1-2 días",
                    "Sí, fuerza/gimnasio 3+ días",
                    "Sí, otros deportes (ciclismo, natación, etc.)"
                ],
                help="Esto afecta la carga total de entrenamiento recomendada"
            )
        
        with col2:
            experience_level = st.selectbox(
                "📊 Tu nivel de experiencia",
                options=[
                    "Principiante (< 1 año corriendo)",
                    "Intermedio (1-3 años)",
                    "Avanzado (> 3 años)"
                ],
                index=1,
                help="Esto ajusta la complejidad de los entrenamientos"
            )
            
            main_goal = st.selectbox(
                "🎯 Objetivo principal",
                options=[
                    "Mejorar ritmo/velocidad",
                    "Aumentar distancia/resistencia",
                    "Preparar una carrera específica",
                    "Mantener forma física",
                    "Perder peso/salud general"
                ],
                help="El plan se enfocará en este objetivo"
            )
        
        # Store user preferences
        user_prefs = {
            'running_days': running_days,
            'other_sports': other_sports,
            'experience_level': experience_level,
            'main_goal': main_goal
        }
        
        st.markdown("---")
        
        # Generate button
        col_btn, col_info = st.columns([1, 3])
        with col_btn:
            generate_btn = st.button("🚀 Generar Análisis", type="primary", use_container_width=True)
        with col_info:
            st.markdown("<p style='color: #888; font-size: 0.8rem; margin-top: 0.5rem;'>Análisis personalizado con IA (~10 segundos)</p>", unsafe_allow_html=True)
        
        if generate_btn:
            with st.spinner("🤖 Analizando tus datos con IA..."):
                try:
                    from utils.ai_analyzer import AIRunningAnalyzer
                    
                    # Initialize analyzer
                    analyzer = AIRunningAnalyzer(api_key)
                    
                    # Prepare context with user preferences
                    context = analyzer.prepare_context(st.session_state.runs, runs_df, user_prefs)
                    
                    # Generate analysis (not cached since preferences may change)
                    analysis = analyzer.generate_analysis(context)
                    
                    # Store in session state
                    st.session_state['ai_analysis'] = analysis
                    st.session_state['ai_analysis_time'] = pd.Timestamp.now()
                    st.session_state['ai_analysis_prefs'] = user_prefs
                    
                except Exception as e:
                    st.error(f"❌ Error al generar análisis: {str(e)}")
                    st.session_state['ai_analysis'] = None
        
        # Display analysis if available
        if 'ai_analysis' in st.session_state and st.session_state['ai_analysis']:
            # Show when it was generated
            if 'ai_analysis_time' in st.session_state:
                gen_time = st.session_state['ai_analysis_time']
                st.caption(f"Generado: {gen_time.strftime('%d/%m/%Y %H:%M')}")
            
            # Display the analysis
            st.markdown(st.session_state['ai_analysis'])
            
            # Refresh button
            if st.button("🔄 Regenerar Análisis"):
                del st.session_state['ai_analysis']
                st.rerun()
    
    st.markdown("---")
    
    # Specialized Analysis Section
    st.markdown("## 🔬 Análisis Especializados")
    
    # Create tabs for different specialized analyses
    tab_terrain, tab_biomech, tab_cardio, tab_perf = st.tabs([
        "🏔️ Terreno",
        "👟 Biomecánica", 
        "❤️ Cardiovascular",
        "🏆 Rendimiento"
    ])
    
    with tab_terrain:
        st.markdown("### 🏔️ Análisis de Terreno")
        
        # Classify terrain for all runs
        classify_all_runs(st.session_state.runs)
        
        # Analyze terrain
        terrain_analyzer = TerrainAnalyzer(st.session_state.runs)
        terrain_summary = terrain_analyzer.get_terrain_summary()
        
        # Show distribution
        terrain_dist = terrain_summary.get('distribution', {})
        if terrain_dist:
            col1, col2 = st.columns(2)
            
            with col1:
                # Create pie chart
                import plotly.graph_objects as go
                labels = [f"{info['emoji']} {info['name']}" for info in terrain_dist.values()]
                values = [info['count'] for info in terrain_dist.values()]
                colors = [info['color'] for info in terrain_dist.values()]
                
                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    marker=dict(colors=colors),
                    hole=0.3,
                    textfont=dict(color='#FFFFFF', size=14)  # White text on pie slices
                )])
                fig.update_layout(
                    title="Distribución por Tipo de Terreno",
                    paper_bgcolor='#0E1117',
                    font=dict(color='#FAFAFA'),
                    height=300,
                    legend=dict(
                        font=dict(color='#FFFFFF', size=12),  # White legend text
                        bgcolor='rgba(26, 31, 53, 0.95)',
                        bordercolor='#FFFFFF',
                        borderwidth=1
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### Porcentajes")
                for terrain_type, info in terrain_dist.items():
                    st.metric(
                        f"{info['emoji']} {info['name']}", 
                        f"{info['km_percentage']:.1f}%",
                        f"{info['count']} sesiones"
                    )
        
        # Show recommendations
        recommendations = terrain_summary.get('recommendations', [])
        if recommendations:
            st.markdown("#### 💡 Recomendaciones")
            for rec in recommendations:
                st.markdown(rec)
    
    with tab_biomech:
        st.markdown("### 👟 Análisis Biomecánico")
        
        biomech_analyzer = BiomechanicsAnalyzer(st.session_state.runs)
        biomech_summary = biomech_analyzer.get_biomechanics_summary()
        
        # Show cadence patterns
        cadence_patterns = biomech_summary.get('cadence_patterns', {})
        if cadence_patterns:
            st.markdown("#### Patrones de Cadencia por Ritmo")
            st.markdown("<p style='color: #B0B0B0; font-size: 0.85rem;'>Tu cadencia promedio en diferentes zonas de esfuerzo:</p>", unsafe_allow_html=True)
            st.markdown("<p style='color: #B0B0B0; font-size: 0.8rem;'><strong>Easy</strong>=Fácil | <strong>Moderate</strong>=Moderado | <strong>Hard</strong>=Duro</p>", unsafe_allow_html=True)
            
            for zone_name, zone_data in cadence_patterns.items():
                col1, col2, col3 = st.columns(3)
                with col1:
                    # Translate zone names
                    zone_es = {'easy': 'Fácil', 'moderate': 'Moderado', 'hard': 'Duro'}.get(zone_name, zone_name.title())
                    st.metric("Zona", zone_es)
                with col2:
                    st.metric("Cadencia Promedio", f"{zone_data['avg_cadence']:.0f} spm")
                with col3:
                    if zone_data['optimal']:
                        st.metric("Estado", "✅ Óptimo")
                        st.markdown("<p style='color: #00FF7F; font-size: 0.7rem;'>Cadencia en rango ideal</p>", unsafe_allow_html=True)
                    else:
                        st.metric("Estado", "⚠️ Mejorable")
                        st.markdown("<p style='color: #FFA500; font-size: 0.7rem;'>Considera aumentar cadencia</p>", unsafe_allow_html=True)
        
        # Running economy
        economy = biomech_summary.get('running_economy', {})
        if economy:
            st.markdown("#### Score de Economía")
            score = economy.get('overall_economy_score', 0)
            st.metric("Economía de Carrera", f"{score:.0f}/100")
        
        # Recommendations
        recommendations = biomech_summary.get('recommendations', [])
        if recommendations:
            st.markdown("#### 💡 Recomendaciones")
            for rec in recommendations:
                st.markdown(rec)
    
    with tab_cardio:
        st.markdown("### ❤️ Análisis Cardiovascular")
        st.markdown("<p style='color: #B0B0B0; font-size: 0.85rem;'>Cómo responde tu corazón al esfuerzo prolongado</p>", unsafe_allow_html=True)
        
        cardio_analyzer = CardiovascularAnalyzer(st.session_state.runs)
        cardio_summary = cardio_analyzer.get_cardiovascular_summary()
        
        # Recent session metrics
        recent_drift = cardio_summary.get('recent_drift', {})
        if recent_drift.get('has_data'):
            st.markdown("#### 📊 Deriva Cardíaca")
            st.markdown("<p style='color: #B0B0B0; font-size: 0.8rem;'>Cuánto sube tu FC durante un entrenamiento largo (a mismo ritmo). <strong>Menos deriva = mejor forma física.</strong></p>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                drift_val = recent_drift['drift_pct']
                st.metric("Deriva", f"{drift_val:.1f}%")
            with col2:
                severity = recent_drift['severity']
                severity_es = {'low': 'Baja ✅', 'moderate': 'Moderada ⚠️', 'high': 'Alta 🔴'}.get(severity, severity.title())
                st.metric("Nivel", severity_es)
            with col3:
                st.markdown(f"<p style='color: #B0B0B0; font-size: 0.85rem; margin-top: 1rem;'>{recent_drift['message']}</p>", unsafe_allow_html=True)
        else:
            st.info("📊 No hay datos de FC suficientes para analizar deriva cardíaca")
        
        recent_coupling = cardio_summary.get('recent_coupling', {})
        if recent_coupling.get('has_data'):
            st.markdown("#### 🔗 Acoplamiento FC-Ritmo")
            st.markdown("<p style='color: #B0B0B0; font-size: 0.8rem;'>Relación entre tu FC y tu ritmo. <strong>Ratio bajo = más eficiente.</strong></p>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Ratio", f"{recent_coupling['coupling_ratio']:.2f}")
            with col2:
                eff = recent_coupling['efficiency']
                eff_es = {'excellent': 'Excelente ✅', 'good': 'Bueno ✅', 'average': 'Normal', 'poor': 'Mejorable ⚠️'}.get(eff, eff.title())
                st.metric("Eficiencia", eff_es)
        
        # Insights
        insights = cardio_summary.get('insights', [])
        if insights:
            st.markdown("#### 💡 Insights Cardiovasculares")
            for insight in insights:
                st.info(insight)
    
    with tab_perf:
        st.markdown("### 🏆 Predicciones de Rendimiento")
        st.markdown("<p style='color: #B0B0B0; font-size: 0.85rem;'>Basadas en tus récords personales actuales</p>", unsafe_allow_html=True)
        
        perf_predictor = PerformancePredictor(st.session_state.runs)
        
        # Get predictions
        predictions = perf_predictor.predict_all_distances()
        
        if predictions:
            st.markdown("#### 🎯 Tiempos Predichos")
            
            # Create DataFrame for table
            import pandas as pd
            table_data = []
            for dist, pred in predictions.items():
                table_data.append({
                    'Distancia': dist,
                    'Tiempo Objetivo': pred['time_str'],
                    'Ritmo (min/km)': pred['pace_str']
                })
            
            df_predictions = pd.DataFrame(table_data)
            
            # Display as styled table
            st.markdown("""
            <style>
            .dataframe {
                color: #FAFAFA !important;
            }
            .dataframe th {
                background-color: rgba(0, 255, 255, 0.1) !important;
                color: #00FFFF !important;
                font-weight: bold !important;
            }
            .dataframe td {
                background-color: rgba(255, 255, 255, 0.05) !important;
                color: #FAFAFA !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.dataframe(df_predictions, use_container_width=True, hide_index=True)
            
            # Goal suggestions
            st.markdown("#### 📈 Objetivos Sugeridos")
            st.markdown("<p style='color: #B0B0B0; font-size: 0.85rem;'>Objetivos alcanzables en los próximos 3-6 meses:</p>", unsafe_allow_html=True)
            goals = perf_predictor.suggest_race_goals()
            for goal in goals:
                st.markdown(f"<p style='color: #B0B0B0; font-size: 0.9rem;'>• {goal}</p>", unsafe_allow_html=True)
        else:
            st.info("Necesitas establecer récords personales para generar predicciones")
    
    st.markdown("---")

    # Session Analysis
    st.markdown("## 🗺️ Análisis de Sesión")
    
    # Select a run (sorted by date, most recent first)
    # Runs are already sorted in merge_runs function  
    run_options = [f"{run['start_time'].strftime('%d/%m/%Y %H:%M')} - {run['filename']}'" 
                   for run in st.session_state.runs]
    
    selected_run_idx = st.selectbox(
        "Selecciona un entrenamiento",
        range(len(run_options)),
        format_func=lambda x: run_options[x]
    )
    
    if selected_run_idx is not None:
        selected_run = st.session_state.runs[selected_run_idx]
        metrics = selected_run['metrics']
        df = selected_run['data']
        
        # Display session type and training load
        session_info = selected_run.get('session_info', {})
        training_load = selected_run.get('training_load', {})
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(0, 255, 255, 0.1) 0%, rgba(0, 200, 255, 0.05) 100%); 
                    border-left: 4px solid #00FFFF; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <h3 style="margin: 0; color: #00FFFF;">
                {session_info.get('emoji', '🏃')} {session_info.get('name', 'Sesión')}
            </h3>
            <p style="margin: 0.5rem 0 0 0; color: #B0B0B0;">
                TRIMP: {int(training_load.get('trimp', 0))} | 
                TSS Estimado: {int(training_load.get('tss', 0))}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display session metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Distancia", f"{metrics['distance_km']:.2f} km")
        with col2:
            st.metric("Tiempo", format_duration(metrics['duration_minutes']))
        with col3:
            st.metric("Ritmo", format_pace(metrics['pace_min_per_km']))
        with col4:
            st.metric("Desnivel +", f"{metrics['elevation_gain']:.0f} m")
        
        # Multi-axis chart
        st.markdown("### 📊 Métricas de la Sesión")
        fig_session = create_session_analysis_chart(df)
        st.plotly_chart(fig_session, use_container_width=True)
        
        # Map
        st.markdown("### 🗺️ Ruta")
        
        if 'lat' in df.columns and 'lon' in df.columns and df['lat'].notna().any():
            # Create Folium map
            center_lat = df['lat'].mean()
            center_lon = df['lon'].mean()
            
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=14,
                tiles='OpenStreetMap'
            )
            
            # Add route as polyline
            route_coords = df[['lat', 'lon']].dropna().values.tolist()
            
            folium.PolyLine(
                route_coords,
                color='#00FFFF',
                weight=4,
                opacity=0.8
            ).add_to(m)
            
            # Add start and end markers
            if len(route_coords) > 0:
                folium.Marker(
                    route_coords[0],
                    popup='Inicio',
                    icon=folium.Icon(color='green', icon='play')
                ).add_to(m)
                
                folium.Marker(
                    route_coords[-1],
                    popup='Fin',
                    icon=folium.Icon(color='red', icon='stop')
                ).add_to(m)
            
            folium_static(m, width=1200, height=600)
        else:
            st.info("No hay datos de GPS disponibles para este entrenamiento")

else:
    # Empty state
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem;">
        <h2 style="color: #00FFFF;">👆 Sube tus archivos TCX para comenzar</h2>
        <p style="color: #B0B0B0; font-size: 1.1rem;">
            Arrastra y suelta tus archivos .tcx en el área de carga arriba
            <br>para analizar tus entrenamientos con métricas avanzadas
        </p>
    </div>
    """, unsafe_allow_html=True)


# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #B0B0B0; padding: 2rem;">
    <p>⚡ Apex Run Analytics v1.0 | Análisis deportivo de nivel profesional</p>
</div>
""", unsafe_allow_html=True)
