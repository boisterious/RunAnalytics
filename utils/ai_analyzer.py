"""AI-Powered Running Analysis using Google Gemini REST API"""

import os
import requests
from typing import Dict, List, Optional
import streamlit as st


class AIRunningAnalyzer:
    """Analyze running data using Groq AI via REST API"""
    
    API_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL = "llama-3.3-70b-versatile"  # Modelo potente y gratuito de Groq
    
    def __init__(self, api_key: str):
        """Initialize with Groq API key"""
        self.api_key = api_key
        self.initialized = bool(api_key)
        
        if not api_key:
            st.warning("No se proporcionó API key para Groq AI.")
    
    def _format_pace(self, pace_decimal: float) -> str:
        """Format pace from decimal (5.70) to mm:ss format (5:42)"""
        minutes = int(pace_decimal)
        seconds = int((pace_decimal - minutes) * 60)
        return f"{minutes}:{seconds:02d}"
    
    def prepare_context(self, runs: List[Dict], runs_df, user_prefs: Optional[Dict] = None) -> str:
        """Prepare running data context for AI analysis"""
        import pandas as pd
        
        # Basic stats
        total_runs = len(runs)
        total_km = runs_df['distance_km'].sum()
        total_hours = runs_df['duration_minutes'].sum() / 60
        
        # Best performances
        best_pace = runs_df['pace_min_per_km'].min()
        best_ei = runs_df['efficiency_index'].max() if runs_df['efficiency_index'].notna().any() else None
        
        # Calculate RECENT training volume (last 4 weeks)
        now = pd.Timestamp.now()
        runs_df_copy = runs_df.copy()
        runs_df_copy['start_time'] = pd.to_datetime(runs_df_copy['start_time'])
        
        # Make timezone-naive for comparison
        if runs_df_copy['start_time'].dt.tz is not None:
            runs_df_copy['start_time'] = runs_df_copy['start_time'].dt.tz_localize(None)
        
        recent_4_weeks = runs_df_copy[runs_df_copy['start_time'] >= (now - pd.Timedelta(days=28))]
        
        if len(recent_4_weeks) > 0:
            recent_weekly_km = recent_4_weeks['distance_km'].sum() / 4
            recent_sessions_per_week = len(recent_4_weeks) / 4
            recent_avg_distance = recent_4_weeks['distance_km'].mean()
            recent_avg_pace = recent_4_weeks['pace_min_per_km'].mean()
        else:
            recent_weekly_km = total_km / max(1, (total_runs / 3))  # Estimate
            recent_sessions_per_week = 2
            recent_avg_distance = runs_df['distance_km'].mean()
            recent_avg_pace = runs_df['pace_min_per_km'].mean()
        
        # Trends (simple: last 5 vs previous 5)
        if len(runs) >= 10:
            recent_pace = runs_df.head(5)['pace_min_per_km'].mean()
            previous_pace = runs_df.iloc[5:10]['pace_min_per_km'].mean()
            pace_improvement = ((previous_pace - recent_pace) / previous_pace * 100)
        else:
            pace_improvement = 0
        
        # Personal records
        from utils.metrics import PersonalRecords
        pr_detector = PersonalRecords(runs)
        pbs = pr_detector.detect_pbs()
        
        # Build context string
        context = f"""
DATOS DEL CORREDOR:

RESUMEN GENERAL:
- Total entrenamientos: {total_runs}
- Kilómetros totales: {total_km:.1f} km
- Horas totales: {total_hours:.1f} h
- Mejor ritmo: {self._format_pace(best_pace)} min/km

VOLUMEN ACTUAL (últimas 4 semanas - MUY IMPORTANTE para el plan):
- Kilómetros por semana: {recent_weekly_km:.1f} km/semana
- Sesiones por semana: {recent_sessions_per_week:.1f} sesiones/semana
- Distancia media por sesión: {recent_avg_distance:.1f} km
- Ritmo medio reciente: {self._format_pace(recent_avg_pace)} min/km
"""
        
        if best_ei:
            context += f"- Mejor Efficiency Index: {best_ei:.3f} m/min/bpm\n"
        
        # Add user preferences if provided
        if user_prefs:
            context += f"""
PREFERENCIAS DEL USUARIO (MUY IMPORTANTE - RESPETAR):
- Días disponibles para RUNNING: {user_prefs.get('running_days', 4)} días/semana
- Otras actividades: {user_prefs.get('other_sports', 'No especificado')}
- Nivel de experiencia: {user_prefs.get('experience_level', 'Intermedio')}
- Objetivo principal: {user_prefs.get('main_goal', 'Mejorar ritmo')}
"""
        
        context += f"\nTENDENCIA RITMO:\n"
        if pace_improvement > 0:
            context += f"- Mejorando: {pace_improvement:.1f}% más rápido en últimas 5 sesiones\n"
        elif pace_improvement < 0:
            context += f"- Declinando: {abs(pace_improvement):.1f}% más lento en últimas 5 sesiones\n"
        else:
            context += "- Estable\n"
        
        if pbs:
            context += "\nRÉCORDS PERSONALES:\n"
            for dist, pb in pbs.items():
                context += f"- {dist}: {self._format_pace(pb['pace'])} min/km\n"
        
        # Session distribution
        session_types = {}
        for run in runs:
            st_name = run.get('session_info', {}).get('name', 'Desconocido')
            session_types[st_name] = session_types.get(st_name, 0) + 1
        
        if session_types:
            context += "\nDISTRIBUCIÓN SESIONES:\n"
            for stype, count in session_types.items():
                pct = (count / total_runs * 100)
                context += f"- {stype}: {count} ({pct:.0f}%)\n"
        
        return context
    
    def generate_analysis(self, context: str) -> str:
        """Generate AI analysis from context using Groq REST API"""
        
        if not self.initialized:
            return "❌ **Error**: No se proporcionó API key para Groq AI."
        
        prompt = f"""Eres un entrenador profesional de running con 20 años de experiencia. Analiza estos datos de un corredor:

{context}

INSTRUCCIONES:
1. Esta app SOLO analiza entrenamientos de running. NO menciones entrenamientos de fuerza ni gimnasio (el usuario puede hacer esto por su cuenta).
2. Ten en cuenta las otras actividades que hace el usuario al planificar la carga total.
3. Usa los días de running indicados como GUÍA, pero si consideras que más o menos días serían beneficiosos, puedes sugerirlo justificando el motivo.
4. IMPORTANTE: El corredor YA está en un nivel de volumen determinado (ver datos de últimas 4 semanas). Tu plan debe:
   - PARTIR de ese nivel actual, no empezar desde cero
   - PROPONER CAMBIOS Y MEJORAS: variedad de sesiones (series, tempos, tiradas largas) que quizás no esté haciendo
   - Progresar gradualmente hacia el objetivo

Genera un informe con EXACTAMENTE estas 5 secciones en markdown:

## 🎯 Valoración General
(2-3 líneas sobre su nivel actual y progreso basándote en los datos)

## 💪 Fortalezas Detectadas
(3-4 puntos específicos que hace bien, basándote en los récords y tendencias)

## 📈 Áreas de Mejora en Running
(3-4 aspectos concretos a trabajar: variedad de sesiones, trabajo de velocidad, tiradas largas, técnica, etc.)

## 🏃 Plan de Entrenamiento Semanal (Próximas 4 Semanas)
COMO COACH, propón un plan que:
- Parta del volumen actual del corredor (no reducirlo)
- Introduzca VARIEDAD: diferentes tipos de sesiones (no solo rodajes al mismo ritmo)
- Incluya al menos un tipo de cada: sesión de calidad (series/tempo) + rodaje suave + tirada más larga
- Si los días disponibles son pocos, prioriza calidad sobre cantidad
- Si consideras que necesita más días, indícalo como sugerencia

Formato para cada semana:
**Semana X:**
- Lunes: [Sesión específica con distancia y ritmo O "Descanso / Otras actividades"]
- Martes: [...] 
- ... (todos los días de la semana)
- **Total running semanal: XX km**
- 💡 *Nota del coach: [breve indicación si hay algo importante esa semana]*

Repite para las 4 semanas con progresión.

## 🎖️ Objetivo de Carrera
(Una carrera/distancia específica para los próximos 3-6 meses con tiempo objetivo realista)

TABLA DE REFERENCIA DE TIEMPOS (usa esto para calcular objetivos):
- 5K a 5:00 min/km = 25:00 min
- 5K a 5:30 min/km = 27:30 min
- 5K a 6:00 min/km = 30:00 min
- 10K a 5:00 min/km = 50:00 min
- 10K a 5:30 min/km = 55:00 min
- 10K a 6:00 min/km = 60:00 min (1 hora)
- 21K a 5:00 min/km = 1:45:00
- 21K a 5:30 min/km = 1:55:30
- 21K a 6:00 min/km = 2:06:00

IMPORTANTE:
- Usa ritmos en formato mm:ss (ej: 5:30 min/km, NO 5.30)
- VERIFICA las matemáticas: tiempo = ritmo × distancia
- Incluye distancias EXACTAS en km para cada sesión
- Incluye el total de km semanal
- Basa los ritmos en los récords personales del corredor
- Tono motivador pero realista
- Usa emojis con moderación
- Máximo 600 palabras total
"""
        
    def _call_api(self, prompt: str) -> str:
        """Helper to call Groq API"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            payload = {
                "model": self.MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un entrenador profesional de running con amplia experiencia en análisis de datos de entrenamiento."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2048
            }
            
            response = requests.post(self.API_URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                try:
                    return data['choices'][0]['message']['content']
                except (KeyError, IndexError) as e:
                    return f"❌ **Error al procesar respuesta**: Estructura inesperada. {str(e)}"
            else:
                error_msg = response.json().get('error', {}).get('message', response.text)
                return f"❌ **Error de API ({response.status_code})**: {error_msg}"
                
        except requests.exceptions.Timeout:
            return "❌ **Error**: La solicitud tardó demasiado. Inténtalo de nuevo."
        except requests.exceptions.RequestException as e:
            return f"❌ **Error de conexión**: {str(e)}"
        except Exception as e:
            return f"❌ **Error inesperado**: {str(e)}"

    def generate_analysis(self, context: str) -> str:
        """Generate general AI analysis (Legacy/Full Profile)"""
        if not self.initialized: return "❌ **Error**: No se proporcionó API key."
        
        prompt = f"""Eres un entrenador profesional de running con 20 años de experiencia. Analiza estos datos de un corredor:

{context}

INSTRUCCIONES:
1. Esta app SOLO analiza entrenamientos de running.
2. Ten en cuenta las otras actividades que hace el usuario.
3. El corredor YA está en un nivel de volumen determinado. Tu plan debe PARTIR de ese nivel.

Genera un informe con EXACTAMENTE estas 5 secciones en markdown:

## 🎯 Valoración General
(2-3 líneas sobre su nivel actual y progreso)

## 💪 Fortalezas Detectadas
(3-4 puntos específicos)

## 📈 Áreas de Mejora
(3-4 aspectos concretos a trabajar)

## 🏃 Plan de Entrenamiento Semanal (Próximas 4 Semanas)
Propón un plan que parta del volumen actual e introduzca variedad.
Formato:
**Semana X:**
- Lunes: ...
...
- **Total running semanal: XX km**

## 🎖️ Objetivo de Carrera
(Una carrera/distancia específica para los próximos 3-6 meses)

IMPORTANTE:
- Usa ritmos en formato mm:ss
- Distancias EXACTAS en km
- Tono motivador pero realista
- Máximo 600 palabras
"""
        return self._call_api(prompt)

    def analyze_weekly(self, weekly_stats: Dict, recent_runs: List[Dict], user_context: str = "") -> str:
        """Generate specific weekly analysis"""
        if not self.initialized: return "❌ **Error**: No se proporcionó API key."
        
        # Build context from stats
        context = f"""
