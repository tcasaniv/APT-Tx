import flet as ft
import os
import time
import platform
import subprocess
import shutil
import requests # Para descargar imágenes desde URL
from pathlib import Path # Para manejo de rutas más robusto
import sys # Necesario para sys.executable y sys.frozen
from utils import apt_encoder, modulate_APT_img_to_audio, preprocesar_img_to_APT

VERSION_APP="v0.1.0"

# --- Constantes ---
APP_NAME = "APT-Tx"
APP_FILES_DIR_NAME = "APT-Tx_Files" # Carpeta para guardar archivos generados
SCRIPTS_DIR_NAME = "scripts" # Carpeta para los scripts de GNU Radio

# --- Placeholders de Imágenes ---
PLACEHOLDER_IMG_A_COLOR = "https://fakeimg.pl/600x400/1e88e5/ffffff?text=Imagen+A+Original&font=noto&font_size=30"
PLACEHOLDER_IMG_B_COLOR = "https://fakeimg.pl/600x400/43a047/ffffff?text=Imagen+B+Original&font=noto&font_size=30"
PLACEHOLDER_PREPROCESSED_A_PENDING = "https://fakeimg.pl/600x400/757575/ffffff?text=Preprocesar+A&font=noto&font_size=25"
PLACEHOLDER_PREPROCESSED_B_PENDING = "https://fakeimg.pl/600x400/757575/ffffff?text=Preprocesar+B&font=noto&font_size=25"
PLACEHOLDER_PREPROCESSED_DONE = "https://fakeimg.pl/600x400/ffb300/000000?text=Preprocesado&font=noto&font_size=30" # Genérico
PLACEHOLDER_APT_PENDING = "https://fakeimg.pl/600x400/757575/ffffff?text=APT+Pendiente&font=noto&font_size=30"
PLACEHOLDER_APT_GENERATED_SIM = "https://fakeimg.pl/600x400/d81b60/ffffff?text=APT+Generada+(Sim)&font=noto&font_size=30"
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
# Debes crear estos scripts en la carpeta "scripts" o donde corresponda
scripts_config = {
    "Simulación (Audio/Gráfica)": "simulate_fm.py",
    "HackRF (Simulación)": "simulate_hackrf.py",
    "HackRF (Transmisión Real en silencio)": "transmit_hackrf_muted.py",
    "HackRF (Transmisión Real)": "transmit_hackrf.py",
    "USRP (Simulación)": "transmit_usrp.py",
    "USRP (Transmisión Real en silencio)": "transmit_usrp.py",
    "USRP (Transmisión Real)": "transmit_usrp.py",
}

# --- Funciones de Utilidad ---
def get_app_base_dir():
    """Obtiene la ruta base de la aplicación (donde está el script principal o el ejecutable)."""
    if getattr(sys, 'frozen', False): # Si está empaquetado por PyInstaller
        return Path(sys.executable).parent
    return Path(__file__).parent

def get_app_files_dir():
    """Obtiene la ruta a la carpeta de archivos de la aplicación y la crea si no existe."""
    if platform.system() == "Windows":
        base_path = Path(os.environ['USERPROFILE']) / 'Documents'
    else:
        base_path = Path.home()
    
    app_dir = base_path / APP_FILES_DIR_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return str(app_dir)

def get_scripts_dir():
    """Obtiene la ruta a la carpeta de scripts de GNU Radio y la crea si no existe."""
    # Por defecto, busca la carpeta 'scripts' junto al ejecutable o script principal.
    # Se puede cambiar esto para que use get_app_files_dir().
    scripts_dir = get_app_base_dir() / SCRIPTS_DIR_NAME
    scripts_dir.mkdir(parents=True, exist_ok=True)
    return str(scripts_dir)
    

def open_file_with_default_program(filepath):
    try:
        if not filepath or not Path(filepath).exists():
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
# (preprocessing_img, apt_encoding_img, audio_apt_generation
#  asumen que image_X_source_path es local tras la descarga)


