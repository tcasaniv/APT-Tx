import flet as ft
import os
import time
import platform
import subprocess
import shutil
import requests # Para descargar imágenes desde URL
import sys # Necesario para sys.executable y sys.frozen
from utils import apt_encoder, modulate_APT_img_to_audio, preprocesar_img_to_APT

VERSION_APP="v1.0.1"

# --- Constantes ---
APP_NAME = "APT-Tx"
APP_FILES_DIR_NAME = "APT-Tx_Files" # Carpeta para guardar archivos generados
SCRIPTS_DIR_NAME = "scripts" # Carpeta para los scripts de GNU Radio

# --- Placeholders de Imágenes ---
# PLACEHOLDER_IMG_A_COLOR = "https://fakeimg.pl/600x400/1e88e5/ffffff?text=Imagen+A+Original&font=noto&font_size=30"
PLACEHOLDER_IMG_A_COLOR = "PLACEHOLDER_IMG_A_COLOR.png"
# PLACEHOLDER_IMG_B_COLOR = "https://fakeimg.pl/600x400/43a047/ffffff?text=Imagen+B+Original&font=noto&font_size=30"
PLACEHOLDER_IMG_B_COLOR = "PLACEHOLDER_IMG_B_COLOR.png"
# PLACEHOLDER_PREPROCESSED_A_PENDING = "https://fakeimg.pl/600x400/757575/ffffff?text=Preprocesar+A&font=noto&font_size=25"
PLACEHOLDER_PREPROCESSED_A_PENDING = "PLACEHOLDER_PREPROCESSED_A_PENDING.png"
# PLACEHOLDER_PREPROCESSED_B_PENDING = "https://fakeimg.pl/600x400/757575/ffffff?text=Preprocesar+B&font=noto&font_size=25"
PLACEHOLDER_PREPROCESSED_B_PENDING = "PLACEHOLDER_PREPROCESSED_B_PENDING.png"
# PLACEHOLDER_PREPROCESSED_DONE = "https://fakeimg.pl/600x400/ffb300/000000?text=Preprocesado&font=noto&font_size=30" # Genérico
PLACEHOLDER_PREPROCESSED_DONE = "PLACEHOLDER_PREPROCESSED_DONE.png"
# PLACEHOLDER_APT_PENDING = "https://fakeimg.pl/600x400/757575/ffffff?text=APT+Pendiente&font=noto&font_size=30"
PLACEHOLDER_APT_PENDING = "PLACEHOLDER_APT_PENDING.png"
# PLACEHOLDER_APT_GENERATED = "https://fakeimg.pl/600x400/d81b60/ffffff?text=Imagen+APT+Generada&font=noto&font_size=30"
PLACEHOLDER_APT_GENERATED = "PLACEHOLDER_APT_GENERATED.png"
# Ejemplo de imagen APT para simulación si se guarda un archivo
DUMMY_APT_IMAGE_FOR_SIMULATION = "https://upload.wikimedia.org/wikipedia/commons/5/57/NOAA_19_APT_Image.jpg" 

# --- Variables globales para almacenar rutas o URLs y estado ---
image_a_source_path = None
image_b_source_path = None
preprocessed_a_path_generated = None
preprocessed_b_path_generated = None
generated_apt_image_path = None
generated_wav_path = None


# --- Configuración de Scripts GNU Radio ---
scripts_config = {
    "Simulación (sin SDR)": "simulate_sdr.py",
    "Simulación (sin SDR | sin audio)": "simulate_sdr_no_audio.py",
    "HackRF (Transmisión Real)": "transmit_hackrf.py",
    "bladeRF (Transmisión Real)": "transmit_bladerf.py",
    "LimeSDR (Transmisión Real)": "transmit_limesdr.py",
    "PlutoSDR (Transmisión Real)": "transmit_pluto.py",
    "USRP (Transmisión Real)": "transmit_usrp.py",
}

# --- Funciones de Utilidad ---
def get_app_base_dir():
    """Obtiene la ruta base de la aplicación (donde está el script principal o el ejecutable)."""
    if getattr(sys, 'frozen', False): 
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_app_files_dir():
    """Obtiene la ruta a la carpeta de archivos de la aplicación y la crea si no existe."""
    if platform.system() == "Windows":
        base_path = os.path.join(os.environ['USERPROFILE'], 'Documents')
    else:
        base_path = os.path.expanduser("~")
    
    app_dir = os.path.join(base_path, APP_FILES_DIR_NAME)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def get_scripts_dir():
    """Obtiene la ruta a la carpeta de scripts de GNU Radio y la crea si no existe."""
    scripts_dir = os.path.join(get_app_base_dir(), SCRIPTS_DIR_NAME)
    os.makedirs(scripts_dir, exist_ok=True)
    return scripts_dir

def open_file_with_default_program(filepath):
    try:
        if not filepath or not os.path.exists(filepath):
            print(f"No se puede abrir: '{filepath}'. No es un archivo válido o no existe.")
            return False
        
        if platform.system() == 'Windows':
            os.startfile(filepath)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', filepath))
        elif platform.system() == 'Linux':
            subprocess.call(('xdg-open', filepath))
        else:
            raise NotImplementedError(f"Plataforma no soportada: {platform.system()}")
        return True
    except Exception as e:
        print(f"Error al abrir '{filepath}': {e}")
        return False

## --- Funciones de Lógica --

def reset_downstream_processing(page: ft.Page, from_step: str):
    """Resetea los paths y UI para los pasos posteriores al indicado."""
    global preprocessed_a_path_generated, preprocessed_b_path_generated
    global generated_apt_image_path, generated_wav_path
    
    if from_step == "source_a_changed" or from_step == "source_all_changed":
        preprocessed_a_path_generated = None
    if from_step == "source_b_changed" or from_step == "source_all_changed":
        preprocessed_b_path_generated = None
    
    if from_step in ["source_a_changed", "source_b_changed", "source_all_changed", "preprocess_changed", "apt_encode_failed", "audio_gen_failed"]:
        generated_apt_image_path = None
        generated_wav_path = None
    
    if from_step in ["source_a_changed", "source_b_changed", "source_all_changed", "preprocess_changed", "apt_encode_failed"]:
         generated_wav_path = None


