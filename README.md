# APT-Tx
Este programa convierte imágenes en una señal de audio en formato WAV, adecuada para ser transmitida mediante el método de transmisión de imagen de satélite NOAA APT.

## Pre-procesar imágenes

- Se elige una imagen a color en formato PNG, JPG, etc.
- Se coloca la ruta dentro del archivo `convert_img.py`.
- Se ejecuta el código python para convertir a una imagen BMP de 24 bits.
- La imagen queda guardada en la carpeta BMP.

## APT Encoder + Modulador FM + Modulador I/Q (bin)

- A partir de la imagen en BMP generamos audio APT en formato WAV
- Este WAV luego se modula en FM y se convierte a señal I/Q.
- Se guarda la señal I/Q en formato .bin

Todo ese proceso se logra con el siguiente comando para transmitir una sola imagen BMP.
```PS
PS APT-Tx> 
PS APT-Tx> & '.\APT_Tx.exe' '.\BMP\imgA.bmp' output_APT.wav output_APT.bin
```

O con el siguiente comando para transmitir dos imágenes BMP distintas.
```PS
PS APT-Tx> 
PS APT-Tx> & '.\APT_Tx_AB.exe' '.\BMP\imgA.bmp' '.\BMP\imgB.bmp'  output_APT.wav output_APT.bin
```

# Transmitir muestras I/Q con HackRF

Podemos transmitir el archivo I/Q generado con extensión .bin con un hackRF.

Para ello usamos el siguiente comando:

```PS
PS APT-Tx> 
PS APT-Tx> hackrf_transfer -t ".\output_APT.bin" -f 137500000 -s 2822400 -a 1  -x 40 -b 1750000
```

Con ello estamos transmitiendo el archivo de muestras I/Q  a una frecuencia central de 137.5 MHz con una frecuencia de muestreo de 2.822400 MHz (44100 * 64) con el amplificador de potencia activado y con una ganancia de 40. Además se le está aplicando un filtro de ancho de banda de 1.75 MHz.
