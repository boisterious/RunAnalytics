# Apex Run Analytics - Complete Virtual Running Coach Platform

## 🎯 Overview

**Apex Run Analytics** se ha transformado en una **plataforma completa de coaching virtual** con análisis multi-nivel, inteligencia de entrenamiento avanzada y recomendaciones personalizadas.

## ✨ Características Implementadas

### Phase 1: Foundation & Data Persistence ✅
- ✅ Persistencia automática de datos en JSON
- ✅ Contador de archivos y barra de progreso
- ✅ Modos "Añadir al Historial" vs "Reemplazar Todo"
- ✅ Auto-scroll tras procesamiento
- ✅ Sesiones ordenadas por fecha (descendente)
- ✅ Tooltips explicativos para métricas (EI, GAP, Cadencia, Zonas FC)
- ✅ Récords expandidos: 7 distancias (1K, 3K, 5K, 10K, 15K, 21K, 42K)

### Phase 2: Training Intelligence Engine ✅
- ✅ **Clasificador automático** de sesiones: 8 tipos
  - Recovery, Easy, Tempo, Threshold, Intervals, Long Run, Fartlek, Race
- ✅ **Zonas de FC (Z1-Z5)** con análisis de distribución
- ✅ **Carga de entrenamiento**: TRIMP y TSS calculados
- ✅ Gráficas de distribución de tipos de sesión y zonas FC

### Phase 3: Multi-Level Coaching Analysis ✅
- ✅ **Análisis Semanal** (7 días)
  - KPIs: sesiones, km, horas, TRIMP
  - Recomendaciones sobre volumen, frecuencia, variedad
- ✅ **Análisis Mensual** (30 días)
  - Tendencias de Efficiency Index y ritmo
  - Recomendaciones de enfoque de entrenamiento
- ✅ **Análisis Anual** (largo plazo)
  - Progresión multi-mes
  - Acumulados y tendencias

### Phase 4: Specialized Analysis Modules ✅

#### Análisis de Terreno
- ✅ Clasificador: Llano / Ondulado / Montañoso / Alta Montaña
- ✅ Análisis de rendimiento por perfil altimétrico
- ✅ Efectividad de GAP por tipo de terreno
- ✅ Recomendaciones de balance terreno

#### Análisis Biomecánico
- ✅ Patrones de cadencia por zona de ritmo
- ✅ Cálculo de longitud de zancada
- ✅ Score de economía de carrera
- ✅ Recomendaciones de técnica (cadencia óptima 170-190 spm)

#### Análisis Cardiovascular
- ✅ Deriva cardíaca (cardiac drift)
- ✅ Acoplamiento FC-Ritmo (eficiencia cardiovascular)
- ✅ Desacoplamiento aeróbico
- ✅ Alertas de fatiga y hidratación

#### Predicción de Rendimiento
- ✅ Predicciones de tiempos usando Fórmula de Riegel
- ✅ Comparativa con estándares edad/género
- ✅ Sugerencias de objetivos (5%, 10% mejora)

### Phase 5: Session Deep Dive ✅
- ✅ Splits automáticos por kilómetro
- ✅ Análisis de estrategia de pacing (even/negative/positive split)
- ✅ Detección automática de intervalos
- ✅ Score de calidad de sesión (1-10)
- ✅ Breakdown completo de la sesión

### Phase 7: Visualization Enhancements ✅
- ✅ Función para añadir líneas de tendencia
- ✅ Heatmap calendario de entrenamiento
- ✅ Gráfica carga aguda vs crónica
- ✅ Comparador multi-sesión
- ✅ Distribución de zonas FC mejorada

## 📁 Estructura del Proyecto

```
apex-run-analytics/
├── app.py                          # Main Streamlit application
├── data/
│   └── runs_history.json          # Persistent run history
├── styles/
│   └── custom.css                 # Dark mode styling
└── utils/
    ├── tcx_parser.py              # TCX file parser
    ├── metrics.py                 # Core metrics calculation
    ├── visualizations.py          # Base visualizations
    ├── persistence.py             # ✨ Data persistence (Phase 1)
    ├── ui_helpers.py              # ✨ Tooltips & helpers (Phase 1)
    ├── training_analyzer.py       # ✨ Session classification, HR zones (Phase 2)
    ├── coaching_engine.py         # ✨ Multi-level coaching (Phase 3)
    ├── terrain_analyzer.py        # ✨ Terrain analysis (Phase 4)
    ├── biomechanics_analyzer.py   # ✨ Biomechanics (Phase 4)
    ├── cardiovascular_analyzer.py # ✨ Cardiovascular metrics (Phase 4)
    ├── performance_predictor.py   # ✨ Race predictions (Phase 4)
    ├── session_analyzer.py        # ✨ Deep dive analysis (Phase 5)
    └── enhanced_visualizations.py # ✨ Advanced charts (Phase 7)
```

## 🚀 Instalación y Uso

### Requisitos
```bash
pip install streamlit pandas numpy folium geopy plotly streamlit-folium
```

### Ejecutar
```bash
streamlit run app.py
```

### Funcionalidades Principales

1. **Subir archivos TCX**
   - Drag & drop múltiples archivos
   - Modos: Añadir o Reemplazar historial
   - Progreso en tiempo real

2. **Dashboard Principal**
   - KPIs generales (distancia, tiempo, EI)
   - Gráficas de evolución con tendencias
   - Distribución de sesiones por tipo
   - Zonas de frecuencia cardíaca

3. **Tu Coach Virtual**
   - Análisis semanal, mensual y anual
   - Recomendaciones personalizadas
   - Alertas de sobreentrenamiento

