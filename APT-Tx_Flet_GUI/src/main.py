import flet as ft
import os
import time
import platform
import subprocess
import shutil

VERSION_APP="v0.1.0"

# --- Constantes ---
APP_NAME = "APT-Tx_Flet_GUI"
APP_FILES_DIR_NAME = "APT-Tx_Files" # Carpeta para guardar archivos generados

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
# Rutas de las imágenes fuente originales (local o URL)
image_a_source_path = None
image_b_source_path = None

# Rutas a los archivos generados por el procesamiento
preprocessed_a_path_generated = None
preprocessed_b_path_generated = None
generated_apt_image_path = None
generated_wav_path = None


# --- Funciones de Utilidad ---
def get_app_files_dir():
    """Obtiene la ruta a la carpeta de archivos de la aplicación y la crea si no existe."""
    if platform.system() == "Windows":
        # Usualmente Documents
        base_path = os.path.join(os.environ['USERPROFILE'], 'Documents')
    else:
        # Usualmente Home
        base_path = os.path.expanduser('~')
    
    app_dir = os.path.join(base_path, APP_FILES_DIR_NAME)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def open_file_with_default_program(filepath):
    try:
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

# --- Funciones de Lógica (Simuladas) ---
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
    """
    Simula el preprocesamiento de una imagen.
    Guarda una copia o placeholder en el directorio de la app.
    Retorna la ruta al archivo preprocesado generado.
    """
    if not source_image_path_val:
        status_bar_text_ref.value = f"Error: No hay imagen fuente para preprocesar ({image_name_suffix})."
        page.update()
        return None

    status_bar_text_ref.value = f"Preprocesando Imagen {image_name_suffix}..."
    page.update()
    time.sleep(1) # Simular trabajo

    output_filename = f"preprocessed_img_{image_name_suffix}.png"
    generated_file_path = os.path.join(get_app_files_dir(), output_filename)

    # Simulación: Copiar la original o usar un placeholder si es URL (requeriría descarga)
    try:
        if source_image_path_val.startswith("http"):
            # En un caso real, descargaríamos la imagen aquí.
            # Aquí NO guardamos un archivo real desde URL para simplificar la simulación.
            # En su lugar, la imagen preprocesada mostrada será un placeholder.
            preprocessed_image_display_ref.src = PLACEHOLDER_PREPROCESSED_DONE 
            # Para que `update_action_buttons_state` funcione, es mejor tener una ruta.
            # En un caso real, se descargaría y se procesaría.
            # Si queremos que la lógica de "archivo existe" funcione, necesitamos un archivo.
            # Por ahora, la simulación de URL no generará un archivo físico para preprocesamiento.
            # Esto significa que el flujo se detendrá si la fuente es URL.
            if source_image_path_val.startswith("http"): # Si es URL, mostramos placeholder "done" pero no generamos archivo
                preprocessed_image_display_ref.src = PLACEHOLDER_PREPROCESSED_DONE
                status_bar_text_ref.value = f"Imagen {image_name_suffix} (URL) 'preprocesada' (simulado visualmente)."
                page.update()
                return None # No hay archivo local generado para URLs en esta simulación
            else: # Si es local
                shutil.copy(source_image_path_val, generated_file_path)
                preprocessed_image_display_ref.src = generated_file_path # Mostrar el archivo "procesado"
        else: # Es local
            shutil.copy(source_image_path_val, generated_file_path) # Simula "procesamiento" copiando
            preprocessed_image_display_ref.src = generated_file_path # Mostrar el archivo "procesado"
        
        preprocessed_image_display_ref.update()
        status_bar_text_ref.value = f"Imagen {image_name_suffix} preprocesada. Guardada en: {output_filename}"
        page.update()
        return generated_file_path
    except Exception as e:
        status_bar_text_ref.value = f"Error preprocesando Imagen {image_name_suffix}: {e}"
        preprocessed_image_display_ref.src = PLACEHOLDER_PREPROCESSED_A_PENDING if image_name_suffix == "A" else PLACEHOLDER_PREPROCESSED_B_PENDING
        page.update()
        return None


