from PIL import Image as Img

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
    # return ruta_salida_img