# Pre-procesar imágenes

En caso de no tener la imagen en formato BMP se puede usar esta herramienta para convertir la imagen a BMP de 24 bits.

- Se elige una imagen a color en formato PNG, JPG, etc.
- Se coloca la ruta dentro del archivo `convert_img.py`.
- Se ejecuta el código python para convertir a una imagen BMP de 24 bits.
- Asigna el tamaño adecuado teniendo un ancho de 909 px.
- La imagen queda guardada en la carpeta BMP.

## Ejemplo de uso

Modificar ruta de la imagen en la línea:

```py
imagen_path = "./img/spiral.jpg"
```

Correr el archivo con python:

```sh
python tools/convert_img.py
```

En la misma carpeta de la imagen original aparecerá la imagen ahora en formato BMP.