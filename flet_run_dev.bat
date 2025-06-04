@echo off
setlocal

set "VENV_DIR=venv\Scripts\activate"

rem Crear entorno virtual si no existe
if not exist "%VENV_DIR%" (
    echo Entorno virtual no encontrado. Creando entorno...
    python -m venv venv
    if errorlevel 1 (
        echo Error: No se pudo crear el entorno virtual.
        exit /b 1
    )
)
call "%VENV_DIR%"
if errorlevel 1 (
    echo Error: No se pudo activar el entorno virtual.
    exit /b 1
)
rem Instalar dependencias
echo Comprobando dependencias
pip install -r requirements.txt

rem Ejecutar aplicación
echo Iniciando aplicación
flet run
if errorlevel 1 (
    echo Error: No se pudo ejecutar Flet.
    exit /b 1
)
