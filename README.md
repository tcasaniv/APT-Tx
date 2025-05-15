# APT-Tx
Este programa convierte imágenes en una señal de audio en formato WAV, adecuada para ser transmitida mediante el método de transmisión de imagen de satélite NOAA APT.

## Configuración entorno python

- Instalar python.
- Crear entorno virtual:
```sh
python -m venv venv
```

Una vez creado, el entorno virtual debe activarse. En Windows, puedes hacerlo con:

```pwsh
venv\Scripts\activate
```

En sistemas Unix (macOS y Linux), usa:

```sh
source venv/bin/activate
```

Luego, se deben instalar las dependencias con:

```sh
pip install -r requirements.txt 
```

## APT Encoder con GUI

Se puede abrir la GUI con Python:

```sh
python src/APT_Encoder_GUI.py
```

- Se elige dos imágenes a color en formato PNG, JPG, etc.
- Se hace el preprocesamiento para tenerlas en escala de grises y con ancho de 909 px.
- A partir de las imágenes generamos una imagen APT.
- A partir de la imagen APT generamos audio APT en formato WAV

# Transmitir señal APT con SDR

Podemos transmitir el archivo WAV generado con GNU Radio y un SDR (hackRF, USRP, bladeRF).

Se realiza un flowgraph en GNU Radio que permita modular el archivo WAV en FM con 17 kHz de desviación, resultando una señal de 34 kHz de ancho de banda.
Se añade el bloque correspondiente al SDR que usará para transmitir la señal.

## Decodificar APT (sin transmitir)

Podemos decodificar el archivo WAV con un programa como satdump y así obtener de nuevo la imagen APT.