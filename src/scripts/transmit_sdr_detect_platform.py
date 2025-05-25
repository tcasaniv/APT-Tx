import platform
import os

APP_FILES_DIR_NAME = "APT-Tx_Files"

def get_app_files_dir():
    """Obtiene la ruta a la carpeta de archivos de la aplicación y la crea si no existe."""
    if platform.system() == "Windows":
        base_path = os.path.join(os.environ['USERPROFILE'], 'Documents')
    else:
        base_path = os.path.expanduser("~")
    
    app_dir = os.path.join(base_path, APP_FILES_DIR_NAME)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

output_filename = "apt_generated_audio.wav"
generated_file_path = os.path.join(get_app_files_dir(), output_filename)
wav_path = generated_file_path

print(wav_path)