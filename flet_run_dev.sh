#!/usr/bin/env bash
VENV_DIR="venv"  # Directorio del entorno virtual
VENV_ACTIVATE_SCRIPT="venv/bin/activate"

# Determinar qué comando de Python usar (preferir python3)
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    echo "Advertencia: 'python3' no encontrado. Usando 'python' en su lugar."
    echo "Se recomienda encarecidamente instalar y usar python3 para la creación de entornos virtuales."
    PYTHON_CMD="python"
    if ! command -v python &> /dev/null; then
        echo "Error: Ni 'python3' ni 'python' fueron encontrados en el PATH."
        exit 1
    fi
fi

# 1. Crear entorno virtual si no existe
if [ ! -f "$VENV_ACTIVATE_SCRIPT" ]; then
    echo "Entorno virtual no encontrado en '${VENV_DIR}'. Creando entorno..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "Error: No se pudo crear el entorno virtual con '$PYTHON_CMD -m venv $VENV_DIR'."
        exit 1
    fi
    echo "Entorno virtual creado exitosamente en '${VENV_DIR}'."
else
    echo "Entorno virtual encontrado en '${VENV_DIR}'."
fi

# 2. Activar entorno virtual
echo "Activando entorno virtual desde '${VENV_ACTIVATE_SCRIPT}'..."
# shellcheck disable=SC1090 # Informa a shellcheck que es intencional cargar un script no conocido estáticamente
source "$VENV_ACTIVATE_SCRIPT"
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: No se pudo activar el entorno virtual."
    echo "Asegúrate de que '${VENV_ACTIVATE_SCRIPT}' existe y es correcto, y que no hubo errores durante la activación."
    exit 1
fi
echo "Entorno virtual activado: $VIRTUAL_ENV"

# 3. Instalar dependencias
echo "Comprobando e instalando/actualizando dependencias desde requirements.txt..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: No se pudieron instalar las dependencias desde requirements.txt."
    exit 1
fi
echo "Dependencias instaladas/actualizadas correctamente."

# 4. Ejecutar aplicación
echo "Iniciando aplicación Flet..."
flet run
if [ $? -ne 0 ]; then
    echo "Error: No se pudo ejecutar Flet (comando 'flet run' falló)."
    exit 1
fi

echo "Aplicación Flet finalizada o detenida por el usuario."

exit 0