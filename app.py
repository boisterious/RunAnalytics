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
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    initial_sidebar_state="expanded"
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
    
    # Recalculate metrics for loaded history to ensure consistency
    if st.session_state.runs:
        # 1. Recalculate metrics (Best Efforts)
        needs_metrics_update = False
        for run in st.session_state.runs:
            if 'best_efforts' not in run.get('metrics', {}) or not run['metrics'].get('best_efforts'):
                needs_metrics_update = True
                break
        
        if needs_metrics_update:
            logger.info("Recalculating metrics...")
            for i, run in enumerate(st.session_state.runs):
                if 'best_efforts' not in run.get('metrics', {}) or not run['metrics'].get('best_efforts'):
                    if 'data' in run and not run['data'].empty:
                        metrics_calculator = RunningMetrics(run['data'])
                        new_metrics = metrics_calculator.calculate_all_metrics()
                        if new_metrics.get('avg_heart_rate') is None and run['metrics'].get('avg_heart_rate'):
                            new_metrics['avg_heart_rate'] = run['metrics']['avg_heart_rate']
                        run['metrics'].update(new_metrics)
            save_runs_history(st.session_state.runs)
        
        # 2. Recalculate TRIMP
        needs_trimp_update = False
        for run in st.session_state.runs:
            if 'training_load' not in run or not run.get('training_load'):
                needs_trimp_update = True
                break
        
        if needs_trimp_update:
            all_max_hrs = [r.get('max_hr_estimated', 0) for r in st.session_state.runs if r.get('max_hr_estimated')]
            global_max_hr = max(all_max_hrs) if all_max_hrs else 185
            if global_max_hr < 170: global_max_hr = 185
            
            for i, run in enumerate(st.session_state.runs):
                if 'training_load' not in run or not run.get('training_load'):
                    try:
                        run['training_load'] = calculate_session_load(run, max_hr=global_max_hr)
                    except Exception as e:
                        run['training_load'] = {'trimp': 0, 'tss': 0}
            save_runs_history(st.session_state.runs)

if 'runs_df' not in st.session_state:
    st.session_state.runs_df = None

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


# --- VIEW FUNCTIONS ---

