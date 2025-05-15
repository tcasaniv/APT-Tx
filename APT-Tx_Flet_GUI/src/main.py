import flet as ft
import os
import base64 # Para posible manejo de imágenes en base64 si es necesario
import time

# --- Variables globales para almacenar rutas o URLs de imágenes ---
image_a_path = None
image_b_path = None

# --- Funciones Demo (solo actualizan el label de estado) ---

def preprocessing_img(image_name, status_label, preprocessed_image_display, source_image_path):
    status_label.value = f"Preprocesando {image_name}..."
    status_label.page.update()
    # Simulación: simplemente mostramos la misma imagen o una placeholder
    if source_image_path:
        if os.path.exists(source_image_path) or source_image_path.startswith("http"):
             preprocessed_image_display.src = source_image_path
        else: # Podría ser base64
            preprocessed_image_display.src_base64 = source_image_path
    else:
        preprocessed_image_display.src = "https://preview.redd.it/my-best-noaa-apt-recording-so-far-v0-pgx6kastjq6d1.jpg?width=640&crop=smart&auto=webp&s=37e85385995a04651653bb8a96aac5986d8e0abb"
    preprocessed_image_display.page.update()
    status_label.value = f"{image_name} preprocesada."
    status_label.page.update()
    return True # Indicar éxito

def apt_encoding_img(status_label, apt_image_display):
    global image_a_path, image_b_path
    if not image_a_path or not image_b_path:
        status_label.value = "Error: Se necesitan ambas imágenes para codificar a APT."
        status_label.page.update()
        return False

    status_label.value = "Codificando imágenes a formato APT..."
    status_label.page.update()
    time.sleep(2)
    # Simulación: mostramos una imagen APT de ejemplo
    apt_image_display.src = "https://upload.wikimedia.org/wikipedia/commons/5/57/NOAA_19_APT_Image.jpg" # Ejemplo de imagen APT
    # O una placeholder: apt_image_display.src = "https://via.placeholder.com/600x200.png?text=Imagen+APT+Codificada"
    apt_image_display.page.update()
    status_label.value = "Imágenes codificadas a APT."
    status_label.page.update()
    return True

def audio_apt_generation(status_label, audio_status_text):
    status_label.value = "Generando audio APT..."
    status_label.page.update()
    time.sleep(2)
    # Simulación
    audio_status_text.value = "Audio APT generado (simulado). Duración: XX segundos."
    audio_status_text.page.update()
    status_label.value = "Audio APT generado."
    status_label.page.update()
    return True

def sdr_transmission(status_label, options):
    status_label.value = "Preparando transmisión SDR con opciones:"
    for opt, checked in options.items():
        if checked:
            status_label.value += f"\n - {opt}"
    status_label.page.update()
    # Simulación
    status_label.value += "\nTransmitiendo con SDR (simulación)..."
    status_label.page.update()
    # Aquí iría la lógica real de transmisión
    time.sleep(2) # Simular tiempo de transmisión
    status_label.value = "Transmisión SDR (simulada) completada."
    status_label.page.update()

