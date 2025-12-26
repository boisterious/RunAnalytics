"""Helper utilities for UI components"""

def create_metric_tooltip(metric_name: str) -> str:
    """Create tooltip/help text for different metrics
    
    Args:
        metric_name: Name of the metric
        
    Returns:
        HTML string with tooltip explanation
    """
    
    tooltips = {
        'efficiency_index': """
            <div class="tooltip-content">
                <h4>💎 Efficiency Index (EI)</h4>
                <p><strong>Fórmula:</strong> (metros/minuto) / pulsaciones promedio</p>
                <p><strong>Qué mide:</strong> Cuántos metros recorres por minuto por cada pulsación cardíaca. 
                Indica la eficiencia de tu sistema cardiovascular.</p>
                <p><strong>Interpretación:</strong></p>
                <ul>
                    <li>📈 <strong>EI más alto</strong> = Mejor forma física y economía de carrera</li>
                    <li>📉 <strong>EI más bajo</strong> = Necesitas más esfuerzo cardiovascular</li>
                </ul>
                <p><strong>Uso:</strong> Monitoriza la evolución del EI a lo largo del tiempo. 
                Un EI creciente indica que estás mejorando tu capacidad aeróbica.</p>
            </div>
        """,
        
        'gap': """
            <div class="tooltip-content">
                <h4>⛰️ Grade Adjusted Pace (GAP)</h4>
                <p><strong>Fórmula:</strong> Distancia equivalente = Distancia real + (Desnivel+ × 10)</p>
                <p><strong>Qué mide:</strong> Tu ritmo ajustado considerando el desnivel positivo. 
                Normaliza el esfuerzo en subidas para compararlo con carreras en llano.</p>
                <p><strong>Ejemplo:</strong> Si corres 10 km con 200m D+ en 60 minutos:</p>
                <ul>
                    <li>Distancia equivalente: 10 + (0.2 × 10) = 12 km</li>
                    <li>GAP: 60 min / 12 km = 5:00 min/km</li>
                    <li>Ritmo real: 60 min / 10 km = 6:00 min/km</li>
                </ul>
                <p><strong>Uso:</strong> Compara sesiones con diferente desnivel de forma justa.</p>
            </div>
        """,
        
        'gap_efficiency': """
            <div class="tooltip-content">
                <h4>💪 GAP Efficiency Index</h4>
                <p><strong>Qué es:</strong> Efficiency Index calculado sobre la distancia ajustada por GAP.</p>
                <p><strong>Por qué es útil:</strong> Mide tu eficiencia cardiovascular considerando el esfuerzo 
                extra de las subidas.</p>
                <p><strong>Comparación:</strong></p>
                <ul>
                    <li>EI normal: Eficiencia en la distancia real</li>
                    <li>GAP EI: Eficiencia considerando el desnivel</li>
                </ul>
                <p>Si tu GAP EI es similar al EI normal, significa que mantienes buena eficiencia en subidas.</p>
            </div>
        """,
        
        'cadence': """
            <div class="tooltip-content">
                <h4>👟 Cadencia</h4>
                <p><strong>Qué mide:</strong> Número de pasos por minuto (spm - steps per minute).</p>
                <p><strong>Rango óptimo:</strong> 170-190 spm para la mayoría de corredores.</p>
                <p><strong>Beneficios de cadencia alta:</strong></p>
                <ul>
                    <li>✅ Reduce impacto en rodillas</li>
                    <li>✅ Mejora economía de carrera</li>
                    <li>✅ Previene lesiones</li>
                    <li>✅ Reduce tiempo de contacto con el suelo</li>
                </ul>
                <p><strong>Cómo mejorar:</strong> Practica con metrónomo, aumenta gradualmente 
                5 spm cada 2-3 semanas.</p>
            </div>
        """,
        
        'heart_rate_zones': """
            <div class="tooltip-content">
                <h4>❤️ Zonas de Frecuencia Cardíaca</h4>
                <p><strong>Basadas en % de FC máxima:</strong></p>
                <ul>
                    <li>🟢 <strong>Z1 (50-60%):</strong> Recuperación activa</li>
                    <li>🔵 <strong>Z2 (60-70%):</strong> Base aeróbica - La zona de entrenamiento fundamental</li>
                    <li>🟡 <strong>Z3 (70-80%):</strong> Tempo - Ritmo sostenido</li>
                    <li>🟠 <strong>Z4 (80-90%):</strong> Umbral - Esfuerzo intenso pero controlado</li>
                    <li>🔴 <strong>Z5 (90-100%):</strong> VO2max - Máxima Intensidad</li>
                </ul>
                <p><strong>Recomendación:</strong> 80% del volumen en Z2, 20% en Z3-Z5</p>
            </div>
        """,

        'trimp': """
            <div class="tooltip-content">
                <h4>💪 TRIMP (Training Impulse)</h4>
                <p><strong>Qué es:</strong> Medida de carga que combina volumen e intensidad.</p>
                <p><strong>Interpretación:</strong></p>
                <ul>
                    <li>🟢 <strong>&lt; 50:</strong> Recuperación</li>
                    <li>🔵 <strong>50-100:</strong> Mantenimiento</li>
                    <li>🟡 <strong>100-200:</strong> Entrenamiento duro</li>
                    <li>🔴 <strong>&gt; 200:</strong> Muy exigente</li>
                </ul>
                <p>Ayuda a gestionar la fatiga y evitar sobreentrenamiento.</p>
            </div>
        """
    }
    
    return tooltips.get(metric_name.lower(), "")