def reset_downstream_processing(page: ft.Page, from_step: str):
    """Resetea los paths y UI para los pasos posteriores al indicado."""
    global preprocessed_a_path_generated, preprocessed_b_path_generated
    global generated_apt_image_path, generated_wav_path
    
    # Referencias a controles UI (se deben pasar o hacer accesibles globalmente si es necesario)
    # Esto es un poco hacky, idealmente estos controles estarían en una clase o serían pasados.
    # Por ahora, asumimos que se puede acceder a page y sus controles si es necesario,
    # o mejor, que las funciones de actualización de UI se llamen desde donde están los controles.

    if from_step == "source_a_changed" or from_step == "source_all_changed":
        preprocessed_a_path_generated = None
        # page.preprocessed_a_display.src = PLACEHOLDER_PREPROCESSED_A_PENDING (necesita referencia al control)
    if from_step == "source_b_changed" or from_step == "source_all_changed":
        preprocessed_b_path_generated = None
        # page.preprocessed_b_display.src = PLACEHOLDER_PREPROCESSED_B_PENDING
    
    if from_step in ["source_a_changed", "source_b_changed", "source_all_changed", "preprocess_changed"]:
        generated_apt_image_path = None
        generated_wav_path = None
        # page.apt_image_display.src = PLACEHOLDER_APT_PENDING
        # page.audio_status_text.value = "Audio APT: Aún no generado."
        # page.btn_play_audio.disabled = True

    # Actualizar botones
    # page.update_action_buttons_state() (necesita referencia a la función o page)
    # Esta función se llamará desde el main_page_instance.update_action_buttons_state()

def preprocessing_img(page: ft.Page, image_name_suffix: str, status_bar_text_ref, 
                      preprocessed_image_display_ref, source_image_path_val):
    if not source_image_path_val or not Path(source_image_path_val).exists():
        status_bar_text_ref.value = f"Error: No hay imagen fuente local para preprocesar ({image_name_suffix})."
        page.update()
        return None

    status_bar_text_ref.value = f"Preprocesando Imagen {image_name_suffix}..."
    page.update()

    output_filename = f"preprocessed_img_{image_name_suffix}_{int(time.time())}.png"
    generated_file_path = str(Path(get_app_files_dir()) / output_filename)

    try:
        preprocesar_img_to_APT(source_image_path_val, generated_file_path,image_name_suffix)
        preprocessed_image_display_ref.src = generated_file_path
        preprocessed_image_display_ref.update()
        status_bar_text_ref.value = f"Imagen {image_name_suffix} preprocesada. Guardada como: {output_filename}"
        page.update()
        return generated_file_path
    except Exception as e:
        status_bar_text_ref.value = f"Error preprocesando Imagen {image_name_suffix}: {e}"
        preprocessed_image_display_ref.src = PLACEHOLDER_PREPROCESSED_A_PENDING if image_name_suffix == "A" else PLACEHOLDER_PREPROCESSED_B_PENDING
        preprocessed_image_display_ref.update()
        page.update()
        return None


def apt_encoding_img(page: ft.Page, status_label, apt_image_display, 
                     preproc_a_path, preproc_b_path):
    global generated_apt_image_path
    if not (preproc_a_path and Path(preproc_a_path).exists()) or \
       not (preproc_b_path and Path(preproc_b_path).exists()):
        status_label.value = "Error: Se necesitan ambas imágenes preprocesadas (archivos locales) para codificar a APT."
        page.update()
        return None

    status_label.value = "Codificando imágenes a formato APT..."
    page.update()
    time.sleep(2)

    output_filename = f"apt_encoded_image_{int(time.time())}.png"
    generated_file_path = str(Path(get_app_files_dir()) / output_filename)
    
    try:
        apt_encoder(preproc_a_path, preproc_b_path, generated_file_path)
        apt_image_display.src = generated_file_path # Mostrar la imagen generada
        apt_image_display.update()
        status_label.value = f"Imágenes codificadas a APT. Guardada como: {output_filename}"
        page.update()
        generated_apt_image_path = generated_file_path
        return generated_file_path
    except Exception as e:
        status_label.value = f"Error generando imagen APT: {e}"
        apt_image_display.src = PLACEHOLDER_APT_PENDING
        apt_image_display.update()
        page.update()
        generated_apt_image_path = None
        return None
    
