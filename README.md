# APT-Tx
Este programa codifica imágenes en el formato de satélites NOAA APT (modulación AM con telemetría incluida), lo modula en FM y en formato I/Q para ser transmitida por un hackRF.

## Compilación Windows

Se debe compilar con el siguiente comando en Windows:
```PWSH
# Para usar una sola imagen
gcc "APT Encoder (C)/APT_Tx.c" -o "build/Win64/APT_Tx.exe"

# Para usar dos imágenes distintas
# gcc "APT Encoder (C)/APT_Tx_AB.c" -o "build/Win64/APT_Tx_AB.exe"
```

## Compilación Linux

Se debe compilar con el siguiente comando en Linux:
```sh
# Para usar una sola imagen
gcc "APT Encoder (C)/APT_Tx.c" -o "build/Linux64/APT_Tx" -lm

# Para usar dos imágenes distintas
# gcc "APT Encoder (C)/APT_Tx_AB.c" -o "build/Linux64/APT_Tx_AB" -lm
```

## APT Encoder + Modulador FM + Modulador I/Q (bin)

- A partir de una imagen en BMP (o dos distintas) generamos audio APT en formato WAV
- Este WAV luego se modula en FM y se convierte a señal I/Q.
- Se guarda la señal I/Q en formato .bin

## Modo de uso

Todo ese proceso se logra con el siguiente comando para usar una sola imagen BMP.

En Windows, con Powershell:

```PWSH
& '.\APT_Tx.exe' imgA.bmp  output_APT.wav output_APT.bin
```
En Linux, con la terminal:

```sh
build/Linux64/APT_Tx imgA.bmp  output_APT.wav output_APT.bin
```

O con el siguiente comando para usar dos imágenes BMP distintas.

En Windows, con Powershell:
```PWSH
& '.\APT_Tx_AB.exe' imgA.bmp imgB.bmp  output_APT.wav output_APT.bin
```
En Linux, con la terminal:

```sh
build/Linux64/APT_Tx imgA.bmp imgB.bmp  output_APT.wav output_APT.bin
```

## Transmitir muestras I/Q con HackRF

Podemos transmitir el archivo I/Q generado con extensión .bin con un hackRF.

Para ello usamos el siguiente comando tanto en Windows como en Linux:

```sh
hackrf_transfer -t "output_APT.bin" -f 137500000 -s 2822400 -a 1  -x 40 -b 1750000
```

Con ello estamos transmitiendo el archivo de muestras I/Q  a una frecuencia central de 137.5 MHz con una frecuencia de muestreo de 2.822400 MHz (44100 * 64) con el amplificador de potencia activado y con una ganancia de 40. Además se le está aplicando un filtro de ancho de banda de 1.75 MHz.


## Visualizar archivo I/Q (sin transmitir)

Podemos visualizar el archivo I/Q desde el programa SDR#.
- Para ello vamos en la opción de Source/Fuente y seleccionamos `Baseband File Player`.
- Seleccionamos el archivo .bin.
- Ingresamos el Sample Rate de 2822400 Hz.
- Con 16 Bits por muestra.
- Y solo un canal.
Con ello podremos ver la señal sin necesidad de transmitir con un transmisor SDR.