def apt_encoding_img(page: ft.Page, status_label, apt_image_display, 
                     preproc_a_path, preproc_b_path):
    """
    Simula la codificación APT desde dos imágenes preprocesadas.
    Guarda una imagen APT de placeholder en el directorio de la app.
    Retorna la ruta a la imagen APT generada.
    """
    global generated_apt_image_path
    if not preproc_a_path or not preproc_b_path:
        status_label.value = "Error: Se necesitan ambas imágenes preprocesadas para codificar a APT."
        page.update()
        return None

    status_label.value = "Codificando imágenes a formato APT..."
    page.update()
    time.sleep(2)

    output_filename = "apt_encoded_image.png" # Podría ser .jpg o algún otro formato de imagen
    generated_file_path = os.path.join(get_app_files_dir(), output_filename)

    # Simulación: Copiar una imagen de placeholder (o la primera preprocesada)
    try:
        # En una app real, aquí se generaría la imagen APT.
        # Como es URL, no lo vamos a descargar para esta simulación.
        # En su lugar, la imagen mostrada será un placeholder, pero crearemos un archivo dummy para la ruta.
        with open(generated_file_path, "w") as f: # Crear un archivo dummy
            f.write("This is a simulated APT image file.")
        apt_image_display.src = PLACEHOLDER_APT_GENERATED_SIM # Mostrar el placeholder visual
        
        apt_image_display.update()
        status_label.value = f"Imágenes codificadas a APT. Guardada como: {output_filename}"
        page.update()
        generated_apt_image_path = generated_file_path
        return generated_file_path
    except Exception as e:
        status_label.value = f"Error generando imagen APT: {e}"
        page.update()
        generated_apt_image_path = None
        return None

def audio_apt_generation(page: ft.Page, status_label, audio_status_text, apt_img_path_val):
    """
    Simula la generación de audio APT desde una imagen APT.
    Guarda un archivo WAV/MP3 de placeholder en el directorio de la app.
    Retorna la ruta al archivo de audio generado.
    """
    global generated_wav_path
    if not apt_img_path_val:
        status_label.value = "Error: Se necesita una imagen APT para generar el audio."
        page.update()
        generated_wav_path = None # Resetear si falla
        return None

    status_label.value = "Generando audio APT..."
    page.update()
    time.sleep(2)

    output_filename = "apt_generated_audio.wav"
    generated_file_path = os.path.join(get_app_files_dir(), output_filename)

    try:
        # Simulación:
        # Simular duración (si el archivo es real, podrías obtenerla)
        duration_text = "XX:XX"
        if os.path.exists(generated_file_path):
             # Usar una librería para leer duración de WAV real
             # Por ahora, hardcodeado
             duration_text = "03:45 (ejemplo)"

        audio_status_text.value = f"Audio APT generado: {output_filename}. Duración: {duration_text}"
        audio_status_text.page.update() # page.update() actualiza todo, pero esto es más específico
        status_label.value = "Audio APT generado."
        page.update()
        generated_wav_path = generated_file_path
        return generated_file_path
    except Exception as e:
        status_label.value = f"Error generando audio APT: {e}"
        page.update()
        generated_wav_path = None
        return None


def sdr_transmission(page: ft.Page, status_label, wav_to_transmit_path, options):
    if not wav_to_transmit_path or not os.path.exists(wav_to_transmit_path):
        status_label.value = "Error: No hay archivo WAV para transmitir o el archivo no existe."
        page.update()
        return

    status_label.value = "Preparando transmisión SDR con opciones:"
    # Aquí construirías el comando para GNU Radio
    # Por ejemplo: python your_gnuradio_script.py --file {wav_to_transmit_path} ...options...
    
    # Muestra las opciones seleccionadas (ejemplo)
    selected_options_str = []
    for ctrl_name, ctrl_obj in options.items():
        if ctrl_obj.value: # Si el Checkbox está marcado
            selected_options_str.append(ctrl_obj.label)
    if selected_options_str:
        status_label.value += "\nOpciones: " + ", ".join(selected_options_str)
    
    status_label.value += f"\nArchivo de audio: {os.path.basename(wav_to_transmit_path)}"
    page.update()
    
    # Simulación
    status_label.value += "\nIniciando script de transmisión GNU Radio (simulado)..."
    page.update()
    time.sleep(3) # Simular tiempo de transmisión
    status_label.value = "Transmisión SDR completada (simulada)."
    page.update()