RESUMEN SEMANAL:
- Distancia total: {weekly_stats.get('total_km', 0):.1f} km
- Tiempo total: {weekly_stats.get('total_time_hours', 0):.1f} horas
- Número de sesiones: {weekly_stats.get('total_runs', 0)}
- Carga TRIMP: {int(weekly_stats.get('total_load', 0))}
- Tipos de sesión: {weekly_stats.get('session_types', {})}
"""
        if user_context:
            context += f"\nCONTEXTO DEL USUARIO (MUY IMPORTANTE - PRIORIDAD MÁXIMA): {user_context}\n"

        prompt = f"""Analiza esta semana de entrenamiento de un corredor:
{context}

INSTRUCCIONES CRÍTICAS:
1. **PRIORIZA EL CONTEXTO DEL USUARIO**: Si el usuario explica por qué el volumen es bajo (ej: vacaciones, enfermedad, semana incompleta), NO lo critiques negativamente. Úsalo para EXPLICAR los datos.
2. **Mira al Futuro**: Si el usuario dice que hará más sesiones esta semana, tenlo en cuenta en tu evaluación.
3. **Sé Empático**: Si hubo un parón justificado, da ánimos para retomar, no regañes.

Como entrenador, dame un feedback CORTO y DIRECTO (máx 150 palabras) con:
1. **Evaluación**: ¿Ha sido una semana de carga, descarga o mantenimiento? (Considera el contexto).
2. **Consejo Inmediato**: ¿Qué debería hacer la próxima semana?
3. **Alerta**: Solo si hay algo realmente preocupante que NO esté explicado por el contexto.

Usa emojis y formato markdown.
"""
        return self._call_api(prompt)

    def analyze_monthly(self, monthly_stats: Dict, progression: Dict, user_context: str = "") -> str:
        """Generate monthly trend analysis"""
        if not self.initialized: return "❌ **Error**: No se proporcionó API key."
        
        context = f"""
