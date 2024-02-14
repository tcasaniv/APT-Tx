#-*- coding:utf-8 -*-
from tkinter import *
from tkinter import ttk
#@markdown # Descargar imagen a transmitir
import os
import requests

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image as Img
import scipy.io.wavfile as wav
import scipy.signal as sps

def create_directory_if_not_exists(path:str):
    """
    Verificar y crear el directorio de salida si no existe
    :param path: Ruta del directorio a comprobar si existe.
    """
    try:
        directorio_salida = os.path.dirname(path)
        if not os.path.exists(directorio_salida):
            os.makedirs(directorio_salida)
            print(f"Se creó el directorio: {directorio_salida}")
    except OSError as e:
        print(f"Error al crear el directorio: {e}")

def download_from_url(url: str, path_save_file: str = None):
    """
    Descarga un recurso desde una URL.
    :param url: URL del recurso web.
    :param path_save_file: Ruta y nombre donde guardar el archivo.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanza una excepción en caso de error HTTP

        if path_save_file is None:
            # Obtener el nombre del archivo de la URL
            file_name = url.split("/")[-1]
            # Construir la ruta por defecto
            path_save_file = os.path.join("./Files_download", file_name)
        
        create_directory_if_not_exists(path_save_file)

        with open(path_save_file, 'wb') as file:
            print(f"Descargando recurso:\n{path_save_file}")
            file.write(response.content)
            print("Recurso descargado correctamente.")

    except requests.exceptions.RequestException as e:
        print(f"Error al descargar el recurso: {e}") 

def btn_download_imgs():
    print("|-------- Descargando imágenes --------|")
    imagen_tx_A = download_imgA.get()
    imagen_tx_B = download_imgB.get()
    # imagen_tx = "https://www.unsa.edu.pe/wp-content/uploads/2022/02/FACHADA-UNSA3-878x426.jpg"
    # imagen_tx = "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/de9bb908-43b8-493a-b337-6733ab64bf8e/original=true/1.jpeg" # @param {type:"string"}
    # ruta_guardar_img = './Files/Image1.jpeg'  # @param {type:"string"}

    # create_directory_if_not_exists(ruta_guardar_img)
    download_from_url(imagen_tx_A,download_directory_A.get())
    download_from_url(imagen_tx_B,download_directory_B.get())


def reescalar_img(PIL_img,ancho_deseado = 909):
    """
    Reescalar la imagen a 909 px de ancho (el alto se ajustará automáticamente para mantener la proporción)
    """
    proporcion = ancho_deseado / float(PIL_img.size[0])
    alto_deseado = int(float(PIL_img.size[1]) * float(proporcion))
    imagen_reescalada   = PIL_img.resize((ancho_deseado, alto_deseado), Img.Resampling.LANCZOS)
    print(f"Tamaño de la imagen original: {PIL_img.size}")
    print(f"Tamaño de la imagen reescalada: {imagen_reescalada.size}")
    return imagen_reescalada

def convertir_img_a_grises(PIL_img):
    """
    Convertir imagen a escala de grises
    """
    imagen_gris = PIL_img.convert('L')
    print(f"Imagen convertida a escala de grises")
    return imagen_gris


def preprocesar_img_to_APT(ruta_entrada_img: str) -> str:
    """
    Convierte una imagen al formato y tamaño adecuado para transmisión APT.
    Retorna el path de la imagen preprocesada.

    :param ruta_entrada_img: Ruta de la imagen a preparar para transmitir por APT.
    :return ruta de la imagen preprocesada.
    """
    # Abrir la imagen
    try:
        imagen = Img.open(ruta_entrada_img)
    except Exception as e:
        print(f"No se pudo abrir la imagen. Error: {e}")
        return  # Sal del método si no se puede abrir la imagen
    
    print(f"Imagen:\n{ruta_entrada_img}\n")
    
    # Obtener nombre, extensión y path del archivo
    nombre_archivo = os.path.basename(ruta_entrada_img)
    directorio_archivo = os.path.dirname(ruta_entrada_img)
    nombre_sin_extension, extension = os.path.splitext(nombre_archivo)

    # Reescalar y convertir a escala de grises
    img_reescalada = reescalar_img(imagen,909)
    imagen_gris = convertir_img_a_grises(img_reescalada)

    # Crea la ruta para guardar la imagen
    ruta_directorio_salida = os.path.join(os.path.dirname(directorio_archivo), preprocessed_directory.get())
    print(f"ruta_directorio_salida: {ruta_directorio_salida}")
    
    img_salida_reescalada = f'{nombre_sin_extension}_reescalada.png'
    img_salida = f'{nombre_sin_extension}_reescalada_gris.png'

    ruta_salida_img_reescalada = os.path.join(ruta_directorio_salida, img_salida_reescalada)
    ruta_salida_img = os.path.join(ruta_directorio_salida, img_salida)
    create_directory_if_not_exists(ruta_salida_img)
    
    # Guardar la imagen preprocesada
    img_reescalada.save(ruta_salida_img_reescalada)
    imagen_gris.save(ruta_salida_img)
    print(f"Imagen preprocesada para formato APT guardada en:\n{ruta_salida_img}\n")
    return ruta_salida_img


# Codificar imagen en APT
def apt_encoder():
    print("|-------- APT Encoder --------|")
	
    #@markdown # Elegir imágenes a codificar en APT

    #@markdown Imagen para el canal A:
    imagen_A = input_imgA.get()
    # Reescalar y convertir a escala de grises la Imagen A
    ruta_img_APT_A = preprocesar_img_to_APT(imagen_A)

    #@markdown Imagen para el canal B:
    imagen_B = input_imgB.get()
    # Reescalar y convertir a escala de grises la Imagen B
    ruta_img_APT_B = preprocesar_img_to_APT(imagen_B)

    #@markdown Ruta donde guardar audio APT e imagen a transmitir:
    path_salida_APT = output_directory.get()
    create_directory_if_not_exists(path_salida_APT)
    #@markdown Samplerate para el audio APT:
    sample_rate_audio = 11025 # 11025 Hz


    

    output_sample_rate = int(sample_rate_audio)

    # Cargar las imágenes de vídeo A y vídeo B
    videoA_image = Img.open(ruta_img_APT_A)
    videoB_image = Img.open(ruta_img_APT_B)



    # Convertir la imagen en una matriz de 256 niveles de cada línea de píxeles, es decir, una matriz 2D de array[row][col].
    videoA_pixels = np.asarray(videoA_image)
    videoB_pixels = np.asarray(videoB_image)

    # Definir las palabras de sincronización para las imágenes A y B
    SYNCA = "000011001100110011001100110011000000000"
    SYNCB = "000011100111001110011100111001110011100"

    # Convierte las palabras de sincronización en listas
    syncA_array = [int(bit) for bit in SYNCA]
    syncB_array = [int(bit) for bit in SYNCB]

    # Generar una línea de los píxeles de sincronización
    syncA_pixels = np.array(syncA_array, dtype=np.int8) * 255
    syncB_pixels = np.array(syncB_array, dtype=np.int8) * 255

    # Generar una línea de los píxeles espaciales
    spaceA_pixels = np.zeros(47, dtype=np.int8)
    spaceB_pixels = np.ones(47, dtype=np.int8) * 255

    # Crear una matriz vacía para nuestra imagen final
    image_pixels = np.zeros(shape=(videoA_image.height, 2080))

    # Recorre cada línea de píxeles para crear la imagen final
    for line in range(0, videoA_image.height):
        minute_marker = line % 120 == 0 # esta línea contendrá un marcador de minutos en los espacios

        # Telemetría
        telemetry_block = (line // 8) % 16

        if telemetry_block < 8:
            block_color = 32 * (telemetry_block)
            telemetryA_pixels = np.ones(45, dtype=np.int8) * block_color
            telemetryB_pixels = np.ones(45, dtype=np.int8) * block_color

        elif telemetry_block == 8:
            telemetryA_pixels = np.zeros(45, dtype=np.int8)
            telemetryB_pixels = np.zeros(45, dtype=np.int8)

        else:
            telemetryA_pixels = np.ones(45, dtype=np.int8) * 128
            telemetryB_pixels = np.ones(45, dtype=np.int8) * 128

        # Concatenar para hacer una fila entera de la imagen
        row = np.concatenate((syncA_pixels, spaceB_pixels if minute_marker else spaceA_pixels, videoA_pixels[line], telemetryA_pixels, syncB_pixels, spaceA_pixels if minute_marker else spaceB_pixels, videoB_pixels[line], telemetryB_pixels))

        # Cambia la fila vacía de la imagen por la fila recién concatenada
        image_pixels[line] = row


    # Vuelve a convertir la matriz de píxeles en una imagen PIL
    image_pixels = image_pixels.astype(np.uint8)
    imageTx = Img.fromarray(image_pixels)

    # Guarda la imagen generada
    image_filepath = f"{path_salida_APT}_.png"
    imageTx.save(image_filepath)




    # Aplanar la matriz de píxeles de la imagen a una matriz 1D y normalizarla
    image_pixels = np.asarray(imageTx).flatten() / 255

    # Generar una onda portadora a 2400 Hz
    sample_rate = 2080 * 20
    duration = 0.5 * imageTx.height
    n_samples = int(duration * sample_rate)

    time = np.linspace(0, duration, n_samples)
    carrier = 1023 * np.sin(2 * np.pi * 2400 * time)

    # Escala la señal para que coincida con el número de muestra de la portadora
    scale = n_samples // len(image_pixels)
    signal = np.repeat(image_pixels, scale)

    # Modula en amplitud la portadora con la señal de 256 niveles.
    modulated = carrier * signal



    # Remuestrea el audio a la velocidad deseada
    sample_rate = output_sample_rate
    n_samples = int(sample_rate * duration)
    modulated = sps.resample(modulated, n_samples)


    # Guardar el audio como archivo WAV
    modulated_int16 = modulated.astype(np.int16)
    wav.write(f"{path_salida_APT}.wav", sample_rate, modulated_int16)
    print(f"\nGuardado en:\n{path_salida_APT}.wav\n")

######################### Instancia de la clase Tk #########################

ventana = Tk()
ventana.title('APT Encoder')

######################### Configuración de geometría #########################
ventana.columnconfigure(0, weight=1)
ventana.rowconfigure(0, weight=1)

frame_download_imgs = ttk.Frame(ventana, padding=10)
frame_download_imgs.grid(row=0, column=0, sticky="nsew")

frame_apt_encoder = ttk.Frame(ventana, padding=10)
frame_apt_encoder.grid(row=1, column=0, sticky="nsew")

######################### Descargar Imagen #########################
etiqueta_download_title = Label(frame_download_imgs, text='Descargar desde URL')
etiqueta_download_title.grid(row=1, column=1,columnspan=3)

# Imagen A a descargar
etiqueta_download_imgA = Label(frame_download_imgs, text='Imagen A:', width=20)
etiqueta_download_imgA.grid(row=2, column=1)
download_imgA = StringVar()
download_imgA.set("https://www.unsa.edu.pe/wp-content/uploads/2022/02/FACHADA-UNSA3-878x426.jpg")
entrada_download_imgA = Entry(frame_download_imgs, textvariable=download_imgA,width=60)
entrada_download_imgA.grid(row=2, column=2, columnspan=2, sticky="ew")

# Directorio de guardado imagen A
etiqueta_download_directory_A = Label(frame_download_imgs, text='Directorio de Descarga: ', width=20)
etiqueta_download_directory_A.grid(row=3, column=1)
download_directory_A = StringVar(value="./Files_download/img_A.jpg")
entrada_download_directory_A = Entry(frame_download_imgs, textvariable=download_directory_A,width=60)
entrada_download_directory_A.grid(row=3, column=2, sticky="ew")

# Imagen B a descargar
etiqueta_download_imgB = Label(frame_download_imgs, text='Imagen B:', width=20)
etiqueta_download_imgB.grid(row=4, column=1)
download_imgB = StringVar()
download_imgB.set("https://www.unsa.edu.pe/wp-content/uploads/2022/02/FACHADA-UNSA3-878x426.jpg")
entrada_download_imgB = Entry(frame_download_imgs, textvariable=download_imgB,width=60)
entrada_download_imgB.grid(row=4, column=2, sticky="ew")

# Directorio de guardado imagen B
etiqueta_download_directory_B = Label(frame_download_imgs, text='Directorio de Descarga: ', width=20)
etiqueta_download_directory_B.grid(row=5, column=1)
download_directory_B = StringVar(value="./Files_download/img_B.jpg")
entrada_download_directory_B = Entry(frame_download_imgs, textvariable=download_directory_B,width=60)
entrada_download_directory_B.grid(row=5, column=2, sticky="ew")

# Botón Descargar
btn_download = Button(frame_download_imgs, text='Descargar imágenes', command=btn_download_imgs)
btn_download.grid(row=6, column=1,columnspan=3, sticky="ew")



######################### APT Encoder #########################

etiqueta_apt_title = Label(frame_apt_encoder, text='APT Encoder')
etiqueta_apt_title.grid(row=9, column=1,columnspan=3)



# Generación de widgets APT Encoder
# Imagen A de entrada
etiqueta_input_imgA = Label(frame_apt_encoder, text='Imagen A:', width=20)
etiqueta_input_imgA.grid(row=10, column=1)
input_imgA = StringVar(value='./Files/Image1.jpeg')
entrada_input_imgA = Entry(frame_apt_encoder, textvariable=input_imgA,width=60)
entrada_input_imgA.grid(row=10, column=2, sticky="ew")

# Imagen B de entrada
etiqueta_input_imgB = Label(frame_apt_encoder, text='Imagen B:', width=20)
etiqueta_input_imgB.grid(row=12, column=1)
input_imgB = StringVar(value='./Files/Image1.jpeg')
entrada_input_imgB = Entry(frame_apt_encoder, textvariable=input_imgB,width=60)
entrada_input_imgB.grid(row=12, column=2, sticky="ew")

# Directorio de preprocesamiento
etiqueta_preprocessed_directory = Label(frame_apt_encoder, text='Directorio de Preprocesamiento: ', width=20)
etiqueta_preprocessed_directory.grid(row=14, column=1)
preprocessed_directory = StringVar(value='./Files_preprocessed')
entrada_preprocessed_directory = Entry(frame_apt_encoder, textvariable=preprocessed_directory,width=60)
entrada_preprocessed_directory.grid(row=14, column=2, sticky="ew")

# Directorio de Salida
etiqueta_output_directory = Label(frame_apt_encoder, text='Directorio de Salida: ', width=20)
etiqueta_output_directory.grid(row=16, column=1)
output_directory = StringVar(value='./Files_Tx/imagen_APT_Tx')
entrada_output_directory = Entry(frame_apt_encoder, textvariable=output_directory,width=60)
entrada_output_directory.grid(row=16, column=2, sticky="ew")


#Botón APT Encoder
boton = Button(frame_apt_encoder, text='Iniciar', command=apt_encoder)
boton.grid(row=19, column=1,columnspan=3, sticky="ew")

#ejecución de ventana
ventana.mainloop()