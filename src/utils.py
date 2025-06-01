import time
from PIL import Image as Img
import numpy as np
import scipy.signal as sps
import scipy.io.wavfile as wav

def reescalar_img(PIL_img:Img,ancho_deseado:int = 909, image_name_suffix:str = "") -> Img:
    """
    Reescalar la imagen a 909 px de ancho (el alto se ajustará automáticamente para mantener la proporción)
    """
    proporcion = ancho_deseado / float(PIL_img.size[0])
    alto_deseado = int(float(PIL_img.size[1]) * float(proporcion))
    imagen_reescalada   = PIL_img.resize((ancho_deseado, alto_deseado), Img.Resampling.LANCZOS)
    print(f"Tamaño de la imagen {image_name_suffix} original: {PIL_img.size}")
    print(f"Tamaño de la imagen {image_name_suffix} reescalada: {imagen_reescalada.size}")
    return imagen_reescalada

def convertir_img_a_grises(PIL_img:Img, image_name_suffix:str = "") -> Img:
    """
    Convertir imagen a escala de grises
    """
    imagen_gris = PIL_img.convert('L')
    print(f"Imagen {image_name_suffix} convertida a escala de grises")
    return imagen_gris


def preprocesar_img_to_APT(ruta_entrada_img:str, ruta_salida_img: str,image_name_suffix:str = "") -> str:
    """
    Convierte una imagen al formato y tamaño adecuado para transmisión APT.

    :param ruta_entrada_img: Ruta de la imagen a preparar para transmitir por APT.
    :return ruta de la imagen preprocesada.
    """
    print("|-------- Preprocesar Imagen --------|")
    start_time = time.perf_counter() # Inicia el cronómetro
    print("Abriendo imagen para preprocesar...")
    # Abrir la imagen
    try:
        imagen = Img.open(ruta_entrada_img)
    except Exception as e:
        print(f"No se pudo abrir la imagen. Error: {e}")
        return  # Sal del método si no se puede abrir la imagen
    
    print(f"Imagen:\n{ruta_entrada_img}\n")

    # Reescalar y convertir a escala de grises
    img_reescalada = reescalar_img(imagen,909,image_name_suffix)
    imagen_gris = convertir_img_a_grises(img_reescalada,image_name_suffix)
    
    # Guardar la imagen preprocesada
    # img_reescalada.save(ruta_salida_img_reescalada)
    imagen_gris.save(ruta_salida_img)
    print(f"Imagen {image_name_suffix} preprocesada para formato APT guardada en:\n{ruta_salida_img}\n")
    end_time = time.perf_counter() # Detiene el cronómetro
    processing_time = end_time - start_time
    # Usamos alto_deseado de la función reescalar_img, que se corresponde con imagen_gris.size[1]
    lines_processed = imagen_gris.size[1] 
    
    print(f"Tiempo total de preprocesamiento: {processing_time:.4f} segundos")
    if processing_time > 0:
        lines_per_second = lines_processed / processing_time
        print(f"Rendimiento: {lines_per_second:.2f} líneas procesadas por segundo\n") # Imprime la duración y métrica
    else:
        print("Rendimiento: Demasiado rápido para medir o cero líneas procesadas.\n")
    

