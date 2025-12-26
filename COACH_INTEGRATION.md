# Quick Integration Guide for Virtual Coach Section

## Add this code to app.py after line 527 (after the "---" following Personal Records)

```python
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
            st.metric("TRIMP", f"{int(weekly_stats.get('total_load', 0))}")
    
    for insight in all_insights.get('short_term', []):
        display_insight_card(insight)

with tab_month:
    st.markdown("### 📋 Análisis Mensual")
    monthly_prog = summary_stats.get('monthly_progression', {})
    if not monthly_prog.get('insufficient_data'):
        col1, col2 = st.columns(2)
        with col1:
            ei_trend = monthly_prog.get('efficiency_trend', 'stable')
            ei_change = monthly_prog.get('ei_change_pct', 0)
            st.metric("Efficiency Index", ei_trend.title(), f"{ei_change:+.1f}%")
        with col2:
            pace_trend = monthly_prog.get('pace_trend', 'stable')
            pace_change = monthly_prog.get('pace_change_pct', 0)
            st.metric("Ritmo", pace_trend.title(), f"{pace_change:+.1f}%")
    
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
```

## Location
Insert after line 527 in app.py (after the markdown line `st.markdown("---")` that follows Personal Records section)
