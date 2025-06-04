# APT-Tx
Este programa convierte imágenes en una señal de audio en formato WAV, adecuada para ser transmitida mediante el método de transmisión de imagen de satélite NOAA APT usando usando un equipo SDR (Radio Definida por Software).

- [APT-Tx](#apt-tx)
  - [Configuración entorno de desarrollo Python](#configuración-entorno-de-desarrollo-python)
  - [Iniciar APT-Tx con GUI (desarrollo)](#iniciar-apt-tx-con-gui-desarrollo)
    - [Transmitir señal APT con SDR](#transmitir-señal-apt-con-sdr)
  - [Decodificar APT (sin transmitir)](#decodificar-apt-sin-transmitir)
  - [Crear la aplicación](#crear-la-aplicación)
    - [Android](#android)
    - [iOS](#ios)
    - [macOS](#macos)
    - [Linux](#linux)
    - [Windows](#windows)
  - [Alternativa para ejecutar la app](#alternativa-para-ejecutar-la-app)
    - [uv](#uv)
    - [Poetry](#poetry)


## Configuración entorno de desarrollo Python

<details open>
<summary>De forma automática</summary>

Puedes configurar el entorno e iniciar la aplicación de manera sencilla haciendo doble click en el script `flet_run_dev` con la extensión según tu sistema operativo.

> `flet_run_dev.bat` para Windows.

> `flet_run_dev.sh` para Linux y MacOS.

</details>

<details>
<summary>De forma manual</summary>

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

</details>

## Iniciar APT-Tx con GUI (desarrollo)

Se puede iniciar la GUI con `Python` o con el comando `flet`:

```sh
# python src/main.py
flet run
```

- Se elige dos imágenes a color desde un enlace o archivo local.
- Se hace el preprocesamiento para tenerlas en escala de grises y con ancho de 909 px.
- A partir de las imágenes generamos una imagen APT.
- A partir de la imagen APT generamos audio APT en formato WAV.

### Transmitir señal APT con SDR

Podemos transmitir el archivo WAV generado con un script hecho en GNU Radio y un SDR (hackRF, USRP, bladeRF, LimeSDR, PlutoSDR).

El flowgraph en GNU Radio permite modular el archivo WAV en FM con 17 kHz de desviación, resultando una señal de 34 kHz de ancho de banda.
Luego usa el bloque correspondiente al SDR para transmitir la señal.

> Nota: Este flowgraph está incluido en el programa pero se debe instalar GNU Radio a parte.

## Decodificar APT (sin transmitir)

Podemos decodificar el archivo WAV con un programa como satdump o noaa-apt-decoder y así obtener de nuevo la imagen APT.

## Crear la aplicación

<details>
<summary>Click para ver</summary>

### Android

> Nota: De momento no están disponibles todas las dependencias para Android por lo que fallará el comando.

```
flet build apk -v
```

Para más detalles sobre la creación y firma de `.apk` o `.aab`, consulte la [Guía de Empaquetado de Android](https://flet.dev/docs/publish/android/).

### iOS

> Nota: De momento no están disponibles todas las dependencias para iOS por lo que fallará el comando.

```
flet build ipa -v
```

Para obtener más información sobre cómo crear y firmar `.ipa`, consulta la [Guía de empaquetado de iOS](https://flet.dev/docs/publish/ios/).

### macOS

```
flet build macos -v
```

Para obtener más información sobre la creación de paquetes de macOS, consulte la [Guía de empaquetado de macOS](https://flet.dev/docs/publish/macos/).

### Linux

```
flet build linux -v
```

Para más detalles sobre la creación de paquetes Linux, consulte la [Guía de Empaquetado Linux](https://flet.dev/docs/publish/linux/).

### Windows

```
flet build windows -v
```

Para más detalles sobre la creación de paquetes Windows, consulte la [Guía de Empaquetado Windows](https://flet.dev/docs/publish/windows/).

</details>

## Alternativa para ejecutar la app

De manera alternativa a `venv` y al comando `flet` uno puede usar `uv` o `Poetry` para instalar dependencias y ejecutar la app.


<details>
<summary>Click para ver</summary>

### uv

Ejecutar como una aplicación de escritorio:

```a
uv run flet run
```

Ejecutar como una aplicación web:

```
uv run flet run --web
```

### Poetry

Instalar dependencias de `pyproject.toml`:

```
poetry install
```

Ejecutar como una aplicación de escritorio:

```
poetry run flet run
```

Ejecutar como una aplicación web:

```
poetry run flet run --web
```

Para más detalles sobre el funcionamiento de la aplicación, consulte la [Guía de introducción](https://flet.dev/docs/getting-started/).

<details＞