# Codificar imagen en APT
def apt_encoder(preproc_a_path:Img, preproc_b_path:Img, output_APT_img_path:str):
    print("|-------- APT Encoder --------|")
    start_time = time.perf_counter() # Inicia el cronómetro
    print("Abriendo imágenes preprocesadas para codificación APT...")

    # Abrir la imagen
    try:
        PIL_imgA = Img.open(preproc_a_path)
        PIL_imgB = Img.open(preproc_b_path)
        print(f"Imagen A cargada: {preproc_a_path} tamaño: {PIL_imgA.size}")
        print(f"Imagen B cargada: {preproc_b_path} tamaño: {PIL_imgB.size}")
    except Exception as e:
        print(f"No se pudo abrir las imágenes. Error: {e}")
        return  # Sal del método si no se puede abrir las imágenes

    # Convertir la imagen en una matriz de 256 niveles de cada línea de píxeles, es decir, una matriz 2D de array[row][col].
    print("Convirtiendo imágenes a matrices numpy...")
    videoA_pixels = np.asarray(PIL_imgA)
    videoB_pixels = np.asarray(PIL_imgB)

    # Definir las palabras de sincronización para las imágenes A y B
    print("Definiendo palabras de sincronización para las imágenes A y B...")
    SYNCA = "000011001100110011001100110011000000000"
    SYNCB = "000011100111001110011100111001110011100"

    # Convierte las palabras de sincronización en listas
    syncA_array = [int(bit) for bit in SYNCA]
    syncB_array = [int(bit) for bit in SYNCB]

    # Generar una línea de los píxeles de sincronización
    syncA_pixels = np.array(syncA_array, dtype=np.int16) * 255
    syncB_pixels = np.array(syncB_array, dtype=np.int16) * 255

    # Generar una línea de los píxeles espaciales
    spaceA_pixels = np.zeros(47, dtype=np.int16)
    spaceB_pixels = np.ones(47, dtype=np.int16) * 255

    # Definir la altura de la imagen APT elegiendo la menor altura entre las dos imágenes
    height_APT_image = min(PIL_imgA.height, PIL_imgB.height)
    print(f"Altura de la imagen APT: {height_APT_image} (mínimo entre ambas imágenes)")

    # Crear una matriz vacía para nuestra imagen final
    print("Creando matriz vacía para la imagen APT final...")
    image_pixels = np.zeros(shape=(height_APT_image, 2080))

    print("Comenzando a construir cada línea de la imagen APT...")
    # Recorre cada línea de píxeles para crear la imagen final
    for line in range(0, height_APT_image):
        minute_marker = line % 120 == 0 # esta línea contendrá un marcador de minutos en los espacios

        # Telemetría
        telemetry_block = (line // 8) % 16

        if telemetry_block < 8:
            block_color = 32 * (telemetry_block)
            telemetryA_pixels = np.ones(45, dtype=np.int16) * block_color
            telemetryB_pixels = np.ones(45, dtype=np.int16) * block_color

        elif telemetry_block == 8:
            telemetryA_pixels = np.zeros(45, dtype=np.int16)
            telemetryB_pixels = np.zeros(45, dtype=np.int16)

        else:
            telemetryA_pixels = np.ones(45, dtype=np.int16) * 128
            telemetryB_pixels = np.ones(45, dtype=np.int16) * 128

        # Concatenar para hacer una fila entera de la imagen
        row = np.concatenate((
            syncA_pixels,
            spaceB_pixels if minute_marker else spaceA_pixels,
            videoA_pixels[line],
            telemetryA_pixels,
            syncB_pixels,
            spaceA_pixels if minute_marker else spaceB_pixels,
            videoB_pixels[line],
            telemetryB_pixels
        ))

        # Cambia la fila vacía de la imagen por la fila recién concatenada
        image_pixels[line] = row

    print("Conversión de matriz numpy a imagen PIL...")
    # Vuelve a convertir la matriz de píxeles en una imagen PIL
    image_pixels = image_pixels.astype(np.uint8)
    imageTx = Img.fromarray(image_pixels)

    # Guarda la imagen generada
    imageTx.save(output_APT_img_path)
    print(f"\nImagen APT generada y guardada en:\n{output_APT_img_path}\n")
    end_time = time.perf_counter() # Detiene el cronómetro
    processing_time = end_time - start_time
    lines_generated = height_APT_image # La altura de la imagen APT es el número de líneas generadas
    
    print(f"Tiempo total de codificación APT: {processing_time:.4f} segundos")
    if processing_time > 0:
        lines_per_second = lines_generated / processing_time
        print(f"Rendimiento: {lines_per_second:.2f} líneas APT generadas por segundo\n")
    else:
        print("Rendimiento: Demasiado rápido para medir o cero líneas generadas.\n")


def modulate_APT_img_to_audio(APT_img_path:Img, APT_WAV_path:str, output_sample_rate:int = 11025) -> float:
    """
    Modula en AM la imagen APT y la guarda como audio WAV a un samplerate de 11025 Hz.
    """
    print("|-------- APT Modulator --------|")
    start_time = time.perf_counter() # Inicia el cronómetro

    # Abrir la imagen
    try:
        print(f"Abrir imagen APT desde: {APT_img_path}")
        APT_image = Img.open(APT_img_path)
    except Exception as e:
        print(f"No se pudo abrir la imagen. Error: {e}")
        return None  # Sal del método si no se puede abrir la imagen
    
    # Aplanar la matriz de píxeles de la imagen a una matriz 1D y normalizarla
    print("Convirtiendo la imagen a un arreglo 1D y normalizando valores a [0,1]")
    image_pixels = np.asarray(APT_image).flatten() / 255

    # Generar una onda portadora a 2400 Hz
    sample_rate = 2080 * 20
    duration = 0.5 * APT_image.height
    n_samples = int(duration * sample_rate)
    print(f"Configurando portadora: frecuencia=2400Hz, sample_rate={sample_rate}, duración={duration}s, muestras={n_samples}")

    time_arr = np.linspace(0, duration, n_samples)
    carrier = 1023 * np.sin(2 * np.pi * 2400 * time_arr)
    print("Portadora generada.")

    # Escala la señal para que coincida con el número de muestra de la portadora
    scale = n_samples // len(image_pixels)
    print(f"Repitiendo cada valor de pixel {scale} veces para igualar la longitud de la portadora")
    signal = np.repeat(image_pixels, scale)

    # Modula en amplitud la portadora con la señal de 256 niveles.
    print("Modulando en amplitud la portadora con la señal de la imagen.")
    modulated = carrier * signal

    # Remuestrea el audio a la velocidad deseada
    n_samples_resampled = int(output_sample_rate * duration)
    print(f"Remuestreando audio a {output_sample_rate} Hz, muestras finales: {n_samples_resampled}")
    modulated = sps.resample(modulated, n_samples_resampled)

    # Guardar el audio como archivo WAV
    print(f"Guardando el audio modulado en: {APT_WAV_path}")
    modulated_int16 = modulated.astype(np.int16)
    wav.write(APT_WAV_path, output_sample_rate, modulated_int16)
    print(f"\nGuardado audio en:\n{APT_WAV_path}\n")
    end_time = time.perf_counter() # Detiene el cronómetro
    processing_time = end_time - start_time
    lines_modulated = APT_image.height # La altura de la imagen APT es el número de líneas moduladas
    
    print(f"Tiempo total de generación de audio APT: {processing_time:.4f} segundos")
    if processing_time > 0:
        lines_per_second = lines_modulated / processing_time
        print(f"Rendimiento: {lines_per_second:.2f} líneas de imagen APT moduladas por segundo")
        print(f"Lo que equivale a {duration/processing_time:.2f} segundos de audio por segundo de procesamiento\n")
    else:
        print("Rendimiento: Demasiado rápido para medir o cero líneas moduladas.\n")

    return duration