def preprocessing_img(page: ft.Page, image_name_suffix: str, status_bar_text_ref, 
                      preprocessed_image_display_ref, source_image_path_val):
    if not source_image_path_val or not os.path.exists(source_image_path_val):
        status_bar_text_ref.value = f"Error: No hay imagen fuente local para preprocesar ({image_name_suffix})."
        page.update()
        return None

    status_bar_text_ref.value = f"Preprocesando Imagen {image_name_suffix}..."
    page.update()

    output_filename_base = f"preprocessed_img_{image_name_suffix}_{int(time.time())}.png"
    generated_file_path = os.path.join(get_app_files_dir(), output_filename_base)

    try:
        metrics = preprocesar_img_to_APT(source_image_path_val, generated_file_path, image_name_suffix)
        if metrics:
            preprocessed_image_display_ref.src = metrics["output_path"]
            preprocessed_image_display_ref.update()
            
            lps_text = f"{metrics['lps']:.2f} LPS" if metrics['lps'] is not None else "N/A LPS"
            time_text = f"{metrics['time']:.2f}s"
            status_bar_text_ref.value = (
                f"Imagen {image_name_suffix} preprocesada en {time_text} ({lps_text}). "
                f"Guardada como: {os.path.basename(metrics['output_path'])}"
            )
            page.update()
            return metrics["output_path"]
        else:
            status_bar_text_ref.value = f"Error preprocesando Imagen {image_name_suffix}. Ver consola."
            preprocessed_image_display_ref.src = PLACEHOLDER_PREPROCESSED_A_PENDING if image_name_suffix == "A" else PLACEHOLDER_PREPROCESSED_B_PENDING
            preprocessed_image_display_ref.update()
            page.update()
            return None
    except Exception as e:
        status_bar_text_ref.value = f"Error preprocesando Imagen {image_name_suffix}: {e}"
        preprocessed_image_display_ref.src = PLACEHOLDER_PREPROCESSED_A_PENDING if image_name_suffix == "A" else PLACEHOLDER_PREPROCESSED_B_PENDING
        preprocessed_image_display_ref.update()
        page.update()
        return None


def apt_encoding_img(page: ft.Page, status_label, apt_image_display, 
                     preproc_a_path, preproc_b_path, apt_encoded_status_text):
    global generated_apt_image_path
    if not (preproc_a_path and os.path.exists(preproc_a_path)) or \
       not (preproc_b_path and os.path.exists(preproc_b_path)):
        status_label.value = "Error: Se necesitan ambas imágenes preprocesadas (archivos locales) para codificar a APT."
        page.update()
        generated_apt_image_path = None # Asegurar reseteo
        return None

    status_label.value = "Codificando imágenes a formato APT..."
    page.update()

    output_filename_base = f"apt_encoded_image_{int(time.time())}.png"
    generated_file_path = os.path.join(get_app_files_dir(), output_filename_base)
    
    try:
        metrics = apt_encoder(preproc_a_path, preproc_b_path, generated_file_path)
        if metrics:
            apt_image_display.src = metrics["output_path"] 
            apt_image_display.update()
            
            lps_text = f"{metrics['lps']:.2f} LPS" if metrics['lps'] is not None else "N/A LPS"
            time_text = f"{metrics['time']:.2f}s"
            lines_generated = f"{metrics['lines']:.0f} líneas" if metrics['lines'] is not None else "N/A líneas"
            apt_encoded_status_text.value = (
                f"Imagen APT generada: {os.path.basename(metrics['output_path'])}.\n"
                f"Tiempo total de generación de imagen APT: {time_text}\n"
                f"Ancho de imagen: 2080 píxeles\n"
                f"Líneas generadas: {lines_generated}\n"
                f"Rendimiento: Equivalente a codificar {lps_text} (Líneas Por Segundo)"
            )
            apt_encoded_status_text.update()
            status_label.value = (
                f"Imágenes codificadas a APT en {time_text} ({lps_text}). "
                f"Guardada como: {os.path.basename(metrics['output_path'])}"
            )
            page.update()
            generated_apt_image_path = metrics["output_path"]
            return metrics["output_path"]
        else:
            status_label.value = f"Error generando imagen APT. Ver consola."
            apt_image_display.src = PLACEHOLDER_APT_PENDING
            apt_image_display.update()
            page.update()
            generated_apt_image_path = None
            return None
    except Exception as e:
        status_label.value = f"Error generando imagen APT: {e}"
        apt_image_display.src = PLACEHOLDER_APT_PENDING
        apt_image_display.update()
        page.update()
        generated_apt_image_path = None
        return None
    
def audio_apt_generation(page: ft.Page, status_label, audio_status_text, apt_img_path_val):
    global generated_wav_path
    if not apt_img_path_val or not os.path.exists(apt_img_path_val):
        status_label.value = "Error: Se necesita una imagen APT (archivo local) para generar el audio."
        page.update()
        generated_wav_path = None
        return None

    status_label.value = "Generando audio APT..."
    page.update()

    output_filename_base = f"apt_generated_audio_{int(time.time())}.wav"
    generated_file_path = os.path.join(get_app_files_dir(), output_filename_base)

    try:
        metrics = modulate_APT_img_to_audio(apt_img_path_val, generated_file_path)
        if metrics:
            duration_text = f"{metrics['duration']:.2f} seg"
            time_text = f"{metrics['time']:.2f}s"
            
            lps_text = f"{metrics['lps']:.2f} LPS" if metrics['lps'] is not None else "N/A"
            audio_perf_text = f"{metrics['audio_perf_ratio']:.2f}x" if metrics['audio_perf_ratio'] is not None else "N/A"

            audio_status_text.value = (
                f"Audio APT generado: {os.path.basename(metrics['output_path'])}.\n"
                f"Duración del audio generado: {duration_text}\n\n"
                f"Tiempo total de generación de audio: {time_text}\n"
                f"Ratio de rendimiento de generación de audio: {audio_perf_text} (segundos de audio / segundo de cómputo)\n"
                f"Rendimiento: Equivalente a modular {lps_text} (Líneas Por Segundo)"
            )
            audio_status_text.update()
            status_label.value = f"Audio APT generado en {time_text}."
            page.update()
            generated_wav_path = metrics["output_path"]
            return metrics["output_path"]
        else:
            status_label.value = f"Error generando audio APT. Ver consola."
            page.update()
            generated_wav_path = None
            return None
    except Exception as e:
        status_label.value = f"Error generando audio APT: {e}"
        page.update()
        generated_wav_path = None
        return None