4. **Récords Personales**
   - 7 distancias estándar
   - Fecha de cada récord
   - Ritmo y duración

5. **Análisis Individual**
   - Tipo de sesión automático
   - TRIMP y TSS
   - Gráficas multi-eje
   - Mapa de elevación

## 📊 Métricas Avanzadas

### Efficiency Index (EI)
```
EI = (metros/minuto) / FC_promedio
```
Mide cuántos metros recorres por pulsación. Mayor = Mejor forma física.

### Grade Adjusted Pace (GAP)
```
Distancia_equivalente = Distancia + (Desnivel+ × 10)
```
Normaliza el esfuerzo considerando el desnivel positivo.

### TRIMP (Training Impulse)
```
TRIMP = duración × HR_ratio × e^(1.92 × HR_ratio)
```
Cuantifica la carga de entrenamiento cardiovascular.

### Session Quality Score
Score 1-10 basado en:
- Consistencia de ritmo (30%)
- Calidad datos FC (20%)
- Consistencia cadencia (20%)
- Completitud de datos (15%)
- Distancia alcanzada (15%)

## 🎨 Características UI/UX

- **Dark Mode Premium**: Inspirado en Apple Fitness+
- **Gráficas Interactivas**: Plotly con hover tooltips
- **Mapas Interactivos**: Folium para visualizar rutas
- **Tooltips Educativos**: Explicaciones de cada métrica
- **Auto-scroll**: Navegación automática tras procesar
- **Estadísticas de Historial**: Total sesiones, fechas, botón limpiar

## 🧠 Inteligencia de Entrenamiento

### Clasificación Automática
El sistema analiza cada sesión y la clasifica en:
- **Recuperación**: Baja intensidad, FC Z1
- **Rodaje Suave**: Base aeróbica, FC Z2
- **Tempo**: Ritmo sostenido, FC Z3
- **Umbral**: Alta intensidad, FC Z4
- **Intervalos**: Alta variabilidad de ritmo
- **Tirada Larga**: > 90 min o > 15 km
- **Fartlek**: Variabilidad moderada
- **Carrera**: Máxima intensidad, FC Z5

### Recomendaciones Personalizadas

**Ejemplos:**
- "Volumen semanal bajo (15 km). Objetivo: aumentar 10% gradualmente"
- "Falta variedad: todas las sesiones son rodaje suave. Añade tempo o intervalos"
- "Cadencia promedio 165 spm. Objetivo: 180 spm para mejor economía"
- "Deriva cardíaca alta. Mejora hidratación pre-carrera"
- "80%+ entrenamientos en llano. Añade desnivel para potencia"

## 📈 Análisis Multi-Nivel

### Corto Plazo (7 días)
- Balance volumen/intensidad
- Distribución tipos de sesión
- Carga acumulada vs recomendada
- Frecuencia de entrenamientos

### Medio Plazo (30 días)
- Evolución de Efficiency Index
- Tendencias de ritmo
- Mejoras en umbrales

### Largo Plazo (3+ meses)
- Progresión anual
- Kilometraje acumulado
- Tendencias de mejora

## 🏔️ Análisis Especializados

### Terreno
- **Llano**: 0-10 m/km desnivel
- **Ondulado**: 10-30 m/km
- **Montañoso**: 30-60 m/km
- **Alta Montaña**: 60+ m/km

Incluye análisis de efectividad GAP y recomendaciones de balance.

### Biomecánica
- Cadencia óptima: 170-190 spm
- Longitud de zancada ideal
- Detección de overstriding
- Score de economía de carrera

### Cardiovascular
- Deriva cardíaca < 5% = óptimo
- Acoplamiento FC-Ritmo (ratio CV)
- Desacoplamiento aeróbico
- Recomendaciones de base aeróbica

### Rendimiento
- Predicciones Riegel para 5K, 10K, 21K, 42K
- Comparación con estándares edad/género
- Objetivos de mejora 5% y 10%

## 📝 Dataset Example

El sistema espera archivos `.tcx` con:
- Timestamp
- Latitud/Longitud (GPS)
- Altitud
- Frecuencia Cardíaca (opcional)
- Cadencia (opcional)

## 🛠️ Arquitectura Técnica

- **Frontend**: Streamlit
- **Visualizations**: Plotly, Folium
- **Data Processing**: Pandas, NumPy
- **Persistence**: JSON file-based
- **Styling**: Custom CSS Dark Mode

## 📦 Módulos Implementados

Total: **11 módulos Python** (~2400 líneas de código)

1. `persistence.py` - Gestión de historial
2. `ui_helpers.py` - Tooltips y ayuda
3. `training_analyzer.py` - Clasificación y zonas FC
4. `coaching_engine.py` - Coach virtual multi-nivel
5. `terrain_analyzer.py` - Análisis de terreno
6. `biomechanics_analyzer.py` - Técnica de carrera
7. `cardiovascular_analyzer.py` - Métricas cardíacas
8. `performance_predictor.py` - Predicciones
9. `session_analyzer.py` - Análisis profundo
10. `enhanced_visualizations.py` - Gráficas avanzadas
11. `metrics.py` - Métricas base (expandido)

## 🎯 Próximos Pasos Opcionales

- [ ] Integrar análisis especializados en UI principal
- [ ] Badges de logros / milestones
- [ ] Timeline visual de progreso
- [ ] Exportar informes PDF
- [ ] Integraciones con Strava/Garmin

## 📄 Licencia

MIT License

## 👥 Autor

Jacobo Riega - Apex Run Analytics Platform

---

**Versión**: 2.0.0 - Complete Virtual Running Coach
**Última actualización**: Diciembre 2024
