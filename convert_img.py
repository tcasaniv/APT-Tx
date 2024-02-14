import os
from PIL import Image as Img

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

    # Reescalar
    img_reescalada = reescalar_img(imagen,909)
    img_reescalada = img_reescalada.convert("RGB")

    # Crea la ruta para guardar la imagen
    ruta_directorio_salida = os.path.join(os.path.dirname(directorio_archivo), 'BMP')
    print(f"ruta_directorio_salida: {ruta_directorio_salida}")
    
    img_salida_reescalada = f'{nombre_sin_extension}_reescalada.bmp'

    ruta_salida_img_reescalada = os.path.join(ruta_directorio_salida, img_salida_reescalada)
    create_directory_if_not_exists(ruta_salida_img_reescalada)
    
    # Guardar la imagen preprocesada
    img_reescalada.save(ruta_salida_img_reescalada)
    print(f"Imagen preprocesada para formato APT guardada en:\n{ruta_salida_img_reescalada}\n")
    return ruta_salida_img_reescalada


# Imagen a reescalar:
imagen_path = "./img/spiral.jpg"

ruta_img_APT = preprocesar_img_to_APT(imagen_path)
