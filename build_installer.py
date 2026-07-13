import os
import subprocess
import sys

# --- CONFIGURACIÓN ---
APP_NAME = "APT-Tx"
EXE_NAME = "apt_tx.exe"  # Verifique que este sea el nombre real del .exe generado por Flet en build\windows
INSTALLER_OUT_NAME = "APT-Tx_Setup.exe"
# Ruta por defecto donde suele instalarse NSIS
NSIS_PATH = r"C:\Program Files (x86)\NSIS\makensis.exe"


def get_app_version():
    """Obtiene la versión del proyecto leyendo pyproject.toml (Single Source of Truth)"""
    try:
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("version"):
                    parts = line.split("=")
                    if len(parts) > 1:
                        return parts[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return "1.0.2"  # Versión por defecto en caso de error

def create_nsis_script(version):
    # Rutas a recursos visuales (iconos e imágenes)
    # NSIS compila desde el directorio donde se ejecuta el script.
    icon_path = r"src\assets\icon.ico"
    license_path = r"LICENSE"
    
    # Comprobar si existen y preparar definiciones de NSIS
    nsis_visuals = ""
    if os.path.exists(icon_path):
        nsis_visuals += f'\n    !define MUI_ICON "{icon_path}"'
        nsis_visuals += f'\n    !define MUI_UNICON "{icon_path}"'
    
    # Configurar texto de bienvenida simplificado
    welcome_text = (
        "Este asistente le guiará durante la instalación de APT-Tx.$\\r$\\n$\\r$\\n"
        "Se recomienda cerrar todas las demás aplicaciones antes de iniciar la instalación."
    )
    # Texto para la página de información de dependencias (GNU Radio)
    dependency_info = (
        "INFORMACION SOBRE TRANSMISION SDR (OPCIONAL):\n\n"
        "APT-Tx incluye soporte para transmitir la senal de audio generada hacia hardware SDR "
        "utilizando scripts de GNU Radio.\n\n"
        "Si desea utilizar esta caracteristica, debera tener instalado GNU Radio en su sistema "
        "(se recomienda la distribucion 'radioconda' para Windows y macOS).\n\n"
        "Si no planea transmitir por radio directamente desde este equipo, puede ignorar este paso "
        "y continuar con la instalacion de forma normal. Las funciones de procesamiento de imagen y "
        "generacion de archivos de audio WAV no requieren de este software."
    )
    
    # Crear archivo temporal para la página de la dependencia
    with open("dependency_info.txt", "w", encoding="utf-8-sig") as dep_file:
        dep_file.write(dependency_info)
    
    nsis_script_content = f"""
    Unicode true
    !include "MUI2.nsh"
    !include "FileFunc.nsh"

    Name "{APP_NAME}"
    OutFile "{INSTALLER_OUT_NAME}"
    InstallDir "$PROGRAMFILES\\{APP_NAME}"
    InstallDirRegKey HKLM "Software\\{APP_NAME}" "Install_Dir"
    RequestExecutionLevel admin

    ; Interfaz Gráfica (Modern UI)
    !define MUI_ABORTWARNING
    {nsis_visuals}
    
    ; Textos de Bienvenida Personalizados
    !define MUI_WELCOMEPAGE_TITLE "Bienvenido al Asistente de Instalación de {APP_NAME}"
    !define MUI_WELCOMEPAGE_TEXT "{welcome_text}"
    
    ; Páginas del instalador
    !insertmacro MUI_PAGE_WELCOME
    
    ; 1. Página de la Licencia del Proyecto
    !insertmacro MUI_PAGE_LICENSE "{license_path}"
    
    ; 2. Página Personalizada Informativa de GNU Radio
    Page custom ShowDependencyPage
    
    ; Mostrar opciones premium en la página de finalización (Finish Page)
    !define MUI_FINISHPAGE_RUN "$INSTDIR\\{EXE_NAME}"
    !define MUI_FINISHPAGE_RUN_TEXT "Ejecutar {APP_NAME} ahora"
    !define MUI_FINISHPAGE_SHOWREADME ""
    !define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
    !define MUI_FINISHPAGE_SHOWREADME_TEXT "Crear acceso directo en el Escritorio"
    !define MUI_FINISHPAGE_SHOWREADME_FUNCTION CrearAccesoDirectoEscritorio

    !insertmacro MUI_PAGE_DIRECTORY
    !insertmacro MUI_PAGE_INSTFILES
    !insertmacro MUI_PAGE_FINISH

    ; Páginas del desinstalador
    !insertmacro MUI_UNPAGE_CONFIRM
    !insertmacro MUI_UNPAGE_INSTFILES

    ; Idioma
    !insertmacro MUI_LANGUAGE "Spanish"

    ; --- CÓDIGO DE LA PÁGINA PERSONALIZADA (nsDialogs) ---
    !include "nsDialogs.nsh"
    
    Var Dialog
    Var LabelText
    Var LabelStatus
    Var LinkCtrl
    
    Function ShowDependencyPage
        !insertmacro MUI_HEADER_TEXT "Dependencia Opcional: GNU Radio" "Información para transmisión mediante equipos SDR."
        
        nsDialogs::Create 1018
        Pop $Dialog
        
        ${{If}} $Dialog == error
            Abort
        ${{EndIf}}
        
        ; Texto explicativo principal
        ${{NSD_CreateLabel}} 0 0 100% 45% "APT-Tx incluye soporte para transmitir la señal de audio generada hacia hardware SDR utilizando scripts de GNU Radio.$\\r$\\n$\\r$\\nSi desea utilizar esta característica, necesitará tener instalado GNU Radio en su sistema (se recomienda la distribución 'radioconda' para Windows). Si no planea transmitir por radio, puede ignorar esto."
        Pop $LabelText
        
        ; Detección del estado de GNU Radio
        ; Buscaremos primero si la variable de entorno o registros típicos existen (o si gnuradio-companion.exe está disponible)
        Var /GLOBAL GnuradioInstalled
        StrCpy $GnuradioInstalled "No detectado (Opcional)"
        
        ; Comprobación simple en carpetas comunes
        ${{If}} ${{FileExists}} "$LOCALAPPDATA\\radioconda\\Scripts\\gnuradio-companion.exe"
            StrCpy $GnuradioInstalled "Detectado (radioconda local)"
        ${{ElseIf}} ${{FileExists}} "$PROGRAMFILES\\radioconda\\Scripts\\gnuradio-companion.exe"
            StrCpy $GnuradioInstalled "Detectado (radioconda sistema)"
        ${{ElseIf}} ${{FileExists}} "C:\\ProgramData\\radioconda\\Scripts\\gnuradio-companion.exe"
            StrCpy $GnuradioInstalled "Detectado (radioconda global)"
        ${{ElseIf}} ${{FileExists}} "C:\\radioconda\\Scripts\\gnuradio-companion.exe"
            StrCpy $GnuradioInstalled "Detectado (C:\\radioconda)"
        ${{EndIf}}
        
        ; Mostrar estado de la detección
        ${{NSD_CreateLabel}} 0 55% 100% 10% "Estado actual en el sistema:  $GnuradioInstalled"
        Pop $LabelStatus
        
        ; Crear enlace clickable interactivo
        ${{NSD_CreateLink}} 0 70% 100% 10% "Haga clic aquí para descargar GNU Radio (radioconda)"
        Pop $LinkCtrl
        ${{NSD_OnClick}} $LinkCtrl OnLinkClick
        
        nsDialogs::Show
    FunctionEnd
    
    Function OnLinkClick
        Pop $0 ; Control HWND
        ExecShell "open" "https://github.com/radioconda/radioconda-installer"
    FunctionEnd

    Function CrearAccesoDirectoEscritorio
        CreateShortcut "$DESKTOP\\{APP_NAME}.lnk" "$INSTDIR\\{EXE_NAME}"
    FunctionEnd

    Section "Instalar"
        SetOutPath "$INSTDIR"
        
        ; Guardar ruta de instalación en el registro
        WriteRegStr HKLM "Software\\{APP_NAME}" "Install_Dir" "$INSTDIR"

        ; Copiar todos los archivos recursivamente desde la carpeta build\\windows
        File /r "build\\windows\\*"

        ; Crear el desinstalador
        WriteUninstaller "$INSTDIR\\uninstall.exe"

        ; Registrar en Agregar o Quitar Programas de Windows
        WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "DisplayName" "{APP_NAME}"
        WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "UninstallString" '"$INSTDIR\\uninstall.exe"'
        WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "DisplayIcon" "$INSTDIR\\{EXE_NAME}"
        WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "Publisher" "tcasaniv"
        WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "DisplayVersion" "{version}"
        
        # Calcular tamaño estimado de instalación
        ${{GetSize}} "$INSTDIR" "/S=0K" $0 $1 $2
        IntFmt $0 "0x%08X" $0
        WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "EstimatedSize" "$0"

        ; Accesos directos en el menú de inicio
        CreateDirectory "$SMPROGRAMS\\{APP_NAME}"
        CreateShortcut "$SMPROGRAMS\\{APP_NAME}\\{APP_NAME}.lnk" "$INSTDIR\\{EXE_NAME}"
        CreateShortcut "$SMPROGRAMS\\{APP_NAME}\\Desinstalar.lnk" "$INSTDIR\\uninstall.exe"
    SectionEnd

    Section "Uninstall"
        ; Eliminar de Agregar o Quitar Programas de Windows
        DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}"
        DeleteRegKey HKLM "Software\\{APP_NAME}"

        ; Eliminar accesos directos
        Delete "$DESKTOP\\{APP_NAME}.lnk"
        Delete "$SMPROGRAMS\\{APP_NAME}\\{APP_NAME}.lnk"
        Delete "$SMPROGRAMS\\{APP_NAME}\\Desinstalar.lnk"
        RMDir "$SMPROGRAMS\\{APP_NAME}"

        ; Eliminar archivos instalados (recursivo)
        RMDir /r "$INSTDIR"
    SectionEnd
    """

    script_path = "installer_temp.nsi"
    with open(script_path, "w", encoding="utf-8-sig") as f:
        f.write(nsis_script_content)
    return script_path


def main():
    version = get_app_version()
    print(f"Versión detectada en pyproject.toml: {version}")

    if not os.path.exists("build/windows"):
        print(
            "Error: No se encontró la carpeta 'build/windows'. Ejecute 'flet build windows' primero."
        )
        sys.exit(1)

    if not os.path.exists(NSIS_PATH):
        print(
            f"Error: No se encontró NSIS en la ruta '{NSIS_PATH}'. Instálelo o configure la ruta correcta en el script."
        )
        sys.exit(1)

    print("Generando script de NSIS...")
    nsis_script = create_nsis_script(version)

    print("Compilando instalador de Windows con NSIS...")
    try:
        # Ejecutar makensis para compilar el instalador
        result = subprocess.run(
            [NSIS_PATH, nsis_script], check=True, capture_output=True, text=True
        )
        print(result.stdout)
        print(f"Instalador creado exitosamente: {INSTALLER_OUT_NAME}")
    except subprocess.CalledProcessError as e:
        print("Ocurrió un error al compilar con NSIS:")
        print(e.stderr)
    finally:
        # Limpieza del script temporal .nsi y otros temporales
        if os.path.exists(nsis_script):
            os.remove(nsis_script)
        if os.path.exists("dependency_info.txt"):
            os.remove("dependency_info.txt")


if __name__ == "__main__":
    main()