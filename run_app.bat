@echo off
echo 🚀 Iniciando Apex Run Analytics...
cd /d "%~dp0"
streamlit run app.py
if %errorlevel% neq 0 (
    echo.
    echo ❌ Ocurrió un error al iniciar la aplicación.
    echo Asegúrate de tener instalado Python y las dependencias.
    pause
)