# --- GUI ---
class MainApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.setup_ui()
        self.reset_all_processing_state_and_ui(None) # Estado inicial limpio

    def show_about_apt_dialog(self, e):
        about_apt_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Sobre APT (Automatic Picture Transmission)"),
            content=ft.Text(
                "APT es un sistema de transmisión de imágenes analógicas utilizado por algunos satélites meteorológicos,\n"
                "principalmente los de la serie NOAA POES.\n\n"
                "Las imágenes se transmiten en la banda de 137 MHz y pueden ser recibidas con equipamiento SDR relativamente simple.\n"
                "Este programa simula la generación de la señal de audio APT para su posterior transmisión."
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: self.close_dialog(about_apt_dialog))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = about_apt_dialog
        about_apt_dialog.open = True
        self.page.update()

    def show_about_app_dialog(self, e):
        about_app_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Acerca de {APP_NAME}"),
            content=ft.Column(
                [
                    ft.Text(f"Versión: {VERSION_APP}"),
                    ft.Text("Aplicación para generar señales de audio APT para transmisión FM con SDR."),
                    ft.Text("Desarrollado con Flet y Python."),
                    ft.Text("Idea Original: Transmitir imágenes personalizadas vía satélite (simulado).")
                ], tight=True
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda _: self.close_dialog(about_app_dialog))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = about_app_dialog
        about_app_dialog.open = True
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

        # Resetear UI de imágenes
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

        self.status_bar_text.value = "Estado: Listo. Todo reseteado."
        self.update_action_buttons_state()
        self.page.update()

    def load_url(self, e, img_tag, txt_url_ref):
        global image_a_source_path, image_b_source_path
        
        url_val = txt_url_ref.value.strip()
        path_to_set = None
        current_img_display = self.img_a_display if img_tag == "A" else self.img_b_display
        
        if url_val and url_val.startswith(("http://", "https://")):
            path_to_set = url_val
            current_img_display.src = path_to_set
            self.status_bar_text.value = f"Imagen {img_tag} cargada desde URL."
            txt_url_ref.error_text = None
        elif not url_val:
            txt_url_ref.error_text = f"Ingrese una URL para Imagen {img_tag}"
            self.status_bar_text.value = f"URL de Imagen {img_tag} requerida."
            current_img_display.src = PLACEHOLDER_IMG_A_COLOR if img_tag == "A" else PLACEHOLDER_IMG_B_COLOR
        else:
            txt_url_ref.error_text = "URL inválida (debe ser http:// o https://)"
            self.status_bar_text.value = f"URL de Imagen {img_tag} inválida."
            current_img_display.src = PLACEHOLDER_IMG_A_COLOR if img_tag == "A" else PLACEHOLDER_IMG_B_COLOR
        
        if img_tag == "A":
            image_a_source_path = path_to_set
            self.reset_downstream_for_image("A")
        elif img_tag == "B":
            image_b_source_path = path_to_set
            self.reset_downstream_for_image("B")
        
        self.page.update()
        self.update_action_buttons_state()

    def on_file_picked(self, e: ft.FilePickerResultEvent, img_tag):
        global image_a_source_path, image_b_source_path
        
        path_to_set = None
        current_img_display = self.img_a_display if img_tag == "A" else self.img_b_display
        txt_url_ref = self.txt_url_a if img_tag == "A" else self.txt_url_b

        if e.files and len(e.files) > 0:
            path_to_set = e.files[0].path
            current_img_display.src = path_to_set # Muestra la imagen local
            self.status_bar_text.value = f"Imagen {img_tag} seleccionada: {os.path.basename(path_to_set)}"
            txt_url_ref.value = "" # Limpiar campo URL
            txt_url_ref.error_text = None
        else:
            self.status_bar_text.value = f"No se seleccionó archivo para Imagen {img_tag}."
            # No cambiar la imagen si se cancela, o volver a placeholder si no había nada
            if (img_tag == "A" and not image_a_source_path) or \
               (img_tag == "B" and not image_b_source_path):
                current_img_display.src = PLACEHOLDER_IMG_A_COLOR if img_tag == "A" else PLACEHOLDER_IMG_B_COLOR

        if img_tag == "A":
            image_a_source_path = path_to_set
            self.reset_downstream_for_image("A")
        elif img_tag == "B":
            image_b_source_path = path_to_set
            self.reset_downstream_for_image("B")

        self.page.update()
        self.update_action_buttons_state()

    def reset_downstream_for_image(self, img_tag: str):
        """Resetea el estado de procesamiento para una imagen específica y lo que sigue."""
        global preprocessed_a_path_generated, preprocessed_b_path_generated
        global generated_apt_image_path, generated_wav_path

        if img_tag == "A":
            preprocessed_a_path_generated = None
            self.preprocessed_a_display.src = PLACEHOLDER_PREPROCESSED_A_PENDING
        elif img_tag == "B":
            preprocessed_b_path_generated = None
            self.preprocessed_b_display.src = PLACEHOLDER_PREPROCESSED_B_PENDING
        
        # Si cualquier imagen fuente cambia, el APT y el audio deben regenerarse
        generated_apt_image_path = None
        generated_wav_path = None
        self.apt_image_display.src = PLACEHOLDER_APT_PENDING
        self.audio_status_text.value = "Audio APT: Aún no generado."
        
        self.preprocessed_a_display.update()
        self.preprocessed_b_display.update()
        self.apt_image_display.update()
        self.audio_status_text.update()
        self.update_action_buttons_state()


    def do_preprocess_all(self, e):
        global preprocessed_a_path_generated, preprocessed_b_path_generated
        if not image_a_source_path or not image_b_source_path:
            self.status_bar_text.value = "Error: Ambas imágenes A y B deben estar cargadas."
            self.page.update()
            return
        
        # Preprocesar A
        preprocessed_a_path_generated = preprocessing_img(self.page, "A", self.status_bar_text, 
                                                          self.preprocessed_a_display, image_a_source_path)
        # Preprocesar B
        preprocessed_b_path_generated = preprocessing_img(self.page, "B", self.status_bar_text, 
                                                          self.preprocessed_b_display, image_b_source_path)
        
        if preprocessed_a_path_generated and preprocessed_b_path_generated:
            self.status_bar_text.value = "Ambas imágenes preprocesadas (simulado)."
        elif image_a_source_path.startswith("http") or image_b_source_path.startswith("http"):
             self.status_bar_text.value = "Preprocesamiento (simulado) para URLs solo visual. Se requieren archivos locales para continuar."
        else:
            self.status_bar_text.value = "Error durante el preprocesamiento de una o ambas imágenes."

        # Si alguna imagen era URL, preprocessed_X_path_generated será None
        # Esto se manejará en update_action_buttons_state
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
        if generated_wav_path and os.path.exists(generated_wav_path):
            if open_file_with_default_program(generated_wav_path):
                self.status_bar_text.value = f"Intentando reproducir: {os.path.basename(generated_wav_path)}"
            else:
                self.status_bar_text.value = f"Error al intentar abrir: {os.path.basename(generated_wav_path)}"
        else:
            self.status_bar_text.value = "No hay archivo de audio generado o la ruta no es válida."
        self.page.update()

    def open_output_folder(self, e):
        output_dir = get_app_files_dir()
        if open_file_with_default_program(output_dir):
            self.status_bar_text.value = f"Abriendo carpeta: {output_dir}"
        else:
            self.status_bar_text.value = f"No se pudo abrir la carpeta: {output_dir}"
        self.page.update()
    
    def do_transmit_sdr(self, e):
        sdr_options = {
            "freq": self.cb_freq,
            "gain": self.cb_gain,
            "sample_rate": self.cb_sample_rate,
            "preemphasis": self.cb_preemphasis,
        }
        sdr_transmission(self.page, self.status_bar_text, generated_wav_path, sdr_options)
        self.page.update()


    def update_action_buttons_state(self):
        # Habilitar Preprocesar si ambas imágenes fuente están cargadas
        # Y si son locales (la simulación actual de preproc no genera archivo para URLs)
        # OJO: Si una es URL y otra local, preproc fallará en esta simulación.
        # Para que funcione, ambas deben ser locales.
        can_preprocess_A = image_a_source_path is not None and not image_a_source_path.startswith("http")
        can_preprocess_B = image_b_source_path is not None and not image_b_source_path.startswith("http")
        
        self.btn_preprocess.disabled = not (image_a_source_path and image_b_source_path)
        # Si una de las fuentes es URL, avisamos que preproc no generará archivo para esa.
        # Y el botón de encode APT dependerá de si se generaron archivos locales.

        # Habilitar Codificar a APT si ambas imágenes preprocesadas existen
        self.btn_encode_apt.disabled = not (preprocessed_a_path_generated and os.path.exists(preprocessed_a_path_generated) and \
                                           preprocessed_b_path_generated and os.path.exists(preprocessed_b_path_generated))

        # Habilitar Generar Audio si la imagen APT ha sido generada y existe
        self.btn_generate_audio.disabled = not (generated_apt_image_path and os.path.exists(generated_apt_image_path))

        # Habilitar Reproducir Audio si el WAV ha sido generado y existe
        self.btn_play_audio.disabled = not (generated_wav_path and os.path.exists(generated_wav_path))
            
        # Habilitar Transmitir si el WAV ha sido generado y existe
        self.btn_transmit.disabled = not (generated_wav_path and os.path.exists(generated_wav_path))

        self.page.update()


    def setup_ui(self):
        self.page.title = "APT-TX | Simulador de pases satelitales NOAA"
        self.page.window_width = 1050
        self.page.window_height = 800
        self.page.padding = 0
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # --- Barra de Estado ---
        self.status_bar_text = ft.Text("Estado: Listo.", expand=True, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS)
        status_bar = ft.Container(
            content=ft.Row([
                self.status_bar_text,
                ft.Text(VERSION_APP, size=10)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.SURFACE),
            border=ft.border.only(top=ft.border.BorderSide(1, ft.Colors.OUTLINE_VARIANT))
        )

        # --- AppBar ---
        app_bar = ft.AppBar(
            title=ft.Text("APT-TX | Simulador de Pases Satelitales NOAA"),
            center_title=False,
            bgcolor=ft.Colors.SURFACE,
            actions=[
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(text="Sobre APT", on_click=self.show_about_apt_dialog),
                        ft.PopupMenuItem(text="Acerca de...", on_click=self.show_about_app_dialog),
                        ft.PopupMenuItem(), # Divisor
                        ft.PopupMenuItem(text="Resetear Todo", icon=ft.Icons.REFRESH, on_click=self.reset_all_processing_state_and_ui)
                    ]
                )
            ]
        )
        self.page.appbar = app_bar

        # --- Controles de la GUI ---
        # == Pestaña 1: Selección y Previsualización de Imágenes ==
        self.img_a_display = ft.Image(
            src=PLACEHOLDER_IMG_A_COLOR, width=350, height=250, fit=ft.ImageFit.CONTAIN, border_radius=10
        )
        self.txt_url_a = ft.TextField(label="URL Imagen A", width=280, hint_text="https://...")
        
        self.img_b_display = ft.Image(
            src=PLACEHOLDER_IMG_B_COLOR, width=350, height=250, fit=ft.ImageFit.CONTAIN, border_radius=10
        )
        self.txt_url_b = ft.TextField(label="URL Imagen B", width=280, hint_text="https://...")

        file_picker_a = ft.FilePicker(on_result=lambda e: self.on_file_picked(e, "A"))
        file_picker_b = ft.FilePicker(on_result=lambda e: self.on_file_picked(e, "B"))
        self.page.overlay.extend([file_picker_a, file_picker_b])

        tab1_content = ft.ListView(
            expand=True, spacing=20, padding=20,
            controls=[
                ft.Text("1. Selección de Imágenes Fuente", size=20, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.Column([
                            ft.Text("Imagen A", weight=ft.FontWeight.BOLD), self.img_a_display,
                            ft.Row([self.txt_url_a, ft.ElevatedButton("Cargar URL A", on_click=lambda e: self.load_url(e, "A", self.txt_url_a), icon=ft.Icons.LINK, width=150)], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
                            ft.ElevatedButton("Archivo Local A", icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: file_picker_a.pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "bmp"]), width=self.txt_url_a.width + 150 + 5), # Ajustar ancho
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        ft.VerticalDivider(width=20),
                        ft.Column([
                            ft.Text("Imagen B", weight=ft.FontWeight.BOLD), self.img_b_display,
                            ft.Row([self.txt_url_b, ft.ElevatedButton("Cargar URL B", on_click=lambda e: self.load_url(e, "B", self.txt_url_b), icon=ft.Icons.LINK, width=150)], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
                            ft.ElevatedButton("Archivo Local B", icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: file_picker_b.pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "bmp"]), width=self.txt_url_b.width + 150 + 5),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, vertical_alignment=ft.CrossAxisAlignment.START, wrap=False # Evitar wrap aquí
                ),
            ]
        )

        # == Pestaña 2: Procesamiento y Generación APT ==
        self.preprocessed_a_display = ft.Image(width=300, height=200, fit=ft.ImageFit.CONTAIN, border_radius=10, src=PLACEHOLDER_PREPROCESSED_A_PENDING)
        self.preprocessed_b_display = ft.Image(width=300, height=200, fit=ft.ImageFit.CONTAIN, border_radius=10, src=PLACEHOLDER_PREPROCESSED_B_PENDING)
        self.apt_image_display = ft.Image(width=600, height=200, fit=ft.ImageFit.CONTAIN, border_radius=10, src=PLACEHOLDER_APT_PENDING)
        self.audio_status_text = ft.Text("Audio APT: Aún no generado.",text_align=ft.TextAlign.CENTER)

        self.btn_preprocess = ft.ElevatedButton("1. Preprocesar Imágenes", icon=ft.Icons.IMAGE_SEARCH, on_click=self.do_preprocess_all, disabled=True)
        self.btn_encode_apt = ft.ElevatedButton("2. Codificar a APT", icon=ft.Icons.TRANSFORM, on_click=self.do_encode_apt_action, disabled=True)
        self.btn_generate_audio = ft.ElevatedButton("3. Generar Audio APT", icon=ft.Icons.AUDIOTRACK, on_click=self.do_generate_audio_action, disabled=True)
        self.btn_play_audio = ft.ElevatedButton("Reproducir Audio APT", icon=ft.Icons.PLAY_ARROW, on_click=self.play_audio_apt_generated, disabled=True)
        btn_open_output_folder = ft.ElevatedButton("Abrir Carpeta de Salida", icon=ft.Icons.FOLDER_SHARED, on_click=self.open_output_folder)

        tab2_content = ft.ListView(
            expand=True, spacing=15, padding=20,
            controls=[
                ft.Text("2. Procesamiento y Generación APT", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([self.btn_preprocess, self.btn_encode_apt, self.btn_generate_audio], alignment=ft.MainAxisAlignment.CENTER, spacing=10, wrap=True),
                ft.Divider(height=10),
                ft.Text("Previsualización Preprocesadas", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Row(
                    [
                        ft.Column([ft.Text("Imagen A Preprocesada"), self.preprocessed_a_display], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Column([ft.Text("Imagen B Preprocesada"), self.preprocessed_b_display], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND, wrap=True
                ),
                ft.Divider(height=10),
                ft.Text("Imagen Codificada APT", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                ft.Container(content=self.apt_image_display, alignment=ft.alignment.center),
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

        # == Pestaña 3: Transmisión SDR ==
        self.cb_freq = ft.Checkbox(label="Frecuencia: 137.5 MHz (NOAA 15/18)", value=True)
        self.cb_gain = ft.Checkbox(label="Ganancia: Automática", value=True)
        self.cb_sample_rate = ft.Checkbox(label="Tasa de Muestreo: Ajustar en GRC", value=False, disabled=True) # Típicamente no se cambia desde aquí
        self.cb_preemphasis = ft.Checkbox(label="Preénfasis activado (Recomendado)", value=True)
        self.btn_transmit = ft.ElevatedButton("Transmitir con SDR", icon=ft.Icons.SEND, on_click=self.do_transmit_sdr, disabled=True)

        tab3_content = ft.ListView(
            expand=True, spacing=15, padding=20,
            controls=[
                ft.Text("3. Opciones y Transmisión SDR", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Configuración del Transmisor (Ejemplos):", weight=ft.FontWeight.W_400),
                self.cb_freq, self.cb_gain, self.cb_sample_rate, self.cb_preemphasis,
                ft.Text("Nota: Los parámetros exactos se configurarán en el script de GNU Radio Companion.", italic=True, size=12),
                ft.Divider(height=20),
                ft.Container(content=self.btn_transmit, alignment=ft.alignment.center),
            ]
        )

        # --- Pestañas (Tabs) ---
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

        # --- Estructura Principal de la Página ---
        self.page.add(
            ft.Column(
                controls=[
                    main_tabs,
                    status_bar
                ],
                expand=True,
                spacing=0
            )
        )
        self.update_action_buttons_state() # Estado inicial de los botones

def main(page: ft.Page):
    # Crear directorio de archivos de la app al inicio
    get_app_files_dir()
    # Crear instancia de la clase principal de la app
    app_instance = MainApp(page)
    # page.update() # No es necesario aquí, MainApp se encarga

if __name__ == "__main__":
    ft.app(target=main)