def create_info_icon_html(tooltip_content: str, icon: str = "ℹ️") -> str:
    """Create an info icon with tooltip
    
    Args:
        tooltip_content: HTML content for tooltip
        icon: Emoji or text for the icon
        
    Returns:
        HTML string with styled info icon and tooltip
    """
    
    return f"""
    <div class="tooltip">
        <span style="
            background: rgba(0, 255, 255, 0.1);
            border: 1px solid rgba(0, 255, 255, 0.3);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.9rem;
            cursor: help;
        ">{icon}</span>
        <div class="tooltiptext">{tooltip_content}</div>
    </div>
    """


def create_expandable_help(title: str, content: str) -> str:
    """Create an expandable help section
    
    Args:
        title: Title of the help section
        content: HTML content
        
    Returns:
        HTML with expandable help section
    """
    
    return f"""
    <details class="help-section" style="
        background: rgba(0, 255, 255, 0.05);
        border-left: 3px solid #00FFFF;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    ">
        <summary style="
            cursor: pointer;
            font-weight: 600;
            color: #00FFFF;
            font-size: 1.1rem;
            padding: 0.5rem 0;
        ">{title} ▼</summary>
        <div style="
            margin-top: 1rem;
            color: #B0B0B0;
            line-height: 1.6;
        ">
            {content}
        </div>
    </details>
    """


# Metrics explanations dictionary for easy access
METRICS_GUIDE = {
    'efficiency_index': {
        'name': 'Efficiency Index',
        'unit': 'm/min/bpm',
        'formula': '(distancia_metros / duración_minutos) / FC_promedio',
        'description': 'Indica cuántos metros recorres por minuto por cada pulsación. Mayor = Mejor forma física.',
        'good_range': '> 1.5 para corredores intermedios, > 2.0 para avanzados'
    },
    'gap': {
        'name': 'Grade Adjusted Pace',
        'unit': 'min/km',
        'formula': 'Ritmo calculado sobre: distancia + (desnivel+ × 10)',
        'description': 'Ritmo equivalente en llano considerando el desnivel positivo.',
        'good_range': 'Útil para comparar sesiones con diferente altimetría'
    },
    'cadence': {
        'name': 'Cadencia',
        'unit': 'pasos/min',
        'formula': 'Pasos por minuto',
        'description': 'Frecuencia de pasos. Influye en economía de carrera y prevención de lesiones.',
        'good_range': '170-190 spm es óptimo para la mayoría'
    },
    'heart_rate': {
        'name': 'Frecuencia Cardíaca',
        'unit': 'bpm',
        'formula': 'Pulsaciones por minuto',
        'description': 'Indicador de intensidad del esfuerzo.',
        'good_range': 'Depende de las zonas de entrenamiento (Z1-Z5)'
    }
}