def build_sdr_command(wav_to_transmit_path, selected_script_filename, sdr_options_controls, scripts_base_dir):
    """
    Construye el comando para ejecutar el script GNU Radio y una cadena para mostrar.

    Args:
        wav_to_transmit_path (str|None): Ruta al archivo WAV a transmitir.
        selected_script_filename (str): Nombre del archivo del script GNU Radio.
        sdr_options_controls (dict): Diccionario con las opciones del SDR.
        scripts_base_dir (str): Ruta a la carpeta de scripts.

    Returns:
        tuple: (list_of_command_parts, string_representation_of_command)
               Retorna (None, "Error/Placeholder message") si hay un problema.
    """
    if not selected_script_filename:
        return None, "Error: No se ha seleccionado un script GNU Radio."

    script_full_path = os.path.join(scripts_base_dir, selected_script_filename)
    if not os.path.exists(script_full_path):
        return None, f"Error: El script '{selected_script_filename}' no se encuentra en '{scripts_base_dir}'."

    interprete_python="/usr/bin/python3"
    if platform.system() == 'Windows':
        # interprete_python="~\\AppData\\Local\\Programs\\Python\\Python313\\python.exe"
        interprete_python="C:\\ProgramData\\radioconda\\python.exe"
    elif platform.system() == 'Darwin':  # macOS
        # interprete_python="/opt/homebrew/opt/python@3.13/bin/python3"
        # interprete_python="/opt/homebrew/Cellar/gnuradio/3.10.12.0_1/libexec/venv/bin/python"
        interprete_python="/opt/homebrew/opt/python3/bin/python3"
    elif platform.system() == 'Linux':
        interprete_python="/usr/bin/python3"
    else:
        print("Error: Plataforma no soportada. Usando Python por defecto.")

    command_list = [
        interprete_python,
        "-u", script_full_path,
        "--freq-sdr", str(sdr_options_controls["FREQ_SDR"]),
        "--samp-rate-sdr", str(sdr_options_controls["SAMP_RATE_SDR"])
    ]

    if wav_to_transmit_path and os.path.exists(wav_to_transmit_path):
        command_list.extend(["--wavfile", wav_to_transmit_path])
    else:
        command_list.extend(["--wavfile", 'apt_generated_audio.wav'])

    
    command_str = ' '.join(command_list)
    return command_list, command_str


def sdr_transmission(page: ft.Page, status_label, command_label_ref, wav_to_transmit_path, selected_script_filename, sdr_options_controls):
    
    command_list, command_str_for_execution = build_sdr_command(
        wav_to_transmit_path,
        selected_script_filename,
        sdr_options_controls,
        get_scripts_dir()
    )

    if command_list is None:
        status_label.value = command_str_for_execution 
        if command_label_ref:
             command_label_ref.value = f"Error en la construcción del comando:\n{command_str_for_execution}"
        page.update()
        return

    if command_label_ref:
        command_label_ref.value = f"Ejecutando:\n{command_str_for_execution}"
        page.update() 
    print(f"Ejecutando: {command_str_for_execution}")

    status_label.value = f"Ejecutando: {selected_script_filename}..."
    page.update()

    try:
        process = subprocess.Popen(command_list)
        process.wait() 

        if process.returncode == 0:
            status_label.value = f"Script '{selected_script_filename}' ejecutado exitosamente."
        else:
            status_label.value = f"Script '{selected_script_filename}' finalizó con código de error {process.returncode}. Ver consola."
        
        print(f"Comando ejecutado:\n{' '.join(command_list)}")

    except FileNotFoundError:
        python_interpreter_path = command_list[0] if command_list else "desconocido"
        status_label.value = f"Error: No se encontró el intérprete Python ('{python_interpreter_path}') o el script '{selected_script_filename}'."
    except subprocess.CalledProcessError as e: # No se usa con Popen directamente, pero por si acaso
        status_label.value = f"Error durante la ejecución de '{selected_script_filename}': {e}. Ver consola."
    except Exception as e:
        status_label.value = f"Error inesperado al ejecutar script GNU Radio: {e}"
    
    page.update()