def audio_apt_generation(page: ft.Page, status_label, audio_status_text, apt_img_path_val):
    global generated_wav_path
    if not apt_img_path_val or not Path(apt_img_path_val).exists():
        status_label.value = "Error: Se necesita una imagen APT (archivo local) para generar el audio."
        page.update()
        generated_wav_path = None
        return None

    status_label.value = "Generando audio APT..."
    page.update()

    output_filename = f"apt_generated_audio_{int(time.time())}.wav"
    generated_file_path = str(Path(get_app_files_dir()) / output_filename)

    try:
        duration = modulate_APT_img_to_audio(apt_img_path_val, generated_file_path)
        duration_text = f"{duration} seg"

        audio_status_text.value = f"Audio APT generado: {output_filename}.\nDuración: {duration_text}"
        audio_status_text.update()
        status_label.value = "Audio APT generado."
        page.update()
        generated_wav_path = generated_file_path
        return generated_file_path
    except Exception as e:
        status_label.value = f"Error generando audio APT: {e}"
        page.update()
        generated_wav_path = None
        return None


def sdr_transmission(page: ft.Page, status_label, wav_to_transmit_path, selected_script_filename, sdr_options_controls):
    if not wav_to_transmit_path or not Path(wav_to_transmit_path).exists():
        status_label.value = "Error: No hay archivo WAV para transmitir o el archivo no existe."
        page.update()
        return

    script_full_path = str(Path(get_scripts_dir()) / selected_script_filename)
    if not Path(script_full_path).exists():
        status_label.value = f"Error: El script GNU Radio '{selected_script_filename}' no se encuentra en '{get_scripts_dir()}'."
        page.update()
        return

    status_label.value = f"Preparando transmisión SDR con script: {selected_script_filename}"
    page.update()
    time.sleep(0.5)

    # Construir comando para script de GNU Radio
    interprete_python="/usr/bin/python3"
    if platform.system() == 'Windows':
        interprete_python="/usr/bin/python3"
    elif platform.system() == 'Darwin':  # macOS
        # interprete_python="/opt/homebrew/opt/python@3.13/bin/python3"
        # interprete_python="/opt/homebrew/Cellar/gnuradio/3.10.12.0_1/libexec/venv/bin/python"
        interprete_python="/opt/homebrew/opt/python3/bin/python3"
    elif platform.system() == 'Linux':
        interprete_python="/usr/bin/python3"
    else:
        status_label.value = f"Error: Plataforma no soportada."
    
    command = [
        interprete_python,
        "-u", script_full_path,
        "--freq-sdr",sdr_options_controls["FREQ_SDR"],
        "--samp-rate-sdr", sdr_options_controls["SAMP_RATE_SDR"],
        "--wavfile", wav_to_transmit_path
        ]

    status_label.value = f"Ejecutando: {' '.join(command)}"
    page.update()

    try:
        # Por ahora, solo esperamos a que termine
        status_label.value += "\nScript de transmisión GNU Radio en ejecución..."
        page.update()
        subprocess.run(command)
        print(f"Comando ejecutado:\n{command}")

        status_label.value = f"Script '{selected_script_filename}' ejecutado. Ver consola para la salida."

    except FileNotFoundError:
        status_label.value = f"Error: No se encontró Python ('{interprete_python}') o el script '{script_full_path}'."
    # except subprocess.TimeoutExpired:
    #     status_label.value = f"La ejecución del script '{selected_script_filename}' excedió el tiempo límite."
        # process.kill()
    except Exception as e:
        status_label.value = f"Error al ejecutar script GNU Radio: {e}"
    
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
        self.page.dialog = dialog
        self.page.open(dialog)
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
                    ft.Row([ft.Image(src="icon.png", width=100, height=100, fit=ft.ImageFit.CONTAIN, border_radius=10),
                    ft.Column([ft.Text(f"Versión: {VERSION_APP}"),
                    ft.Text("Aplicación para generar señales de audio APT para transmisión FM con SDR."),
                    ft.Text("Desarrollado con Flet y Python.")])],wrap=True),
                    ft.Text("\nIdea Original: Transmitir imágenes personalizadas con un SDR simulando así el pase de un satélite NOAA.")
                ], tight=True, spacing=5
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: self.close_dialog(about_app_dialog))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = about_app_dialog
        self.page.open(about_app_dialog)
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
        self.txt_url_a.error_text = None
        self.txt_url_b.error_text = None
        
        self.preprocessed_a_display.src = PLACEHOLDER_PREPROCESSED_A_PENDING
        self.preprocessed_b_display.src = PLACEHOLDER_PREPROCESSED_B_PENDING
        self.apt_image_display.src = PLACEHOLDER_APT_PENDING
        self.audio_status_text.value = "Audio APT: Aún no generado."
        
        if hasattr(self, 'sdr_script_dropdown'): # Si ya se inicializó el dropdown
            self.sdr_script_dropdown.value = list(scripts_config.keys())[0] # Resetear al primero

        self.status_bar_text.value = "Estado: Listo. Todo reseteado."
        self.update_action_buttons_state()
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
            img_display_ref.src = "https://fakeimg.pl/300x200/cccccc/909090?text=Descargando..." # Placeholder de descarga
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
                downloaded_file_path = str(Path(get_app_files_dir()) / filename)

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
            self.reset_downstream_for_image("A")
        elif img_tag == "B":
            image_b_source_path = path_to_set
            self.reset_downstream_for_image("B")
        
        self.update_action_buttons_state()
        self.page.update()

    def on_file_picked(self, e: ft.FilePickerResultEvent, img_tag):
        global image_a_source_path, image_b_source_path
        
        path_to_set = None
        current_img_display = self.img_a_display if img_tag == "A" else self.img_b_display
        txt_url_ref = self.txt_url_a if img_tag == "A" else self.txt_url_b

        if e.files and len(e.files) > 0:
            path_to_set = e.files[0].path
            current_img_display.src = path_to_set
            self.status_bar_text.value = f"Imagen {img_tag} seleccionada: {Path(path_to_set).name}"
            txt_url_ref.value = "" 
            txt_url_ref.error_text = None
        else:
            self.status_bar_text.value = f"No se seleccionó archivo para Imagen {img_tag}."
            # No cambiar si ya hay una o si se cancela
            current_placeholder = PLACEHOLDER_IMG_A_COLOR if img_tag == "A" else PLACEHOLDER_IMG_B_COLOR
            current_source = image_a_source_path if img_tag == "A" else image_b_source_path
            if not current_source: # Solo volver a placeholder si no había nada antes
                 current_img_display.src = current_placeholder

        if img_tag == "A":
            image_a_source_path = path_to_set
            self.reset_downstream_for_image("A")
        elif img_tag == "B":
            image_b_source_path = path_to_set
            self.reset_downstream_for_image("B")

        self.update_action_buttons_state()
        self.page.update()

    def reset_downstream_for_image(self, img_tag: str):
        global preprocessed_a_path_generated, preprocessed_b_path_generated
        global generated_apt_image_path, generated_wav_path

        if img_tag == "A":
            preprocessed_a_path_generated = None
            self.preprocessed_a_display.src = PLACEHOLDER_PREPROCESSED_A_PENDING
        elif img_tag == "B":
            preprocessed_b_path_generated = None
            self.preprocessed_b_display.src = PLACEHOLDER_PREPROCESSED_B_PENDING
        
        generated_apt_image_path = None
        generated_wav_path = None
        self.apt_image_display.src = PLACEHOLDER_APT_PENDING
        self.audio_status_text.value = "Audio APT: Aún no generado."
        
        self.preprocessed_a_display.update()
        self.preprocessed_b_display.update()
        self.apt_image_display.update()
        self.audio_status_text.update()


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
            self.status_bar_text.value = "Ambas imágenes preprocesadas."
        else:
            # Si uno falla, reseteamos ambos para evitar estado inconsistente para el siguiente paso
            preprocessed_a_path_generated = None
            preprocessed_b_path_generated = None
            if not temp_preproc_a: self.preprocessed_a_display.src = PLACEHOLDER_PREPROCESSED_A_PENDING
            if not temp_preproc_b: self.preprocessed_b_display.src = PLACEHOLDER_PREPROCESSED_B_PENDING
            self.status_bar_text.value = "Error durante el preprocesamiento. Verifique que las imágenes fuente sean válidas."
            # Reseteamos también APT y audio
            self.reset_downstream_for_image("A") # Esto resetea APT y audio
            self.reset_downstream_for_image("B") # Y esto también (redundante pero seguro)

        self.update_action_buttons_state()
        self.page.update()
    
    def do_encode_apt_action(self, e):
        global generated_apt_image_path
        generated_apt_image_path = apt_encoding_img(self.page, self.status_bar_text, self.apt_image_display,
                                                    preprocessed_a_path_generated, preprocessed_b_path_generated)
        self.update_action_buttons_state()
        self.page.update()

    def do_generate_audio_action(self, e):
        global generated_wav_path
        generated_wav_path = audio_apt_generation(self.page, self.status_bar_text, self.audio_status_text,
                                                  generated_apt_image_path)
        self.update_action_buttons_state()
        self.page.update()

    def play_audio_apt_generated(self, e):
        if generated_wav_path and Path(generated_wav_path).exists():
            if open_file_with_default_program(generated_wav_path):
                self.status_bar_text.value = f"Intentando reproducir: {Path(generated_wav_path).name}"
            else:
                self.status_bar_text.value = f"Error al intentar abrir: {Path(generated_wav_path).name}. Revise la consola."
        else:
            self.status_bar_text.value = "No hay archivo de audio generado o la ruta no es válida."
        self.page.update()
    
    def open_image_in_viewer(self, e, image_control: ft.Image):
        src_path = image_control.src
        if src_path and not src_path.startswith("http") and Path(src_path).exists() and Path(src_path).is_file():
            if open_file_with_default_program(src_path):
                self.status_bar_text.value = f"Abriendo imagen: {Path(src_path).name}"
            else:
                self.status_bar_text.value = f"No se pudo abrir la imagen: {Path(src_path).name}. Revise la consola."
        elif src_path and src_path.startswith("http"):
             self.status_bar_text.value = "No se puede abrir una URL directamente. Descárguela primero."
        else:
            self.status_bar_text.value = "No hay imagen local para mostrar o es un placeholder."
        self.page.update()

    def open_output_folder(self, e):
        output_dir = get_app_files_dir()
        if open_file_with_default_program(output_dir): # Asumiendo que open_file_with_default_program puede abrir carpetas
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
        
        # Pasar referencias a los inputs para que sdr_transmission pueda leer sus valores
        sdr_controls = {
            "FREQ_SDR": f"{self.slider_freq_tx_sdr.value}M",
            "SAMP_RATE_SDR": f"{self.slider_samp_rate_sdr.value}M"
        }

        sdr_transmission(self.page, self.status_bar_text, generated_wav_path, selected_script_filename, sdr_controls)
        self.page.update()


    def update_action_buttons_state(self):
        # Habilitar Preprocesar si ambas imágenes fuente existen como archivos locales
        can_preprocess = (image_a_source_path and Path(image_a_source_path).exists()) and \
                         (image_b_source_path and Path(image_b_source_path).exists())
        self.btn_preprocess.disabled = not can_preprocess

        # Habilitar Codificar a APT si ambas imágenes preprocesadas existen como archivos locales
        can_encode_apt = (preprocessed_a_path_generated and Path(preprocessed_a_path_generated).exists()) and \
                         (preprocessed_b_path_generated and Path(preprocessed_b_path_generated).exists())
        self.btn_encode_apt.disabled = not can_encode_apt

        # Habilitar Generar Audio si la imagen APT ha sido generada y existe como archivo local
        can_generate_audio = generated_apt_image_path and Path(generated_apt_image_path).exists()
        self.btn_generate_audio.disabled = not can_generate_audio

        # Habilitar Reproducir Audio si el WAV ha sido generado y existe como archivo local
        can_play_audio = generated_wav_path and Path(generated_wav_path).exists()
        self.btn_play_audio.disabled = not can_play_audio
            
        # Habilitar Transmitir si el WAV ha sido generado y existe, y hay un script seleccionado
        can_transmit = can_play_audio and (hasattr(self, 'sdr_script_dropdown') and self.sdr_script_dropdown.value is not None)
        self.btn_transmit.disabled = not can_transmit

        # Actualizar visibilidad/estado de botones dependientes de URL
        self.btn_load_url_a.disabled = not self.txt_url_a.value.strip()
        self.btn_load_url_b.disabled = not self.txt_url_b.value.strip()

        self.page.update()


    def setup_ui(self):
        self.page.title = f"{APP_NAME} | Simulador de pases NOAA"
        self.page.window_width = 1050
        self.page.window_height = 850 # Un poco más alto para el dropdown
        self.page.padding = 0
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.status_bar_text = ft.Text("Estado: Listo.", expand=True, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS)
        status_bar = ft.Container(
            content=ft.Row([
                self.status_bar_text,
                ft.Text(VERSION_APP+" | "+platform.system(), size=10)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.SURFACE), # Un color sutil
            border=ft.border.only(top=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT))
        )

        app_bar = ft.AppBar(
            title=ft.Text(f"{APP_NAME} | Simulador de Pases Satelitales NOAA"),
            center_title=False,
            bgcolor=ft.Colors.SURFACE, # Un color sutil
            actions=[
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(text="Sobre APT", on_click=self.show_about_apt_dialog),
                        ft.PopupMenuItem(text="Acerca de...", on_click=self.show_about_app_dialog),
                        ft.PopupMenuItem(), 
                        ft.PopupMenuItem(text="Resetear Todo", icon=ft.Icons.REFRESH, on_click=self.reset_all_processing_state_and_ui)
                    ]
                )
            ]
        )
        self.page.appbar = app_bar

        # === Pestaña 1: Selección de Imágenes ===
        self.img_a_display = ft.Image(src=PLACEHOLDER_IMG_A_COLOR, width=350, height=250, fit=ft.ImageFit.CONTAIN, border_radius=10)
        self.img_a_clickable = ft.GestureDetector(content=self.img_a_display, on_tap=lambda e: self.open_image_in_viewer(e, self.img_a_display))
        self.txt_url_a = ft.TextField(label="URL Imagen A", width=280, hint_text="https://...", on_change=lambda e: self.update_action_buttons_state())
        self.btn_load_url_a = ft.ElevatedButton("Cargar URL A", on_click=lambda e: self.load_url(e, "A", self.txt_url_a, self.img_a_display), icon=ft.Icons.LINK, width=150, disabled=True)
        
        self.img_b_display = ft.Image(src=PLACEHOLDER_IMG_B_COLOR, width=350, height=250, fit=ft.ImageFit.CONTAIN, border_radius=10)
        self.img_b_clickable = ft.GestureDetector(content=self.img_b_display, on_tap=lambda e: self.open_image_in_viewer(e, self.img_b_display))
        self.txt_url_b = ft.TextField(label="URL Imagen B", width=280, hint_text="https://...", on_change=lambda e: self.update_action_buttons_state())
        self.btn_load_url_b = ft.ElevatedButton("Cargar URL B", on_click=lambda e: self.load_url(e, "B", self.txt_url_b, self.img_b_display), icon=ft.Icons.LINK, width=150, disabled=True)

        file_picker_a = ft.FilePicker(on_result=lambda e: self.on_file_picked(e, "A"))
        file_picker_b = ft.FilePicker(on_result=lambda e: self.on_file_picked(e, "B"))
        self.page.overlay.extend([file_picker_a, file_picker_b])

        tab1_content = ft.ListView( expand=True, spacing=15, padding=20,
            controls=[
                ft.Text("1. Selección de Imágenes Fuente", size=20, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.Column([
                            ft.Text("Imagen A", weight=ft.FontWeight.BOLD), self.img_a_clickable,
                            ft.Row([self.txt_url_a, self.btn_load_url_a], alignment=ft.MainAxisAlignment.CENTER, spacing=5,width=450,wrap=True),
                            ft.ElevatedButton("Archivo Local A", icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: file_picker_a.pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "bmp"]), width=self.txt_url_a.width + self.btn_load_url_a.width + 5),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        # ft.VerticalDivider(width=30),
                        ft.Column([
                            ft.Text("Imagen B", weight=ft.FontWeight.BOLD), self.img_b_clickable,
                            ft.Row([self.txt_url_b, self.btn_load_url_b], alignment=ft.MainAxisAlignment.CENTER, spacing=5,width=450,wrap=True),
                            ft.ElevatedButton("Archivo Local B", icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: file_picker_b.pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "bmp"]), width=self.txt_url_b.width + self.btn_load_url_b.width + 5),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND, wrap=True,
                ),
            ]
        )

        # === Pestaña 2: Procesamiento y Generación APT ===
        self.preprocessed_a_display = ft.Image(width=300, height=200, fit=ft.ImageFit.CONTAIN, border_radius=10, src=PLACEHOLDER_PREPROCESSED_A_PENDING)
        self.preprocessed_a_clickable = ft.GestureDetector(content=self.preprocessed_a_display, on_tap=lambda e: self.open_image_in_viewer(e, self.preprocessed_a_display))
        
        self.preprocessed_b_display = ft.Image(width=300, height=200, fit=ft.ImageFit.CONTAIN, border_radius=10, src=PLACEHOLDER_PREPROCESSED_B_PENDING)
        self.preprocessed_b_clickable = ft.GestureDetector(content=self.preprocessed_b_display, on_tap=lambda e: self.open_image_in_viewer(e, self.preprocessed_b_display))

        self.apt_image_display = ft.Image(width=600, height=200, fit=ft.ImageFit.CONTAIN, border_radius=10, src=PLACEHOLDER_APT_PENDING)
        self.apt_image_clickable = ft.GestureDetector(content=self.apt_image_display, on_tap=lambda e: self.open_image_in_viewer(e, self.apt_image_display))
        
        self.audio_status_text = ft.Text("Audio APT: Aún no generado.",text_align=ft.TextAlign.CENTER)

        self.btn_preprocess = ft.ElevatedButton("1. Preprocesar Imágenes", icon=ft.Icons.IMAGE_SEARCH, on_click=self.do_preprocess_all, disabled=True)
        self.btn_encode_apt = ft.ElevatedButton("2. Codificar a APT", icon=ft.Icons.TRANSFORM, on_click=self.do_encode_apt_action, disabled=True)
        self.btn_generate_audio = ft.ElevatedButton("3. Generar Audio APT", icon=ft.Icons.AUDIOTRACK, on_click=self.do_generate_audio_action, disabled=True)
        self.btn_play_audio = ft.ElevatedButton("Reproducir Audio APT", icon=ft.Icons.PLAY_ARROW, on_click=self.play_audio_apt_generated, disabled=True)
        btn_open_output_folder = ft.ElevatedButton("Abrir Carpeta de Salida", icon=ft.Icons.FOLDER_SHARED, on_click=self.open_output_folder)

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
                ft.Container(content=self.apt_image_clickable, alignment=ft.alignment.center),
                ft.Divider(height=10),
                ft.Text("Estado del Audio APT", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Container(content=self.audio_status_text, alignment=ft.alignment.center, padding=10),
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
            on_change=lambda e: self.update_action_buttons_state()
        )

        def slider_input_freq_tx_sdr_changed(e):
            self.slider_freq_tx_sdr.value=round(self.slider_freq_tx_sdr.value,1)
            self.text_value_freq_tx_sdr.value = f"{self.slider_freq_tx_sdr.value} MHz"
            self.page.update()
        
        def slider_samp_rate_sdr_changed(e):
            self.slider_samp_rate_sdr.value=round(self.slider_samp_rate_sdr.value,1)
            self.text_value_samp_rate_sdr.value = f"{self.slider_samp_rate_sdr.value} MHz"
            self.page.update()

        self.text_freq_tx_sdr=ft.Text("Frecuencia de transmisión:")
        self.slider_freq_tx_sdr = ft.Slider(value=928,min=88,max=3000,label="{value} MHz",on_change=slider_input_freq_tx_sdr_changed,divisions=(3000-88))
        self.text_value_freq_tx_sdr=ft.Text(f"{self.slider_freq_tx_sdr.value} MHz")
        
        self.text_samp_rate_sdr=ft.Text("Frecuencia de muestreo SDR (sample rate):")
        self.slider_samp_rate_sdr = ft.Slider(value=8,min=0.2,max=10,label="{value} MHz",
        on_change=slider_samp_rate_sdr_changed,divisions=98)
        self.text_value_samp_rate_sdr=ft.Text(f"{self.slider_samp_rate_sdr.value} MHz")
        
        self.btn_transmit = ft.ElevatedButton("Transmitir con SDR", icon=ft.Icons.SEND, on_click=self.do_transmit_sdr, disabled=True)

        tab3_content = ft.ListView( expand=True, spacing=15, padding=20,
            controls=[
                ft.Text("3. Opciones y Transmisión SDR", size=20, weight=ft.FontWeight.BOLD),
                self.sdr_script_dropdown,
                ft.Text("Parámetros de transmisión para el script:", weight=ft.FontWeight.W_400),
                ft.Row([self.text_freq_tx_sdr,self.text_value_freq_tx_sdr]),
                self.slider_freq_tx_sdr,
                ft.Row([self.text_samp_rate_sdr,self.text_value_samp_rate_sdr]),
                self.slider_samp_rate_sdr,
                ft.Text("Nota: Ajustar parámetros según el SDR a utilizar", italic=True, size=12),
                ft.Divider(height=20),
                ft.Container(content=self.btn_transmit, alignment=ft.alignment.center),
            ]
        )

        main_tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Imágenes Fuente", icon=ft.Icons.COLLECTIONS_BOOKMARK_ROUNDED, content=tab1_content),
                ft.Tab(text="Procesamiento APT", icon=ft.Icons.SETTINGS_APPLICATIONS_ROUNDED, content=tab2_content),
                ft.Tab(text="Transmisión SDR", icon=ft.Icons.SEND_TO_MOBILE_ROUNDED, content=tab3_content),
            ],
            expand=True,
        )

        self.page.add(
            ft.Column(
                controls=[ main_tabs, status_bar ],
                expand=True, spacing=0
            )
        )
        self.update_action_buttons_state()

# --- Main ---
import sys # Necesario para sys.executable y sys.frozen

def main(page: ft.Page):
    # Crear directorios necesarios al inicio
    get_app_files_dir()
    get_scripts_dir()
    
    app_instance = MainApp(page)
    # page.update() # No es necesario, MainApp o sus métodos se encargan

if __name__ == "__main__":
    ft.app(target=main)
