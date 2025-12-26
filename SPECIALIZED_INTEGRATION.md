# Integration Guide - Specialized Modules

## Add after Coach Virtual section (after line ~613 in app.py)

```python
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
                hole=0.3
            )])
            fig.update_layout(
                title="Distribución por Tipo de Terreno",
                paper_bgcolor='#0E1117',
                font=dict(color='#FAFAFA'),
                height=300
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
        for zone_name, zone_data in cadence_patterns.items():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Zona", zone_name.title())
            with col2:
                st.metric("Cadencia Promedio", f"{zone_data['avg_cadence']:.0f} spm")
            with col3:
                status = "✅" if zone_data['optimal'] else "⚠️"
                st.metric("Estado", status)
    
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
    
    cardio_analyzer = CardiovascularAnalyzer(st.session_state.runs)
    cardio_summary = cardio_analyzer.get_cardiovascular_summary()
    
    # Recent session metrics
    recent_drift = cardio_summary.get('recent_drift', {})
    if recent_drift.get('has_data'):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Deriva Cardíaca", f"{recent_drift['drift_pct']:.1f}%")
        with col2:
            st.metric("Severidad", recent_drift['severity'].title())
        with col3:
            st.markdown(f"**{recent_drift['message']}**")
    
    recent_coupling = cardio_summary.get('recent_coupling', {})
    if recent_coupling.get('has_data'):
        st.markdown("#### Acoplamiento FC-Ritmo")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Ratio", f"{recent_coupling['coupling_ratio']:.2f}")
        with col2:
            st.metric("Eficiencia", recent_coupling['efficiency'].title())
    
    # Insights
    insights = cardio_summary.get('insights', [])
    if insights:
        st.markdown("#### 💡 Insights Cardiovasculares")
        for insight in insights:
            st.info(insight)

with tab_perf:
    st.markdown("### 🏆 Predicciones de Rendimiento")
    
    perf_predictor = PerformancePredictor(st.session_state.runs)
    
    # Get predictions
    predictions = perf_predictor.predict_all_distances()
    
    if predictions:
        st.markdown("#### 🎯 Tiempos Predichos")
        cols = st.columns(4)
        for idx, (dist, pred) in enumerate(predictions.items()):
            with cols[idx]:
                st.metric(dist, pred['time_str'], pred['pace_str'])
        
        # Goal suggestions
        st.markdown("#### 📈 Objetivos Sugeridos")
        goals = perf_predictor.suggest_race_goals()
        for goal in goals:
            st.markdown(f"- {goal}")
    else:
        st.info("Necesitas establecer récords personales para generar predicciones")

st.markdown("---")
```

## Location
Insert after the "Tu Coach Virtual" section ends (around line 613)
Before the "# Session Analysis" section