def render_dashboard():
    """Render the main dashboard view (Resumen)"""
    # Custom header
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title">⚡ Apex Run Analytics</h1>
        <p class="main-subtitle">Resumen de Rendimiento</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.runs:
        st.info("👋 ¡Hola! Ve a la sección **📂 Datos** para cargar tus primeros entrenamientos.")
        return

    runs_df = st.session_state.runs_df
    
    # Calculate overview metrics
    total_km = runs_df['distance_km'].sum()
    total_runs = len(runs_df)
    best_pace = runs_df['pace_min_per_km'].min()
    best_ei = runs_df['efficiency_index'].max() if runs_df['efficiency_index'].notna().any() else None
    max_hr = runs_df['max_heart_rate'].max() if runs_df['max_heart_rate'].notna().any() else None
    
    # Display KPI cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(create_kpi_card_html("Total Kilómetros", f"{total_km:.1f} km", f"{total_runs} entrenamientos", "🏃"), unsafe_allow_html=True)
        st.markdown(create_kpi_card_html("Mejor Ritmo", format_pace(best_pace), "min/km", "⚡"), unsafe_allow_html=True)
    
    with col2:
        if best_ei:
            st.markdown(create_kpi_card_html("Mejor Efficiency Index", f"{best_ei:.3f}", "m/min/bpm", "💎"), unsafe_allow_html=True)
        if max_hr:
            st.markdown(create_kpi_card_html("Frecuencia Cardíaca Máxima", f"{int(max_hr)} bpm", "Pico registrado", "❤️"), unsafe_allow_html=True)
            
    st.markdown("---")
    
    # Training Intelligence Section (Simplified for Dashboard)
    st.markdown("## 🎯 Estado Actual")
    
    # Training Load Summary
    from datetime import timedelta
    
    def get_days_ago(run_start_time):
        try:
            start = pd.Timestamp(run_start_time)
            if start.tz is not None: start = start.tz_localize(None)
            now_naive = pd.Timestamp.now()
            return (now_naive - start).days
        except: return 9999
    
    acute_window = [r for r in st.session_state.runs if r.get('start_time') and get_days_ago(r['start_time']) <= 7]
    chronic_window = [r for r in st.session_state.runs if r.get('start_time') and get_days_ago(r['start_time']) <= 28]
    
    acute_load = sum(r.get('training_load', {}).get('trimp', 0) for r in acute_window)
    chronic_load = sum(r.get('training_load', {}).get('trimp', 0) for r in chronic_window)
    chronic_weekly_avg = chronic_load / 4 if chronic_load > 0 else 0
    ratio = acute_load / chronic_weekly_avg if chronic_weekly_avg > 0 else 0
    
    if acute_load > 0 or chronic_load > 0:
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Carga Aguda (7 días)", f"{int(acute_load)}", delta=f"{len(acute_window)} sesiones")
        with col2: st.metric("Carga Crónica (semanal)", f"{int(chronic_weekly_avg)}", delta=f"Promedio 4 semanas")
        with col3:
            if 0.8 <= ratio <= 1.3: ratio_status, ratio_color = "✅ Óptimo", "normal"
            elif ratio > 1.5: ratio_status, ratio_color = "🔴 Alto riesgo", "inverse"
            elif ratio > 1.3: ratio_status, ratio_color = "🟡 Cuidado", "off"
            else: ratio_status, ratio_color = "🔵 Bajo", "off"
            st.metric("Ratio Aguda/Crónica", f"{ratio:.2f}", delta=ratio_status, delta_color=ratio_color)
            
        if ratio > 1.5: st.warning("⚠️ Tu ratio está alto. Considera reducir volumen.")
        elif ratio > 1.3: st.info("📈 Estás en fase de sobrecarga controlada.")
        elif 0.8 <= ratio <= 1.3: st.success("👍 Estás en la zona óptima de progreso.")
        elif ratio < 0.8 and ratio > 0: st.info("📉 Tu carga reciente es baja.")
    else:
        st.info("ℹ️ Sube más entrenamientos con pulsómetro para ver tu carga.")

    st.markdown("---")
    
    # Recent Activity Chart (Pace Evolution)
    st.markdown("### 📈 Tendencia Reciente")
    fig_pace = create_evolution_chart(runs_df, 'pace_min_per_km', 'Ritmo (min/km)')
    fig_pace = add_trend_line(fig_pace, runs_df['start_time'].tolist(), runs_df['pace_min_per_km'].tolist())
    st.plotly_chart(fig_pace, use_container_width=True)


