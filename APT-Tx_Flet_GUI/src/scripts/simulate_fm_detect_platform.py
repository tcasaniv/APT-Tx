import platform
from pathlib import Path

APP_FILES_DIR_NAME = "APT-Tx_Files"

def get_app_files_dir():
    """Obtiene la ruta a la carpeta de archivos de la aplicación y la crea si no existe."""
    if platform.system() == "Windows":
        base_path = Path(os.environ['USERPROFILE']) / 'Documents'
    else:
        base_path = Path.home()
    
    app_dir = base_path / APP_FILES_DIR_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return str(app_dir)

output_filename = f"apt_generated_audio.wav"
generated_file_path = str(Path(get_app_files_dir()) / output_filename)
wav_path = generated_file_path

print(wav_path)