# --- GUI ---
def main(page: ft.Page):
    page.title = "APT-TX | Simulador de pases satelitales NOAA"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE
    

    titleText = ft.Text(value="APT-TX | Simulador de pases satelitales NOAA", color="white", size=16*2)
    page.controls.append(ft.Container(
                    content=titleText,
                    # margin=10,
                    padding=10,
                    bgcolor=ft.Colors.GREY,
                    border_radius=10,
                ))


    # --- Controles de la GUI ---
    status_label = ft.Text("Estado: Listo.", weight=ft.FontWeight.BOLD)

    # --- Selección de Imagen A ---
    img_a_display = ft.Image(
        src="https://image.pollinations.ai/prompt/NOAA%20image%20APT?seed=2118",
        width=300, height=200, fit=ft.ImageFit.CONTAIN,
        # border_radius=ft.border_radius.all(10)
    )
    txt_url_a = ft.TextField(label="URL Imagen A", width=200)
    
    def load_url_a(e):
        global image_a_path
        if txt_url_a.value:
            image_a_path = txt_url_a.value
            img_a_display.src = image_a_path
            status_label.value = "Imagen A cargada desde URL."
            txt_url_a.error_text = ""
            page.update()
            if preprocessing_img("Imagen A", status_label, preprocessed_a_display, image_a_path):
                check_and_encode_apt()
        else:
            txt_url_a.error_text = "Debes ingresar la ruta de la imagen A"
            status_label.value = "Por favor, ingrese una URL para Imagen A."
            page.update()

    # --- Selección de Imagen B ---
    img_b_display = ft.Image(
        src="https://image.pollinations.ai/prompt/NOAA%20image%20APT?seed=1219",
        width=300, height=200, fit=ft.ImageFit.CONTAIN,
        # border_radius=ft.border_radius.all(10)
    )
    txt_url_b = ft.TextField(label="URL Imagen B", width=200)

    def load_url_b(e):
        global image_b_path
        if txt_url_b.value:
            image_b_path = txt_url_b.value
            img_b_display.src = image_b_path
            status_label.value = "Imagen B cargada desde URL."
            page.update()
            if preprocessing_img("Imagen B", status_label, preprocessed_b_display, image_b_path):
                check_and_encode_apt()
        else:
            txt_url_a.error_text = "Debes ingresar la ruta de la imagen B"
            status_label.value = "Por favor, ingrese una URL para Imagen B."
            page.update()

    # --- FilePickers ---
    def on_file_picked_a(e: ft.FilePickerResultEvent):
        global image_a_path
        if e.files and len(e.files) > 0:
            image_a_path = e.files[0].path
            img_a_display.src = image_a_path
            status_label.value = f"Imagen A seleccionada: {e.files[0].name}"
            page.update()
            if preprocessing_img("Imagen A", status_label, preprocessed_a_display, image_a_path):
                check_and_encode_apt()
        else:
            status_label.value = "No se seleccionó archivo para Imagen A."
            page.update()

    def on_file_picked_b(e: ft.FilePickerResultEvent):
        global image_b_path
        if e.files and len(e.files) > 0:
            image_b_path = e.files[0].path
            img_b_display.src = image_b_path
            status_label.value = f"Imagen B seleccionada: {e.files[0].name}"
            page.update()
            if preprocessing_img("Imagen B", status_label, preprocessed_b_display, image_b_path):
                check_and_encode_apt()
        else:
            status_label.value = "No se seleccionó archivo para Imagen B."
            page.update()

    file_picker_a = ft.FilePicker(on_result=on_file_picked_a)
    file_picker_b = ft.FilePicker(on_result=on_file_picked_b)
    page.overlay.extend([file_picker_a, file_picker_b]) # Necesario para FilePicker

    # --- Imágenes Preprocesadas ---
    preprocessed_a_display = ft.Image(
        src="https://preview.redd.it/my-best-noaa-apt-recording-so-far-v0-pgx6kastjq6d1.jpg?width=640&crop=smart&auto=webp&s=37e85385995a04651653bb8a96aac5986d8e0abb",
        width=300, height=200, fit=ft.ImageFit.CONTAIN,
        # border_radius=ft.border_radius.all(10)
    )
    preprocessed_b_display = ft.Image(
        src="https://preview.redd.it/my-best-noaa-apt-recording-so-far-v0-pgx6kastjq6d1.jpg?width=640&crop=smart&auto=webp&s=37e85385995a04651653bb8a96aac5986d8e0abb",
        width=300, height=200, fit=ft.ImageFit.CONTAIN,
        # border_radius=ft.border_radius.all(10)
    )

    # --- Imagen APT Codificada ---
    apt_image_display = ft.Image(
        src="https://upload.wikimedia.org/wikipedia/commons/5/57/NOAA_19_APT_Image.jpg",
        width=600, height=200, fit=ft.ImageFit.CONTAIN,
        # border_radius=ft.border_radius.all(10)
    )

    # --- Audio APT ---
    audio_status_text = ft.Text("Audio APT aún no generado.")

    # --- Función para verificar y codificar ---
    def check_and_encode_apt():
        if image_a_path and image_b_path: # Ambas imágenes deben estar cargadas
            if apt_encoding_img(status_label, apt_image_display):
                audio_apt_generation(status_label, audio_status_text)
    
    # --- Opciones SDR ---
    cb_freq = ft.Checkbox(label="Frecuencia: 137.5 MHz", value=True)
    cb_gain = ft.Checkbox(label="Ganancia: Automática", value=True)
    cb_sample_rate = ft.Checkbox(label="Tasa de Muestreo: 2.048 MS/s", value=False)
    cb_preemphasis = ft.Checkbox(label="Preénfasis activado", value=True)

    # --- Botón de Transmisión ---
    def transmit_clicked(e):
        if not apt_image_display.src or "placeholder" in apt_image_display.src:
             status_label.value = "Error: Primero debe generar la imagen APT."
             page.update()
             return
        
        sdr_options = {
            "Frecuencia 137.5 MHz": cb_freq.value,
            "Ganancia Automática": cb_gain.value,
            "Tasa de Muestreo 2.048 MS/s": cb_sample_rate.value,
            "Preénfasis activado": cb_preemphasis.value
        }
        sdr_transmission(status_label, sdr_options)

    btn_transmit = ft.ElevatedButton("Seleccionar y Transmitir con SDR", on_click=transmit_clicked, icon=ft.Icons.SEND)

    # --- Layout de la GUI ---
    layout = ft.Column(
        [
            ft.Divider(),

            ft.Text("1. Selección de Imágenes Fuente", size=20, weight=ft.FontWeight.BOLD),
            ft.Row(
                [
                    ft.Column([
                        ft.Text("Imagen A"),
                        img_a_display,
                        ft.Row([txt_url_a, ft.ElevatedButton("Cargar URL A", on_click=load_url_a, icon=ft.Icons.LINK)]),
                        ft.ElevatedButton("Seleccionar Archivo Local A", icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: file_picker_a.pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "bmp"])),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(),
                    ft.Column([
                        ft.Text("Imagen B"),
                        img_b_display,
                        ft.Row([txt_url_b, ft.ElevatedButton("Cargar URL B", on_click=load_url_b, icon=ft.Icons.LINK)]),
                        ft.ElevatedButton("Seleccionar Archivo Local B", icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: file_picker_b.pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "bmp"])),
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                vertical_alignment=ft.CrossAxisAlignment.START
            ),
            ft.Divider(),

            ft.Text("2. Imágenes Preprocesadas", size=20, weight=ft.FontWeight.BOLD),
            ft.Row(
                [preprocessed_a_display, preprocessed_b_display],
                alignment=ft.MainAxisAlignment.SPACE_AROUND
            ),
            ft.Divider(),

            ft.Text("3. Imagen Codificada APT", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(content=apt_image_display),
            ft.Divider(),

            ft.Text("4. Audio APT Generado", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(content=audio_status_text),
            ft.Divider(),

            ft.Text("5. Opciones de Transmisión SDR", size=20, weight=ft.FontWeight.BOLD),
            ft.Column(
                [cb_freq, cb_gain, cb_sample_rate, cb_preemphasis],
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.START
            ),
            ft.Divider(),
            
            ft.Container(content=btn_transmit,  padding=20),
            ft.Divider(),
            status_label
        ],
        spacing=15,
        # width=800, # Ancho fijo para mejor control del layout
        alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    page.add(ft.Container(content=layout))
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
