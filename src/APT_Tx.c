#include <time.h> // Esta biblioteca es para usar clock() y medir tiempo
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define  MEM_SIZE 44100                                     // Tamaño de la memoria de voz
#define  MEM_SIZE_iq  44100

// |-------- Frame de telemetría --------|
#define  WDG_1 31                                           // WEDGE #1
#define  WDG_2 63                                           // WEDGE #2
#define  WDG_3 95                                           // WEDGE #3
#define  WDG_4 127                                          // WEDGE #4
#define  WDG_5 159                                          // WEDGE #5
#define  WDG_6 191                                          // WEDGE #6
#define  WDG_7 223                                          // WEDGE #7
#define  WDG_8 255                                          // WEDGE #8
#define  ZERO_MOD_WDG 0                                     // zero Modulation
#define  THM_TMP_1 55                                       // Thermister Temp #1
#define  THM_TMP_2 55                                       // Thermister Temp #2
#define  THM_TMP_3 55                                       // Thermister Temp #3
#define  THM_TMP_4 55                                       // Thermister Temp #4
#define  PTC_TMP 125                                        // Patch Temp
#define  BAC_SCN 1                                          // Back Scan
#define  CH_ID_WDG 30                                       // Channel I.D. Wedge

int main(int argc, char **argv){
    clock_t start_time, end_time;
    double cpu_time_used;
	start_time = clock(); // Guarda el tiempo de inicio

	// |-------- Formato APT --------|
	unsigned char sync_a[39] = {0,0,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,1,1,0,0,0,0,0,0,0,0,0};
	unsigned char image_a[909];
	unsigned char telemetry_a[45];

	unsigned char sync_b[39] = {0,0,0,0,1,1,1,0,0,1,1,1,0,0,1,1,1,0,0,1,1,1,0,0,1,1,1,0,0,1,1,1,0,0,1,1,1,0,0};
	unsigned char image_b[909];
	unsigned char telemetry_b[45];
	
	unsigned char telemetry[16] = {WDG_1,WDG_2,WDG_3,WDG_4,WDG_5,WDG_6,WDG_7,WDG_8,ZERO_MOD_WDG,THM_TMP_1,THM_TMP_2,THM_TMP_3,THM_TMP_4,PTC_TMP,BAC_SCN,CH_ID_WDG};
	double line_pic[2080];

	int bmp_wid;
	int bmp_hgt;
	int bmp_bitcount;

	// Variables para archivo bmp de entrada, archivo wav de salida y archivo bin(I/Q) de salida
	FILE *imageA, *output_file_WAV, *output_file_IQ_bin ;
	unsigned char  tmp1;                                    // 1Byte
	unsigned short tmp2;                                    // 2Byte
	unsigned long  tmp4;                                    // 4Byte
	unsigned char  tmp5;                                    // 4Byte
	unsigned short channel;                                 // Número de muestras de las formas de onda de salida
	unsigned short BytePerSample;                           // Byte number per 1 sample
	unsigned long  file_size;                               // output file size
	unsigned long  Fs_out;                                  // frecuencia de muestreo del archivo wav de salida
	unsigned long  BytePerSec;                              // Byte number per 1 second
	unsigned long  data_len;                                // Número de muestras de las formas de onda de salida
	unsigned long  fmt_chnk    =16;
	unsigned short BitPerSample=8;
	unsigned short fmt_ID      =1;                          // fmt ID.

	if(argc != 4){
		fprintf( stderr, "Usage: %s imgA.bmp output.wav output.bin \n",argv[0] );
		exit(-1);
	}

	printf("\n|-------- Imagen BMP a audio APT WAV --------|\n");
	if((imageA = fopen(argv[1], "rb")) == NULL){
		fprintf( stderr, "No se puede abrir %s\n", argv[1] );
		exit(-2);
	}
	if((output_file_WAV = fopen(argv[2], "wb")) == NULL){
		fprintf( stderr, "No se puede abrir %s\n", argv[2] );
		exit(-2);
	}

	// Leer la cabecera de la imagen A bmp de entrada
	fseek(imageA, 18L, SEEK_SET);
	fread(&tmp4, sizeof(unsigned long), 1, imageA);
	bmp_wid = tmp4;
	fread(&tmp4, sizeof(unsigned long), 1, imageA);
	bmp_hgt = tmp4;
	fseek(imageA, 28L, SEEK_SET);
	fread(&tmp2, sizeof(unsigned long), 1, imageA);
	bmp_bitcount = tmp2;
	
	if(bmp_wid != 909){
		fprintf( stderr, "La anchura de la imagen A bmp de entrada debe ser de 909 píxeles\n");
		exit(-2);
	}
	if(bmp_hgt > 2400){
		fprintf( stderr, "La altura de la imagen A bmp de entrada debe ser inferior a 2400 píxeles\n");
		exit(-2);
	}
	if(bmp_bitcount != 24){
		fprintf( stderr, "El recuento de bits de la imagen A bmp de entrada debe ser de 24 bits de color\n");
		exit(-2);
	}
	
	//Variables para el tratamiento de señales
	int           t             = 0;                                  // Variable de tiempo
	int           n             = 0;                                  //
	int           k             = 0;                                  //
	int           m             = 0;
	int           i             = 0;
	int           i_B           = 0;
	long int      t_out         = 0;                                  // Variables para la medición de la hora final
	int           add_len       = 0;                                  // Número de muestras para extender la señal de salida.
	unsigned char input, output;                                      // Leer y escribir variables
	double        s[MEM_SIZE+1] = {0};                                // Variables para almacenar datos de entrada
	int           Fs            = 44100;                              // frecuencia de muestreo del archivo wav de salida
	int           ch            = 1;                                  // Número de canales de entrada
	int           len           = 0.5*Fs*bmp_hgt;				      // Duración del audio al ser codificado en APT
	double        f             = 2400.0;
	unsigned long portadora_AM;
	unsigned long linea_actual_normalizada;

	//Preparación de los archivos wave de salida
	Fs_out        = Fs;                                               // Ajustar la frecuencia de muestreo de salida
	channel       = ch;                                               // Número de canales de salida
	data_len      = channel*(len+add_len)*BitPerSample/8;             // Longitud de los datos de salida = número de Bytes totales (2 Bytes para 1 muestra)
	file_size     = 36+data_len;                                      // Tamaño total del archivo
	BytePerSec    = Fs_out*channel*BitPerSample/8;                    // Bytes por segundo
	BytePerSample = channel*BitPerSample/8;                           // Bytes por muestra.

	//Escritura de información de cabecera de salida
	fprintf(output_file_WAV, "RIFF");                                              // "RIFF"
	fwrite(&file_size,    sizeof(unsigned long ), 1, output_file_WAV);             // tamaño del archivo
	fprintf(output_file_WAV, "WAVEfmt ");                                          // "WAVEfmt"
	fwrite(&fmt_chnk,     sizeof(unsigned long ), 1, output_file_WAV);             // fmt_chnk=16 (número de bits)
	fwrite(&fmt_ID,       sizeof(unsigned short), 1, output_file_WAV);             // fmt ID=1 (PCM)
	fwrite(&channel,      sizeof(unsigned short), 1, output_file_WAV);             // Número de canales de salida
	fwrite(&Fs_out,       sizeof(unsigned long ), 1, output_file_WAV);             // Frecuencia de muestreo de la salida
	fwrite(&BytePerSec,   sizeof(unsigned long ), 1, output_file_WAV);             // Bytes por segundo
	fwrite(&BytePerSample,sizeof(unsigned short ),1, output_file_WAV);             // Bytes por muestra.
	fwrite(&BitPerSample, sizeof(unsigned short ),1, output_file_WAV);             // Bits por muestra (8 bits)
	fprintf(output_file_WAV, "data");                                              // "data"
	fwrite(&data_len,     sizeof(unsigned long ), 1, output_file_WAV);             // length of output wav data

	
	// Salta a la posición 54 para leer los canales RGB de la imagen pixel a pixel
	fseek(imageA, 54L, SEEK_SET);

	// Bucle para crear línea por línea la imagen APT
	while(t_out<len){

		// Crea una línea APT
		if (n==0) {
			for (k=0;k<909;k++){
				i = 0;

				// CANAL R (rojo)
				fread(&tmp1, sizeof(unsigned char), 1, imageA);
				i = i + tmp1;
				image_a[k] = i;

				// CANAL G (verde)
				fread(&tmp1, sizeof(unsigned char), 1, imageA);
				i = i + tmp1;
				// image_b[k] = i / 2;

				// CANAL B (azul)
				fread(&tmp1, sizeof(unsigned char), 1, imageA);
				i = i + tmp1;
				image_b[k] = i / 3;
			}
			fread(&tmp1, sizeof(unsigned char), 1, imageA);
			for (k=0;k<45;k++){
				telemetry_a[k] = telemetry[(t_out/(8*22050))%16];
				telemetry_b[k] = telemetry[(t_out/(8*22050))%16];
			}
			for (k=0;k<39;k++){
				line_pic[k] = sync_a[k]*255;
				line_pic[k+1040] = sync_b[k]*255;
			}
			for (k=39;k<86;k++){
				if ((t_out/22050)%120 == 14 || (t_out/22050)%120 == 15 ){
					line_pic[k] = 0;
					line_pic[k+1040] = 0;
				} else if ((t_out/22050)%120 == 16 || (t_out/22050)%120 == 17 ){
					line_pic[k] = 255;
					line_pic[k+1040] = 255;
				} else {
					line_pic[k] = 0;
					line_pic[k+1040] = 255;
				}
			}
			for (k=86;k<995;k++){
				line_pic[k] = image_a[k-86];
				line_pic[k+1040] = image_b[k-86];
			}
			for (k=995;k<1040;k++){
				line_pic[k] = telemetry_a[k-995];
				line_pic[k+1040] = telemetry_b[k-995];
			}
		}

		// Tratamiento de señales
		k = 10;                                                                 // ajustar los píxeles por 1 línea
		if(n%2==1 || n%10==2 || n%1040==4) {                                    // 2080*10   +  1040   +   208    +     2 = 22050
			k = 11;                                                             //           =2080/2  =2080/10 =2080/1040
		}

		for (m=0;m<k;m++) {
			// Modular en AM
			portadora_AM = sin(2.0*M_PI*f*t_out/Fs_out);
			linea_actual_normalizada = line_pic[n]/255;
			s[t] = 0.5 + 0.5*( portadora_AM * linea_actual_normalizada );      // Modulación de amplitud
			output = s[t]*255;  // Escala a 0 a 255
			fwrite(&output, sizeof(unsigned char), 1, output_file_WAV);         // Guardar cada muestra modulada en AM en el WAV
			t=(t+1)%MEM_SIZE;                                                   // Actualización del tiempo t
			t_out++;                                                            // Medición del tiempo de fin de bucle
		}
		n=(n+1)%2080;
	}
	fclose(imageA);
	fclose(output_file_WAV);

	printf("\n%s fue generado correctamente.\n",argv[2]);


	// Ahora se debe modular el audio del WAV en FM y luego en I/Q
	// para finalmente guardarlo como archivo binario
	
	printf("\n|-------- Propiedades APT WAV --------|\n");
	
	// Leemos el archivo WAV
	if((output_file_WAV = fopen(argv[2], "rb")) == NULL){
		fprintf( stderr, "No se puede abrir %s\n", argv[2] );
		exit(-2);
	}

	// Creamos un archivo binario vacío para guardar muestras I/Q
	if((output_file_IQ_bin = fopen(argv[3], "wb")) == NULL){
		fprintf( stderr, "No se puede abrir %s\n", argv[3] );
		exit(-2);
	}
	
	// Salta a la posición 40 para leer propiedades del WAV
	fseek(output_file_WAV, 40L, SEEK_SET);
	fread(&tmp4, sizeof(unsigned long), 1, output_file_WAV);
	
	printf("Tamaño del archivo WAV: %lu Bytes\n",tmp4);
	tmp4=tmp4/44100;
	printf("Duración del audio WAV: %lu sec\n",tmp4);


	printf("\n|-------- APT WAV a I/Q bin --------|\n");

	double    Fs_iq   = 44100*64.0;				// 44100*50
	double    theta   = 0.0;       				// Fase de modulación
	double    mr      = 1.0;       			// 0.25 115k 0.75 120k 0.83 130k 0.95 160k   // Modulación FM de la señal
	double    tmp[2];
	unsigned  tmp_un;
	unsigned char xI;
	unsigned char xQ;
	
	printf("Generando archivo binario I/Q\n");
	// Salta a la posición 44 para leer las muestras de audio del WAV
	fseek(output_file_WAV, 44L, SEEK_SET);
	tmp[0] = 0.0; 
	unsigned long frecuencia_instantanea;
	unsigned long frecuencia_instantanea_normalizada;
	double muestra_anterior = 0.0;
	double muestra_actual;
	double muestra_actual_normalizada;

	double portadora_FM = (2.0*M_PI*50.0e3/Fs_iq);
	unsigned long  numero_muestras = 22050*2*tmp4;

	for (i=0;i<numero_muestras;i++){
		fread(&muestra_actual,sizeof(unsigned char), 1, output_file_WAV);
		muestra_actual_normalizada = (muestra_actual-127.5)/128;
		
		// Solo modula en FM y en I/Q por cada muestra de audio a siguiendo la codificación 16-bit PCM.
		// Cada muestra de audio será modulada en 16*4 muestras I/Q
		for (m=0;m<16;m++){
			for (k=0;k<4;k++){
				// Modular en FM y hallar la fase
				frecuencia_instantanea = muestra_anterior*(m+1.0) + muestra_actual_normalizada*(15.0-m);
				frecuencia_instantanea_normalizada = frecuencia_instantanea /16.0;
				// Modular en FM y hallar la fase
				theta = theta + portadora_FM * frecuencia_instantanea_normalizada;

				//Asegurarse que la fase no se deesborde
				if( theta > M_PI ){
					theta = theta - (double)(2.0*M_PI);
				}
				if( theta <-M_PI ){
					theta = theta + (double)(2.0*M_PI);
				}

				// Modular en I/Q según la fase
				xI = (unsigned char)((sin(mr*theta)) * 127.0);
				xQ = (unsigned char)((cos(mr*theta)) * 127.0);

				// Guardar muestra I/Q en el archivo binario
				fwrite(&xI, sizeof(unsigned char), 1, output_file_IQ_bin);
				fwrite(&xQ, sizeof(unsigned char), 1, output_file_IQ_bin);
				t=(t+1)%MEM_SIZE_iq; 
			}
		}
		muestra_anterior = muestra_actual_normalizada;
	}


	printf("\n%s fue generado correctamente.\n",argv[3]);

	// Cerramos los archivos WAV y binario
	fclose(output_file_WAV);
	fclose(output_file_IQ_bin);

    end_time = clock(); // Guarda el tiempo de finalización
    cpu_time_used = ((double) (end_time - start_time)) / CLOCKS_PER_SEC; // Calcula el tiempo de CPU utilizado
	printf("\n|-------- Fin --------|\n");
	printf("\nEl tiempo de ejecución IMG a APT WAV a I/Q bin fue: %f segundos\n\n", cpu_time_used);

	return 0;
}