def render_analysis():
    """Render the detailed analysis view"""
    st.markdown("## 📈 Análisis Profundo")
    
    if not st.session_state.runs:
        st.info("No hay datos para analizar.")
        return

    runs_df = st.session_state.runs_df
    
    # Tabs for different analysis types
    tab_evol, tab_terrain, tab_biomech, tab_cardio, tab_perf, tab_session = st.tabs([
        "Evolución", "Terreno", "Biomecánica", "Cardio", "Rendimiento", "Sesión Individual"
    ])
    
    with tab_evol:
        st.markdown("### Evolución Temporal")
        t1, t2 = st.tabs(["Efficiency Index", "GAP vs Ritmo"])
        with t1:
            if runs_df['efficiency_index'].notna().any():
                fig_ei = create_evolution_chart(runs_df[runs_df['efficiency_index'].notna()], 'efficiency_index', 'Efficiency Index')
                clean_df = runs_df[runs_df['efficiency_index'].notna()]
                fig_ei = add_trend_line(fig_ei, clean_df['start_time'].tolist(), clean_df['efficiency_index'].tolist())
                st.plotly_chart(fig_ei, use_container_width=True)
            else: st.info("Faltan datos de pulsaciones.")
        with t2:
            # GAP comparison logic
            comparison_df = runs_df[['start_time', 'pace_min_per_km', 'gap_pace_min_per_km']].copy()
            import plotly.graph_objects as go
            fig = go.Figure()
            
            # Format custom data for tooltips
            pace_custom = comparison_df['pace_min_per_km'].apply(format_pace)
            gap_custom = comparison_df['gap_pace_min_per_km'].apply(format_pace)

            fig.add_trace(go.Scatter(
                x=comparison_df['start_time'], y=comparison_df['pace_min_per_km'],
                mode='lines+markers', name='Ritmo Normal', customdata=pace_custom,
                line=dict(color=COLORS['cyan'], width=2), marker=dict(size=8),
                hovertemplate='<b>Ritmo:</b> %{customdata} min/km<extra></extra>'
            ))
            fig.add_trace(go.Scatter(
                x=comparison_df['start_time'], y=comparison_df['gap_pace_min_per_km'],
                mode='lines+markers', name='GAP', customdata=gap_custom,
                line=dict(color=COLORS['lime'], width=2), marker=dict(size=8),
                hovertemplate='<b>GAP:</b> %{customdata} min/km<extra></extra>'
            ))
            
            # Trend lines
            x_num = list(range(len(comparison_df)))
            if len(x_num) > 1:
                z_pace = np.polyfit(x_num, comparison_df['pace_min_per_km'].tolist(), 1)
                fig.add_trace(go.Scatter(x=comparison_df['start_time'], y=[np.poly1d(z_pace)(x) for x in x_num],
                    mode='lines', name='Tendencia Ritmo', line=dict(dash='dash', color='rgba(0, 255, 255, 0.6)')))
                
                z_gap = np.polyfit(x_num, comparison_df['gap_pace_min_per_km'].tolist(), 1)
                fig.add_trace(go.Scatter(x=comparison_df['start_time'], y=[np.poly1d(z_gap)(x) for x in x_num],
                    mode='lines', name='Tendencia GAP', line=dict(dash='dash', color='rgba(127, 255, 0, 0.6)')))

            fig.update_layout(title="Comparación: Ritmo vs GAP", xaxis_title="Fecha", yaxis_title="Ritmo (min/km)",
                paper_bgcolor=COLORS['bg_dark'], plot_bgcolor=COLORS['bg_card'], font=dict(color=COLORS['text']),
                legend=dict(font=dict(color='white'), bgcolor='rgba(26,31,53,0.9)'))
            st.plotly_chart(fig, use_container_width=True)

    with tab_terrain:
        st.markdown("### 🏔️ Análisis de Terreno")
        classify_all_runs(st.session_state.runs)
        terrain_analyzer = TerrainAnalyzer(st.session_state.runs)
        terrain_summary = terrain_analyzer.get_terrain_summary()
        terrain_dist = terrain_summary.get('distribution', {})
        
        if terrain_dist:
            col1, col2 = st.columns(2)
            with col1:
                import plotly.graph_objects as go
                labels = [f"{info['emoji']} {info['name']}" for info in terrain_dist.values()]
                values = [info['count'] for info in terrain_dist.values()]
                colors = [info['color'] for info in terrain_dist.values()]
                fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors), hole=0.3, textfont=dict(color='white'))])
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=250)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                for terrain_type, info in terrain_dist.items():
                    st.metric(f"{info['emoji']} {info['name']}", f"{info['km_percentage']:.1f}%", f"{info['count']} sesiones")

    with tab_biomech:
        st.markdown("### 👟 Biomecánica")
        fig_scatter = create_cadence_pace_scatter(runs_df)
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        biomech_analyzer = BiomechanicsAnalyzer(st.session_state.runs)
        biomech_summary = biomech_analyzer.get_biomechanics_summary()
        cadence_patterns = biomech_summary.get('cadence_patterns', {})
        
        if cadence_patterns:
            st.markdown("#### Cadencia por Zona")
            cols = st.columns(3)
            for i, (zone, data) in enumerate(cadence_patterns.items()):
                with cols[i % 3]:
                    status = "✅" if data['optimal'] else "⚠️"
                    st.metric(zone.title(), f"{data['avg_cadence']:.0f} spm", status)

    with tab_cardio:
        st.markdown("### ❤️ Cardiovascular")
        cardio_analyzer = CardiovascularAnalyzer(st.session_state.runs)
        cardio_summary = cardio_analyzer.get_cardiovascular_summary()
        
        recent_drift = cardio_summary.get('recent_drift', {})
        if recent_drift.get('has_data'):
            col1, col2 = st.columns(2)
            with col1: st.metric("Deriva Cardíaca", f"{recent_drift['drift_pct']:.1f}%")
            with col2: st.metric("Nivel", recent_drift['severity'].title())
            st.info(recent_drift['message'])
        else:
            st.info("No hay suficientes datos de FC para calcular deriva.")

    with tab_perf:
        st.markdown("### 🏆 Predicciones")
        perf_predictor = PerformancePredictor(st.session_state.runs)
        predictions = perf_predictor.predict_all_distances()
        
        if predictions:
            table_data = []
            for dist, pred in predictions.items():
                table_data.append({'Distancia': dist, 'Tiempo Objetivo': pred['time_str'], 'Ritmo': pred['pace_str']})
            st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
        else:
            st.info("Necesitas establecer récords personales primero.")

    with tab_session:
        st.markdown("### 🗺️ Análisis de Sesión Individual")
        run_options = [f"{run['start_time'].strftime('%d/%m/%Y %H:%M')} - {run['filename']}" for run in st.session_state.runs]
        selected_run_idx = st.selectbox("Selecciona entrenamiento", range(len(run_options)), format_func=lambda x: run_options[x])
        
        if selected_run_idx is not None:
            selected_run = st.session_state.runs[selected_run_idx]
            metrics = selected_run['metrics']
            df = selected_run['data']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Distancia", f"{metrics['distance_km']:.2f} km")
            with col2: st.metric("Tiempo", format_duration(metrics['duration_minutes']))
            with col3: st.metric("Ritmo", format_pace(metrics['pace_min_per_km']))
            with col4: st.metric("Desnivel", f"{metrics['elevation_gain']:.0f} m")
            
            st.plotly_chart(create_session_analysis_chart(df), use_container_width=True)
            
            if 'lat' in df.columns and 'lon' in df.columns and df['lat'].notna().any():
                center_lat, center_lon = df['lat'].mean(), df['lon'].mean()
                m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles='OpenStreetMap')
                route_coords = df[['lat', 'lon']].dropna().values.tolist()
                folium.PolyLine(route_coords, color='#00FFFF', weight=4, opacity=0.8).add_to(m)
                folium_static(m, width=800, height=400)
            
            st.markdown("---")
            st.markdown("#### 🧠 Análisis de Sesión (IA)")
            
            api_key = st.secrets.get("groq", {}).get("api_key")
            if not api_key:
                st.warning("⚠️ Configura tu API Key de Groq para usar esta función")
            else:
                if st.button("🚀 Analizar esta sesión con IA", key=f"btn_analyze_{selected_run['filename']}"):
                    with st.spinner("Analizando sesión..."):
                        from utils.ai_analyzer import AIRunningAnalyzer
                        analyzer = AIRunningAnalyzer(api_key)
                        analysis = analyzer.analyze_session(selected_run, metrics)
                        st.session_state[f'ai_session_{selected_run["filename"]}'] = analysis
                
                if f'ai_session_{selected_run["filename"]}' in st.session_state:
                    st.markdown(st.session_state[f'ai_session_{selected_run["filename"]}'])