# --- GUI ---
class MainApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_ui()
        self.reset_all_processing_state_and_ui(None)

    def show_alert_dialog(self, title_text, content_text):
        dialog = ft.AlertDialog(
            title=ft.Text(title_text),
            content=ft.Text(content_text),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: self.close_dialog(dialog))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)
        self.page.update()

    def show_about_apt_dialog(self, e):
        self.show_alert_dialog(
            "Sobre APT (Automatic Picture Transmission)",
            "APT es un sistema de transmisión de imágenes analógicas utilizado por algunos satélites meteorológicos, principalmente los de la serie NOAA POES.\n\n"
            "Las imágenes se transmiten en la banda de 137 MHz a 138 MHz y pueden ser recibidas con equipamiento relativamente simple como un receptor FM analógico o un receptor SDR.\n\n"
            "Este programa genera la señal de audio APT para su posterior transmisión con un SDR."
        )

    def show_about_app_dialog(self, e):
        about_app_dialog = ft.AlertDialog(
            title=ft.Text(f"Acerca de {APP_NAME}"),
            content=ft.Column(
                [
                    ft.Row([ft.Image(src="icon.png", width=100, height=100, fit=ft.BoxFit.CONTAIN, border_radius=10),
                    ft.Column([ft.Text(f"Versión: {VERSION_APP}"),
                    ft.Text("Aplicación para generar señales de audio APT para transmisión FM con SDR."),
                    ft.Text("Desarrollado con Flet y Python.")])],wrap=True),
                    ft.Text("\nIdea Original: Transmitir imágenes personalizadas con un SDR simulando así el pase de un satélite NOAA.")
                ], tight=True, spacing=5
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: self.close_dialog(about_app_dialog))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(about_app_dialog)
        self.page.update()
        
    def close_dialog(self, dialog_instance):
        dialog_instance.open = False
        self.page.update()

    def reset_all_processing_state_and_ui(self, e):
        global image_a_source_path, image_b_source_path
        global preprocessed_a_path_generated, preprocessed_b_path_generated
        global generated_apt_image_path, generated_wav_path

        image_a_source_path = None
        image_b_source_path = None
        preprocessed_a_path_generated = None
        preprocessed_b_path_generated = None
        generated_apt_image_path = None
        generated_wav_path = None

        self.img_a_display.src = PLACEHOLDER_IMG_A_COLOR
        self.img_b_display.src = PLACEHOLDER_IMG_B_COLOR
        self.txt_url_a.value = ""
        self.txt_url_b.value = ""
        self.txt_url_a.error = None
        self.txt_url_b.error = None
        
        self.preprocessed_a_display.src = PLACEHOLDER_PREPROCESSED_A_PENDING
        self.preprocessed_b_display.src = PLACEHOLDER_PREPROCESSED_B_PENDING
        self.apt_image_display.src = PLACEHOLDER_APT_PENDING
        self.apt_encoded_status_text.value = "Imagen APT: Aún no generada."
        self.apt_encoded_status_text.tooltip = None
        self.audio_status_text.value = "Audio APT: Aún no generado."
        self.audio_status_text.tooltip = None # Limpiar tooltip si lo tuviera
        
        if hasattr(self, 'sdr_script_dropdown'): # Si ya se inicializó el dropdown
            self.sdr_script_dropdown.value = list(scripts_config.keys())[0] # Resetear al primero

        self.status_bar_text.value = "Estado: Listo. Todo reseteado."
        self.update_action_buttons_state()
        self.update_sdr_command_display() 
        self.page.update()

    def load_url(self, e, img_tag, txt_url_ref, img_display_ref):
        global image_a_source_path, image_b_source_path
        
        url_val = txt_url_ref.value.strip()
        path_to_set = None
        
        if not url_val:
            txt_url_ref.error_text = f"Ingrese una URL para Imagen {img_tag}"
            self.status_bar_text.value = f"URL de Imagen {img_tag} requerida."
            img_display_ref.src = PLACEHOLDER_IMG_A_COLOR if img_tag == "A" else PLACEHOLDER_IMG_B_COLOR
        elif url_val.startswith(("http://", "https://")):
            self.status_bar_text.value = f"Descargando Imagen {img_tag} desde URL..."
            # img_display_ref.src = "https://fakeimg.pl/300x200/cccccc/909090?text=Descargando..." # Placeholder de descarga
            img_display_ref.src = "DESCARGANDO.png" # Placeholder de descarga
            txt_url_ref.error_text = None
            self.page.update()
            try:
                response = requests.get(url_val, stream=True, timeout=10)
                response.raise_for_status() # Lanza excepción para errores HTTP

                # Determinar extensión (simple, puede mejorarse)
                content_type = response.headers.get('content-type')
                ext = ".jpg" # Default
                if content_type:
                    if 'jpeg' in content_type: ext = ".jpg"
                    elif 'png' in content_type: ext = ".png"
                    elif 'bmp' in content_type: ext = ".bmp"
                
                filename = f"downloaded_img_{img_tag.lower()}_{int(time.time())}{ext}"
                downloaded_file_path = os.path.join(get_app_files_dir(),filename)

                with open(downloaded_file_path, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
                
                path_to_set = downloaded_file_path
                img_display_ref.src = path_to_set # Mostrar imagen descargada
                self.status_bar_text.value = f"Imagen {img_tag} descargada y guardada como {filename}."

            except requests.exceptions.RequestException as req_err:
                self.status_bar_text.value = f"Error descargando Imagen {img_tag}: {req_err}"
                txt_url_ref.error_text = "Error de descarga. Verifique URL y conexión."
                img_display_ref.src = PLACEHOLDER_IMG_A_COLOR if img_tag == "A" else PLACEHOLDER_IMG_B_COLOR
            except Exception as ex:
                self.status_bar_text.value = f"Error procesando descarga de Imagen {img_tag}: {ex}"
                txt_url_ref.error_text = "Error inesperado durante descarga."
                img_display_ref.src = PLACEHOLDER_IMG_A_COLOR if img_tag == "A" else PLACEHOLDER_IMG_B_COLOR
        else:
            txt_url_ref.error_text = "URL inválida (debe ser http:// o https://)"
            self.status_bar_text.value = f"URL de Imagen {img_tag} inválida."
            img_display_ref.src = PLACEHOLDER_IMG_A_COLOR if img_tag == "A" else PLACEHOLDER_IMG_B_COLOR
        
        if img_tag == "A":
            image_a_source_path = path_to_set
            reset_downstream_processing(self.page, "source_a_changed")
            self.reset_downstream_for_image_ui("A")
        elif img_tag == "B":
            image_b_source_path = path_to_set
            reset_downstream_processing(self.page, "source_b_changed")
            self.reset_downstream_for_image_ui("B")
        
        self.update_action_buttons_state()
        self.page.update()

    def on_file_picked(self, files, img_tag):
        global image_a_source_path, image_b_source_path
        
        path_to_set = None
        current_img_display = self.img_a_display if img_tag == "A" else self.img_b_display
        txt_url_ref = self.txt_url_a if img_tag == "A" else self.txt_url_b

        if files and len(files) > 0:
            path_to_set = files[0].path
            current_img_display.src = path_to_set
            self.status_bar_text.value = f"Imagen {img_tag} seleccionada: {os.path.basename(path_to_set)}"
            txt_url_ref.value = "" 
            txt_url_ref.error = None
        else:
            self.status_bar_text.value = f"No se seleccionó archivo para Imagen {img_tag}."
            # No cambiar si ya hay una o si se cancela
            current_placeholder = PLACEHOLDER_IMG_A_COLOR if img_tag == "A" else PLACEHOLDER_IMG_B_COLOR
            current_source = image_a_source_path if img_tag == "A" else image_b_source_path
            if not current_source: # Solo volver a placeholder si no había nada antes
                 current_img_display.src = current_placeholder

        if img_tag == "A":
            image_a_source_path = path_to_set
            reset_downstream_processing(self.page, "source_a_changed")
            self.reset_downstream_for_image_ui("A")
        elif img_tag == "B":
            image_b_source_path = path_to_set
            reset_downstream_processing(self.page, "source_b_changed")
            self.reset_downstream_for_image_ui("B")

        self.update_action_buttons_state()
        self.page.update()

    def reset_downstream_for_image_ui(self, img_tag: str):
        """Actualiza la UI para los pasos posteriores al cambio de una imagen fuente."""
        if img_tag == "A":
            self.preprocessed_a_display.src = PLACEHOLDER_PREPROCESSED_A_PENDING
        elif img_tag == "B":
            self.preprocessed_b_display.src = PLACEHOLDER_PREPROCESSED_B_PENDING
        
        self.apt_image_display.src = PLACEHOLDER_APT_PENDING
        self.apt_encoded_status_text.value = "Imagen APT: Aún no generada."
        self.apt_encoded_status_text.tooltip = None
        self.audio_status_text.value = "Audio APT: Aún no generado."
        self.audio_status_text.tooltip = None

        self.preprocessed_a_display.update()
        self.preprocessed_b_display.update()
        self.apt_image_display.update()
        self.apt_encoded_status_text.update()
        self.audio_status_text.update()
        self.update_sdr_command_display() # Actualizar comando ya que el WAV se resetea


    def do_preprocess_all(self, e):
        global preprocessed_a_path_generated, preprocessed_b_path_generated
        if not image_a_source_path or not image_b_source_path:
            self.status_bar_text.value = "Error: Ambas imágenes A y B deben estar cargadas (como archivos locales)."
            self.page.update()
            return
        
        # Preprocesar A
        temp_preproc_a = preprocessing_img(self.page, "A", self.status_bar_text, 
                                           self.preprocessed_a_display, image_a_source_path)
        # Preprocesar B
        temp_preproc_b = preprocessing_img(self.page, "B", self.status_bar_text, 
                                           self.preprocessed_b_display, image_b_source_path)

        # Solo actualizar paths globales si ambos tuvieron éxito
        if temp_preproc_a and temp_preproc_b:
            preprocessed_a_path_generated = temp_preproc_a
            preprocessed_b_path_generated = temp_preproc_b
            self.status_bar_text.value = "Ambas imágenes preprocesadas exitosamente. Listo para codificar a APT."
            reset_downstream_processing(self.page, "preprocess_changed") # Resetea APT y audio lógicamente
            self.apt_image_display.src = PLACEHOLDER_APT_PENDING # Resetea UI de APT
            self.apt_encoded_status_text.value = "Imagen APT: Aún no generada."
            self.apt_encoded_status_text.tooltip = None
            self.audio_status_text.value = "Audio APT: Aún no generado." # Resetea UI de audio
            self.audio_status_text.tooltip = None
            self.apt_image_display.update()
            self.apt_encoded_status_text.update()
            self.audio_status_text.update()

        else:
            preprocessed_a_path_generated = None
            preprocessed_b_path_generated = None
            if not temp_preproc_a: self.preprocessed_a_display.src = PLACEHOLDER_PREPROCESSED_A_PENDING
            if not temp_preproc_b: self.preprocessed_b_display.src = PLACEHOLDER_PREPROCESSED_B_PENDING
            # self.status_bar_text.value = "Error durante el preprocesamiento de una o ambas imágenes."
            reset_downstream_processing(self.page, "preprocess_changed") # Resetea APT y audio lógicamente
            self.reset_downstream_for_image_ui("A") # Esto resetea la UI de APT y audio también

        self.update_action_buttons_state()
        self.update_sdr_command_display()
        self.page.update()
    
    def do_encode_apt_action(self, e):
        encoded_path = apt_encoding_img(self.page, self.status_bar_text, self.apt_image_display,
                                        preprocessed_a_path_generated, preprocessed_b_path_generated,
                                        self.apt_encoded_status_text)
        
        if not encoded_path: # Si falló la codificación
            reset_downstream_processing(self.page, "apt_encode_failed") # Lógica para resetear audio
            self.apt_encoded_status_text.value = "Imagen APT: Aún no generada."
            self.apt_encoded_status_text.tooltip = None
            self.audio_status_text.value = "Audio APT: Aún no generado." # UI para audio
            self.audio_status_text.tooltip = None
            self.apt_encoded_status_text.update()
            self.audio_status_text.update()

        self.update_action_buttons_state()
        self.update_sdr_command_display()
        self.page.update()

    def do_generate_audio_action(self, e):
        audio_path = audio_apt_generation(self.page, self.status_bar_text, self.audio_status_text,
                                          generated_apt_image_path)
        if not audio_path:
            reset_downstream_processing(self.page, "audio_gen_failed")
        self.update_action_buttons_state()
        self.update_sdr_command_display() 
        self.page.update()

    def play_audio_apt_generated(self, e):
        if generated_wav_path and os.path.exists(generated_wav_path):
            if open_file_with_default_program(generated_wav_path):
                self.status_bar_text.value = f"Intentando reproducir: {os.path.basename(generated_wav_path)}"
            else:
                self.status_bar_text.value = f"Error al intentar abrir: {os.path.basename(generated_wav_path)}. Revise la consola."
        else:
            self.status_bar_text.value = "No hay archivo de audio generado o la ruta no es válida."
        self.page.update()
    
    def open_image_in_viewer(self, e, image_control: ft.Image):
        src_path = image_control.src
        if src_path and isinstance(src_path, str) and not src_path.startswith("http") and os.path.exists(src_path) and os.path.isfile(src_path):
            if open_file_with_default_program(src_path):
                self.status_bar_text.value = f"Abriendo imagen: {os.path.basename(src_path)}"
            else:
                self.status_bar_text.value = f"No se pudo abrir la imagen: {os.path.basename(src_path)}. Revise la consola."
        elif src_path and isinstance(src_path, str) and src_path.startswith("http"):
            self.status_bar_text.value = "No se puede abrir una URL directamente. Descárguela primero."
        else:
            self.status_bar_text.value = "No hay imagen local para mostrar o es un placeholder."
        self.page.update()

    def open_output_folder(self, e):
        output_dir = get_app_files_dir()
        if open_file_with_default_program(output_dir):
            self.status_bar_text.value = f"Abriendo carpeta: {output_dir}"
        else:
            self.status_bar_text.value = f"No se pudo abrir la carpeta: {output_dir}. Revise la consola."
        self.page.update()
    
    def do_transmit_sdr(self, e):
        selected_script_display_name = self.sdr_script_dropdown.value
        if not selected_script_display_name:
            self.status_bar_text.value = "Seleccione un script de transmisión."
            self.page.update()
            return
        
        selected_script_filename = scripts_config[selected_script_display_name]
        
        sdr_options = {
            "FREQ_SDR": f"{self.slider_freq_tx_sdr.value}M",
            "SAMP_RATE_SDR": f"{self.slider_samp_rate_sdr.value}M"
        }
        
        self.update_sdr_command_display() # Asegura que el comando mostrado es el actual
                                         # antes de pasarlo a sdr_transmission
        
        sdr_transmission(
            self.page, 
            self.status_bar_text, 
            self.command_label_text, 
            generated_wav_path,       
            selected_script_filename, 
            sdr_options
        )
        # sdr_transmission ya llama a page.update() internamente
    
    def update_sdr_command_display(self, e=None): 
        global generated_wav_path 

        selected_script_display_name = self.sdr_script_dropdown.value
        if not hasattr(self, 'sdr_script_dropdown') or not selected_script_display_name:
            self.command_label_text.value = "Configure los parámetros de transmisión."
            if hasattr(self, 'page') and self.page: self.page.update()
            return

        selected_script_filename = scripts_config[selected_script_display_name]
        
        sdr_options = {
            "FREQ_SDR": f"{self.slider_freq_tx_sdr.value}M",
            "SAMP_RATE_SDR": f"{self.slider_samp_rate_sdr.value}M"
        }
        scripts_dir = get_scripts_dir()
        current_wav_path = generated_wav_path
        
        command_list, cmd_str_display = build_sdr_command(
            current_wav_path, 
            selected_script_filename,
            sdr_options,
            scripts_dir
        )

        is_error_from_builder = cmd_str_display is not None and cmd_str_display.startswith("Error:")
        final_display_str = f"Abrir una terminal y pegar el comando:\n{cmd_str_display if cmd_str_display else 'No se pudo construir el comando.'}"

        if not is_error_from_builder and \
           (not current_wav_path or not os.path.exists(current_wav_path)): # Solo añade nota si el WAV no está
            final_display_str += "\n(Nota: Archivo WAV no generado aún.)"
        
        self.command_label_text.value = final_display_str
        if hasattr(self, 'command_label_text') and self.command_label_text.page:
             self.command_label_text.update()
        elif hasattr(self, 'page') and self.page: 
             self.page.update()


    def update_action_buttons_state(self):
        # Habilitar Preprocesar si ambas imágenes fuente existen como archivos locales
        can_preprocess = (image_a_source_path and os.path.exists(image_a_source_path)) and \
                         (image_b_source_path and os.path.exists(image_b_source_path))
        self.btn_preprocess.disabled = not can_preprocess

        # Habilitar Codificar a APT si ambas imágenes preprocesadas existen como archivos locales
        can_encode_apt = (preprocessed_a_path_generated and os.path.exists(preprocessed_a_path_generated)) and \
                         (preprocessed_b_path_generated and os.path.exists(preprocessed_b_path_generated))
        self.btn_encode_apt.disabled = not can_encode_apt

        # Habilitar Generar Audio si la imagen APT ha sido generada y existe como archivo local
        can_generate_audio = generated_apt_image_path and os.path.exists(generated_apt_image_path)
        self.btn_generate_audio.disabled = not can_generate_audio

        # Habilitar Reproducir Audio si el WAV ha sido generado y existe como archivo local
        can_play_audio = generated_wav_path and os.path.exists(generated_wav_path)
        self.btn_play_audio.disabled = not can_play_audio

        # Habilitar Transmitir si el WAV ha sido generado y existe, y hay un script seleccionado
        can_transmit = can_play_audio and (hasattr(self, 'sdr_script_dropdown') and self.sdr_script_dropdown.value is not None)
        self.btn_transmit.disabled = not can_transmit

        # Actualizar visibilidad/estado de botones dependientes de URL
        self.btn_load_url_a.disabled = not self.txt_url_a.value.strip()
        self.btn_load_url_b.disabled = not self.txt_url_b.value.strip()

        if hasattr(self, 'page') and self.page: self.page.update()


    def on_sdr_script_dropdown_change(self, e):
        self.update_action_buttons_state()
        self.update_sdr_command_display()

    def setup_ui(self):
        self.page.title = f"{APP_NAME} | Simulador de pases NOAA"
        self.page.width = 1050
        self.page.height = 850 
        self.page.padding = 0
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.status_bar_text = ft.Text("Estado: Listo.", expand=True, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS,selectable=True)
        status_bar = ft.Container(
            content=ft.Row([
                self.status_bar_text,
                ft.Text(VERSION_APP+" | "+platform.system(), size=10,selectable=True)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding.symmetric(horizontal=10, vertical=5),
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.SURFACE), # Un color sutil
            border=ft.Border.only(top=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT))
        )

        app_bar = ft.AppBar(
            title=ft.Text(f"{APP_NAME} | Simulador de Pases Satelitales NOAA"),
            center_title=False,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.SURFACE),
            actions=[
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(content=ft.Text("Sobre APT"), on_click=self.show_about_apt_dialog),
                        ft.PopupMenuItem(content=ft.Text("Acerca de..."), on_click=self.show_about_app_dialog),
                        ft.PopupMenuItem(), 
                        ft.PopupMenuItem(content=ft.Text("Resetear Todo"), icon=ft.Icons.REFRESH, on_click=self.reset_all_processing_state_and_ui)
                    ]
                )
            ]
        )
        self.page.appbar = app_bar

        # === Pestaña 1: Selección de Imágenes ===
        txt_url_width = 280
        btn_load_url_width = 150

        self.img_a_display = ft.Image(src=PLACEHOLDER_IMG_A_COLOR, width=350, height=250, fit=ft.BoxFit.CONTAIN, border_radius=10)
        self.img_a_clickable = ft.GestureDetector(content=self.img_a_display, on_tap=lambda e: self.open_image_in_viewer(e, self.img_a_display))
        self.txt_url_a = ft.TextField(label="URL Imagen A", width=txt_url_width, hint_text="https://...", on_change=lambda e: self.update_action_buttons_state())
        self.btn_load_url_a = ft.Button("Cargar URL A", on_click=lambda e: self.load_url(e, "A", self.txt_url_a, self.img_a_display), icon=ft.Icons.LINK, width=btn_load_url_width, disabled=True)
        
        self.img_b_display = ft.Image(src=PLACEHOLDER_IMG_B_COLOR, width=350, height=250, fit=ft.BoxFit.CONTAIN, border_radius=10)
        self.img_b_clickable = ft.GestureDetector(content=self.img_b_display, on_tap=lambda e: self.open_image_in_viewer(e, self.img_b_display))
        self.txt_url_b = ft.TextField(label="URL Imagen B", width=txt_url_width, hint_text="https://...", on_change=lambda e: self.update_action_buttons_state())
        self.btn_load_url_b = ft.Button("Cargar URL B", on_click=lambda e: self.load_url(e, "B", self.txt_url_b, self.img_b_display), icon=ft.Icons.LINK, width=btn_load_url_width, disabled=True)

        async def pick_a(e):
            files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "bmp"])
            self.on_file_picked(files, "A")

        async def pick_b(e):
            files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "bmp"])
            self.on_file_picked(files, "B")

        tab1_content = ft.ListView( expand=True, spacing=15, padding=20,
            controls=[
                ft.Text("1. Selección de Imágenes Fuente", size=20, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.Column([
                            ft.Text("Imagen A", weight=ft.FontWeight.BOLD), self.img_a_clickable,
                            ft.Row([self.txt_url_a, self.btn_load_url_a], alignment=ft.MainAxisAlignment.CENTER, spacing=5,width=450,wrap=True),
                            ft.Button("Archivo Local A", icon=ft.Icons.FOLDER_OPEN, on_click=pick_a, width=(txt_url_width + btn_load_url_width + 5)),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        ft.Column([
                            ft.Text("Imagen B", weight=ft.FontWeight.BOLD), self.img_b_clickable,
                            ft.Row([self.txt_url_b, self.btn_load_url_b], alignment=ft.MainAxisAlignment.CENTER, spacing=5,width=450,wrap=True),
                            ft.Button("Archivo Local B", icon=ft.Icons.FOLDER_OPEN, on_click=pick_b, width=(txt_url_width + btn_load_url_width + 5)),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND, wrap=True,
                ),
            ]
        )

        # === Pestaña 2: Procesamiento y Generación APT ===
        self.preprocessed_a_display = ft.Image(width=300, height=200, fit=ft.BoxFit.CONTAIN, border_radius=10, src=PLACEHOLDER_PREPROCESSED_A_PENDING)
        self.preprocessed_a_clickable = ft.GestureDetector(content=self.preprocessed_a_display, on_tap=lambda e: self.open_image_in_viewer(e, self.preprocessed_a_display))
        
        self.preprocessed_b_display = ft.Image(width=300, height=200, fit=ft.BoxFit.CONTAIN, border_radius=10, src=PLACEHOLDER_PREPROCESSED_B_PENDING)
        self.preprocessed_b_clickable = ft.GestureDetector(content=self.preprocessed_b_display, on_tap=lambda e: self.open_image_in_viewer(e, self.preprocessed_b_display))

        self.apt_image_display = ft.Image(width=600, height=200, fit=ft.BoxFit.CONTAIN, border_radius=10, src=PLACEHOLDER_APT_PENDING)
        self.apt_image_clickable = ft.GestureDetector(content=self.apt_image_display, on_tap=lambda e: self.open_image_in_viewer(e, self.apt_image_display))

        self.apt_encoded_status_text = ft.Text("Imagen APT: Aún no generada.",text_align=ft.TextAlign.CENTER,selectable=True)
        self.audio_status_text = ft.Text("Audio APT: Aún no generado.",text_align=ft.TextAlign.CENTER,selectable=True)

        self.btn_preprocess = ft.Button("1. Preprocesar Imágenes", icon=ft.Icons.IMAGE_SEARCH, on_click=self.do_preprocess_all, disabled=True)
        self.btn_encode_apt = ft.Button("2. Codificar a APT", icon=ft.Icons.TRANSFORM, on_click=self.do_encode_apt_action, disabled=True)
        self.btn_generate_audio = ft.Button("3. Generar Audio APT", icon=ft.Icons.AUDIOTRACK, on_click=self.do_generate_audio_action, disabled=True)
        self.btn_play_audio = ft.Button("Reproducir Audio APT", icon=ft.Icons.PLAY_ARROW, on_click=self.play_audio_apt_generated, disabled=True)
        btn_open_output_folder = ft.Button("Abrir Carpeta de Salida", icon=ft.Icons.FOLDER_SHARED, on_click=self.open_output_folder)

        tab2_content = ft.ListView( expand=True, spacing=15, padding=20,
            controls=[
                ft.Text("2. Procesamiento y Generación APT", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([self.btn_preprocess, self.btn_encode_apt, self.btn_generate_audio], alignment=ft.MainAxisAlignment.CENTER, spacing=10, wrap=True),
                ft.Divider(height=10),
                ft.Text("Previsualización Preprocesadas", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Row(
                    [
                        ft.Column([
                            ft.Text("Imagen A Preprocesada"), self.preprocessed_a_clickable
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Column([
                            ft.Text("Imagen B Preprocesada"), self.preprocessed_b_clickable
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND, wrap=True
                ),
                ft.Divider(height=10),
                ft.Text("Imagen Codificada APT", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Container(content=self.apt_image_clickable, alignment=ft.Alignment.CENTER),
                ft.Container(content=self.apt_encoded_status_text, alignment=ft.Alignment.CENTER, padding=10, 
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), 
                    border_radius=5,
                    bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.ON_SURFACE)),
                ft.Divider(height=10),
                ft.Text("Estado del Audio APT", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Container(content=self.audio_status_text, alignment=ft.Alignment.CENTER, padding=10, 
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), 
                    border_radius=5,
                    bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.ON_SURFACE)),
                ft.Row([
                    self.btn_play_audio, 
                    btn_open_output_folder
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10
                )
            ]
        )

        # === Pestaña 3: Transmisión SDR ===
        self.sdr_script_dropdown = ft.Dropdown(
            label="Modo de Transmisión / Script GRC",
            options=[ft.dropdown.Option(key=name) for name in scripts_config.keys()],
            value=list(scripts_config.keys())[0], # Seleccionar el primero por defecto
            width=400,
            on_text_change=self.on_sdr_script_dropdown_change
        )

        # --- Handlers para Frecuencia de Transmisión ---
        def slider_freq_changed(e):
            self.textfield_freq_tx_sdr.value = f"{self.slider_freq_tx_sdr.value:.1f}"
            self.textfield_freq_tx_sdr.update()
            self.update_sdr_command_display()

        def textfield_freq_changed(e):
            try:
                val = float(self.textfield_freq_tx_sdr.value)
                if 88 <= val <= 1700:
                    self.slider_freq_tx_sdr.value = val
                    self.slider_freq_tx_sdr.update()
                    self.update_sdr_command_display()
                else:
                    self.textfield_freq_tx_sdr.value = f"{self.slider_freq_tx_sdr.value:.1f}"
                    self.textfield_freq_tx_sdr.update()
            except ValueError:
                self.textfield_freq_tx_sdr.value = f"{self.slider_freq_tx_sdr.value:.1f}"
                self.textfield_freq_tx_sdr.update()

        # --- Handlers para Sample Rate ---
        def slider_samp_rate_changed(e):
            self.textfield_samp_rate_sdr.value = f"{self.slider_samp_rate_sdr.value:.1f}"
            self.textfield_samp_rate_sdr.update()
            self.update_sdr_command_display()

        def textfield_samp_rate_changed(e):
            try:
                val = float(self.textfield_samp_rate_sdr.value)
                if 0.2 <= val <= 20:
                    self.slider_samp_rate_sdr.value = val
                    self.slider_samp_rate_sdr.update()
                    self.update_sdr_command_display()
                else:
                    self.textfield_samp_rate_sdr.value = f"{self.slider_samp_rate_sdr.value:.1f}"
                    self.textfield_samp_rate_sdr.update()
            except ValueError:
                self.textfield_samp_rate_sdr.value = f"{self.slider_samp_rate_sdr.value:.1f}"
                self.textfield_samp_rate_sdr.update()

        self.text_freq_tx_sdr = ft.Text("Frecuencia de transmisión:")
        self.slider_freq_tx_sdr = ft.Slider(
            value=137.5, min=88, max=1700, 
            label="{value} MHz", 
            on_change=slider_freq_changed
        ) 
        self.textfield_freq_tx_sdr = ft.TextField(
            value=f"{self.slider_freq_tx_sdr.value:.1f}", 
            width=150, 
            suffix=ft.Text("MHz"), 
            keyboard_type=ft.KeyboardType.NUMBER,
            on_submit=textfield_freq_changed,
            on_blur=textfield_freq_changed,
            text_align=ft.TextAlign.RIGHT,
        )
        
        self.text_samp_rate_sdr = ft.Text("Frecuencia de muestreo SDR (sample rate):")
        self.slider_samp_rate_sdr = ft.Slider(
            value=2.4, min=0.2, max=20, 
            label="{value} MHz", 
            on_change=slider_samp_rate_changed
        )
        self.textfield_samp_rate_sdr = ft.TextField(
            value=f"{self.slider_samp_rate_sdr.value:.1f}", 
            width=150, 
            suffix=ft.Text("MSps"), 
            keyboard_type=ft.KeyboardType.NUMBER,
            on_submit=textfield_samp_rate_changed,
            on_blur=textfield_samp_rate_changed,
            text_align=ft.TextAlign.RIGHT,
        )
        
        self.command_label_text = ft.Text("Comando:\nEsperando configuración...", expand=True, selectable=True, no_wrap=False) # no_wrap=False para permitir multilínea
        self.btn_transmit = ft.Button("Transmitir con SDR", icon=ft.Icons.SEND, on_click=self.do_transmit_sdr, disabled=True)

        tab3_content = ft.ListView( expand=True, spacing=15, padding=20,
            controls=[
                ft.Text("3. Opciones y Transmisión SDR", size=20, weight=ft.FontWeight.BOLD),
                self.sdr_script_dropdown,
                ft.Text("Parámetros de transmisión para el script:", weight=ft.FontWeight.W_400),
                ft.Row([self.text_freq_tx_sdr, self.textfield_freq_tx_sdr], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.slider_freq_tx_sdr,
                ft.Row([self.text_samp_rate_sdr, self.textfield_samp_rate_sdr], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                self.slider_samp_rate_sdr,
                ft.Text("Nota: Ajustar parámetros según el SDR a utilizar", italic=True, size=12),
                ft.Divider(height=10),
                ft.Text("Comando a ejecutar por GNU Radio:", weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=self.command_label_text, 
                    padding=10, 
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT), 
                    border_radius=5,
                    bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.ON_SURFACE) # Fondo sutil para el comando
                ),
                ft.Divider(height=10),
                ft.Container(content=self.btn_transmit, alignment=ft.Alignment.CENTER),
            ]
        )

        main_tabs = ft.Tabs(
            selected_index=0,
            length=3,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Imágenes Fuente", icon=ft.Icons.COLLECTIONS_BOOKMARK_ROUNDED),
                            ft.Tab(label="Procesamiento APT", icon=ft.Icons.SETTINGS_APPLICATIONS_ROUNDED),
                            ft.Tab(label="Transmisión SDR", icon=ft.Icons.SEND_TO_MOBILE_ROUNDED),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            tab1_content,
                            tab2_content,
                            tab3_content,
                        ],
                    ),
                ],
            ),
        )

        self.page.add(
            ft.Column(
                controls=[ main_tabs, status_bar ],
                expand=True, spacing=0
            )
        )


# --- Main ---
def main(page: ft.Page):
    get_app_files_dir()
    scripts_dir=get_scripts_dir()

    # Asegurar que la carpeta de scripts existe antes de que la UI intente acceder a ella
    # (aunque get_scripts_dir ya lo hace, es bueno ser explícito si es crítico para el inicio)
    if not os.path.isdir(scripts_dir):
        # Manejar error si no se puede crear la carpeta de scripts
        page.add(ft.Text(f"Error: No se pudo crear o acceder a la carpeta de scripts: {scripts_dir}"))
        return

    app_instance = MainApp(page)
    # page.update() # MainApp o sus métodos se encargan

if __name__ == "__main__":
    ft.run(main, assets_dir="assets") # En caso de tener una carpeta 'assets' con icon.png u otros assets
    # ft.app(target=main)