PROGRESIÓN MENSUAL:
- Tendencia Eficiencia: {progression.get('efficiency_trend', 'stable')} ({progression.get('ei_change_pct', 0):+.1f}%)
- Tendencia Ritmo: {progression.get('pace_trend', 'stable')} ({progression.get('pace_change_pct', 0):+.1f}%)
- Tendencia Volumen: {progression.get('volume_trend', 'stable')}
"""
        if user_context:
            context += f"\nCONTEXTO DEL USUARIO (MUY IMPORTANTE - PRIORIDAD MÁXIMA): {user_context}\n"

        prompt = f"""Analiza la progresión del último mes de este corredor:
{context}

INSTRUCCIONES CRÍTICAS:
1. **CONTEXTO PRIMERO**: Si la tendencia es negativa pero el usuario da una razón válida (lesión, trabajo, vacaciones), acéptala y adapta el consejo.
2. **No seas robótico**: Entiende la vida real del corredor amateur.

Como entrenador, dame un análisis de TENDENCIAS (máx 200 palabras):
1. **¿Estamos mejorando?**: Interpreta los cambios en eficiencia y ritmo (considerando el contexto).
2. **Enfoque del Mes**: ¿En qué fase del entrenamiento parece estar?
3. **Recomendación Táctica**: ¿Qué cualidad física debería priorizar el próximo mes?

Usa emojis y formato markdown.
"""
        return self._call_api(prompt)

    def analyze_long_term(self, annual_stats: Dict, user_context: str = "") -> str:
        """Generate long term analysis"""
        if not self.initialized: return "❌ **Error**: No se proporcionó API key."
        
        context = f"""
HISTORIAL A LARGO PLAZO:
- Meses activos: {annual_stats.get('total_months', 0)}
- Km totales periodo: {annual_stats.get('total_km_period', 0):.0f}
- Tendencia Km: {annual_stats.get('km_trend', 'stable')}
- Mes más activo: {annual_stats.get('most_active_month', 'N/A')}
"""
        if user_context:
            context += f"\nCONTEXTO DEL USUARIO (MUY IMPORTANTE - PRIORIDAD MÁXIMA): {user_context}\n"

        prompt = f"""Analiza la constancia y visión a largo plazo:
{context}

INSTRUCCIONES CRÍTICAS:
1. **CONTEXTO**: Si hay huecos en el historial explicados por el usuario, no los penalices en la valoración de constancia.
2. **Motivación**: Céntrate en lo positivo y en el futuro.

Como entrenador, valora la CONSISTENCIA (máx 150 palabras):
1. **Valoración de Constancia**: ¿Es un corredor consistente? (Matiza con el contexto).
2. **Visión Macro**: ¿Cómo ves su evolución?
3. **Palabras de Motivación**: Mensaje para mantener la disciplina.

Usa emojis y formato markdown.
"""
        return self._call_api(prompt)

    def analyze_session(self, session_data: Dict, metrics: Dict) -> str:
        """Analyze a specific session"""
        if not self.initialized: return "❌ **Error**: No se proporcionó API key."
        
        # Extract key metrics
        dist = metrics.get('distance_km', 0)
        dur = metrics.get('duration_minutes', 0)
        pace = self._format_pace(metrics.get('pace_min_per_km', 0))
        hr = int(metrics.get('avg_heart_rate', 0)) if metrics.get('avg_heart_rate') else "N/A"
        cad = int(metrics.get('avg_cadence', 0)) if metrics.get('avg_cadence') else "N/A"
        ei = f"{metrics.get('efficiency_index', 0):.2f}" if metrics.get('efficiency_index') else "N/A"
        gap = self._format_pace(metrics.get('gap_pace_min_per_km', 0)) if metrics.get('gap_pace_min_per_km') else "N/A"
        elev = metrics.get('elevation_gain', 0)
        
        context = f"""
DATOS DE LA SESIÓN:
- Distancia: {dist:.2f} km
- Duración: {dur:.1f} min
- Ritmo Medio: {pace} min/km
- GAP (Ritmo Ajustado): {gap} min/km
- Desnivel: +{elev:.0f} m
- FC Media: {hr} bpm
- Cadencia Media: {cad} spm
- Efficiency Index: {ei}
"""
        prompt = f"""Analiza esta sesión de entrenamiento específica:
{context}

Como entrenador, dame un feedback TÉCNICO de la sesión (máx 200 palabras):
1. **Tipo de Sesión**: Identifica qué tipo de entreno parece ser (Rodaje, Tempo, Series, Recuperación...) basándote en los datos.
2. **Análisis de Rendimiento**:
   - Relación Ritmo/FC (si hay datos).
   - Eficiencia (si hay datos).
   - Cadencia.
3. **Veredicto**: ¿Fue una buena sesión? ¿Se cumplió el objetivo probable?

Usa emojis y formato markdown.
"""
        return self._call_api(prompt)
    
    @staticmethod
    @st.cache_data(ttl=300, show_spinner=False)
    def cached_analysis(_self, context: str) -> str:
        return _self.generate_analysis(context)