def render_coach():
    """Render the AI Coach view"""
    st.markdown("## 🤖 Coach Virtual")
    
    coach = VirtualCoach(st.session_state.runs)
    all_insights = coach.generate_all_insights()
    summary_stats = coach.get_summary_stats()
    
    t_week, t_month, t_long = st.tabs(["📅 Semanal", "📊 Mensual", "📈 Largo Plazo"])
    
    def display_insight_card(insight):
        colors = {'success': '#00FF7F', 'info': '#00BFFF', 'warning': '#FFA500', 'error': '#FF4444'}
        border = colors.get(insight.severity, '#00BFFF')
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(0,255,255,0.05) 0%, rgba(0,200,255,0.02) 100%);
                    border-left: 4px solid {border}; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
            <strong style="color: #00FFFF;">{insight.category}</strong>
            <h4 style="margin: 0.2rem 0; color: #FFF;">{insight.title}</h4>
            <p style="margin: 0; color: #B0B0B0; font-size: 0.9rem;">{insight.message}</p>
        </div>
        """, unsafe_allow_html=True)

    # API Key check
    api_key = st.secrets.get("groq", {}).get("api_key")
    
    with t_week:
        stats = summary_stats.get('weekly', {})
        if stats:
            c1, c2, c3 = st.columns(3)
            c1.metric("Km Semanales", f"{stats.get('total_km', 0):.1f}")
            c2.metric("Sesiones", stats.get('total_runs', 0))
            c3.metric("Carga", int(stats.get('total_load', 0)))
        for insight in all_insights.get('short_term', []): display_insight_card(insight)
        
        if api_key:
            st.markdown("---")
            if st.button("🧠 Analizar Semana con IA", key="btn_ai_week"):
                with st.spinner("Consultando al coach..."):
                    from utils.ai_analyzer import AIRunningAnalyzer
                    analyzer = AIRunningAnalyzer(api_key)
                    st.session_state['ai_week_analysis'] = analyzer.analyze_weekly(stats, st.session_state.runs)
            
            if 'ai_week_analysis' in st.session_state:
                st.info(st.session_state['ai_week_analysis'])

    with t_month:
        for insight in all_insights.get('medium_term', []): display_insight_card(insight)
        
        if api_key:
            st.markdown("---")
            if st.button("🧠 Analizar Mes con IA", key="btn_ai_month"):
                with st.spinner("Analizando tendencias..."):
                    from utils.ai_analyzer import AIRunningAnalyzer
                    analyzer = AIRunningAnalyzer(api_key)
                    progression = summary_stats.get('monthly_progression', {})
                    st.session_state['ai_month_analysis'] = analyzer.analyze_monthly(summary_stats.get('monthly', {}), progression)
            
            if 'ai_month_analysis' in st.session_state:
                st.info(st.session_state['ai_month_analysis'])

    with t_long:
        for insight in all_insights.get('long_term', []): display_insight_card(insight)
        
        if api_key:
            st.markdown("---")
            if st.button("🧠 Analizar Trayectoria (IA)", key="btn_ai_long"):
                with st.spinner("Analizando historial..."):
                    from utils.ai_analyzer import AIRunningAnalyzer
                    analyzer = AIRunningAnalyzer(api_key)
                    st.session_state['ai_long_analysis'] = analyzer.analyze_long_term(summary_stats.get('annual', {}))
            
            if 'ai_long_analysis' in st.session_state:
                st.info(st.session_state['ai_long_analysis'])


def render_data_manager():
    """Render the Data Management view"""
    st.markdown("## 📂 Gestión de Datos")
    
    # File Upload
    st.markdown("### Cargar Entrenamientos")
    uploaded_files = st.file_uploader("Arrastra archivos .tcx", type=['tcx'], accept_multiple_files=True)
    
    if uploaded_files:
        st.info(f"{len(uploaded_files)} archivos seleccionados")
        c1, c2 = st.columns(2)
        if c1.button("➕ Añadir al Historial", type="primary", use_container_width=True):
            process_files(uploaded_files, mode='add')
        if c2.button("🔄 Reemplazar Todo", use_container_width=True):
            process_files(uploaded_files, mode='replace')

    st.markdown("---")
    st.markdown("### Historial")
    
    stats = get_history_stats()
    if stats['total_runs'] > 0:
        st.write(f"**Total:** {stats['total_runs']} sesiones")
        st.write(f"**Rango:** {stats['date_range']['earliest'].strftime('%d/%m/%Y')} - {stats['date_range']['latest'].strftime('%d/%m/%Y')}")
        
        if st.button("🗑️ Borrar todo el historial"):
            clear_history()
            st.session_state.runs = []
            st.session_state.runs_df = None
            st.success("Historial borrado.")
            st.rerun()
            
        # Export
        import json
        export_data = [{k: v for k, v in r.items() if k != 'data' and k != 'data_dict'} for r in st.session_state.runs]
        st.download_button("📥 Descargar Backup JSON", json.dumps(export_data, default=str), "backup.json", "application/json")
    
    st.markdown("### Importar Backup")
    uploaded_json = st.file_uploader("Cargar JSON de historial", type=['json'], key="json_uploader")
    if uploaded_json:
        try:
            import json
            imported_data = json.load(uploaded_json)
            if isinstance(imported_data, list) and len(imported_data) > 0:
                # Validate structure
                if 'metrics' in imported_data[0] and 'start_time' in imported_data[0]:
                    for run in imported_data:
                        if 'data' not in run: run['data'] = pd.DataFrame()
                        # Ensure start_time is datetime
                        if isinstance(run.get('start_time'), str):
                            run['start_time'] = pd.to_datetime(run['start_time'])
                    
                    c1, c2 = st.columns(2)
                    if c1.button("➕ Añadir JSON", use_container_width=True):
                        st.session_state.runs = merge_runs(st.session_state.runs, imported_data)
                        save_runs_history(st.session_state.runs)
                        st.success(f"✅ Añadidos {len(imported_data)} entrenamientos")
                        st.rerun()
                    if c2.button("🔄 Reemplazar con JSON", use_container_width=True):
                        st.session_state.runs = imported_data
                        save_runs_history(st.session_state.runs)
                        st.success(f"✅ Cargados {len(imported_data)} entrenamientos")
                        st.rerun()
                else: st.error("❌ Formato JSON inválido")
            else: st.error("❌ Archivo vacío o inválido")
        except Exception as e: st.error(f"Error: {e}")


def process_files(files, mode='add'):
    """Helper to process uploaded files"""
    progress = st.progress(0, "Procesando...")
    new_runs = []
    for i, f in enumerate(files):
        parsed = parse_tcx_files([f])
        if parsed: new_runs.extend(parsed)
        progress.progress((i + 1) / len(files))
    
    if new_runs:
        classifier = SessionClassifier()
        for run in new_runs:
            df = run['data']
            run['metrics'] = RunningMetrics(df).calculate_all_metrics()
            run['session_type'] = classifier.classify(run)
            run['session_info'] = classifier.get_session_info(run['session_type'])
            
            if 'heart_rate' in df.columns:
                hr_an = HRZones()
                run['hr_zones'] = hr_an.analyze_distribution(df['heart_rate'])
                run['max_hr_estimated'] = hr_an.max_hr
            
            run['training_load'] = calculate_session_load(run, max_hr=run.get('max_hr_estimated', 185))

        if mode == 'add':
            st.session_state.runs = merge_runs(st.session_state.runs, new_runs)
        else:
            st.session_state.runs = new_runs
            
        save_runs_history(st.session_state.runs)
        
        # Rebuild DF
        summary_data = []
        for run in st.session_state.runs:
            metrics = run['metrics']
            summary_data.append({
                'filename': run['filename'], 'start_time': run['start_time'],
                'distance_km': metrics['distance_km'], 'duration_minutes': metrics['duration_minutes'],
                'pace_min_per_km': metrics['pace_min_per_km'], 'elevation_gain': metrics['elevation_gain'],
                'gap_pace_min_per_km': metrics['gap_pace_min_per_km'], 'efficiency_index': metrics['efficiency_index'],
                'max_heart_rate': metrics['max_heart_rate']
            })
        st.session_state.runs_df = pd.DataFrame(summary_data)
        
        st.success(f"✅ Procesados {len(new_runs)} archivos.")
        st.rerun()


# --- MAIN LAYOUT ---

# Sidebar Navigation
with st.sidebar:
    st.title("⚡ Apex Run")
    st.markdown("---")
    
    # Navigation Menu
    selected_view = st.radio(
        "Navegación",
        ["📊 Resumen", "📈 Análisis", "🤖 Coach IA", "📂 Datos"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### 👤 Perfil")
    # Mini stats in sidebar
    if st.session_state.runs:
        total_km = sum(r['metrics']['distance_km'] for r in st.session_state.runs)
        st.metric("Total Km", f"{total_km:.0f}")
    
    st.markdown("---")
    st.caption("v1.2.0 | Apex Analytics")

# Render selected view
if selected_view == "📊 Resumen":
    render_dashboard()
elif selected_view == "📈 Análisis":
    render_analysis()
elif selected_view == "🤖 Coach IA":
    render_coach()
elif selected_view == "📂 Datos":
    render_data_manager()
