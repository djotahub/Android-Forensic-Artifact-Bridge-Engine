import os
import subprocess
import threading
import time
import sys
from src.utils import ForensicUtils

class MediaExtractor:
    """
    Módulo de extracción de archivos multimedia (Imágenes, Videos, Audios).
    Optimizado para manejar las restricciones de ruta y permisos de Android 14.
    """
    def __init__(self, adb_manager, case_folders):
        self.adb = adb_manager
        self.media_output = case_folders.get("media")
        self.audit_log = os.path.join(case_folders["logs"], "audit.log")
        self.stop_spinner = False
        
        # Rutas prioritarias para WhatsApp moderno (Android 11-14)
        self.target_paths = [
            "/sdcard/Android/media/com.whatsapp/WhatsApp/Media",
            "/sdcard/WhatsApp/Media"
        ]

    def _spinner_animation(self, message):
        """Hilo secundario para animación visual."""
        spinner = ['|', '/', '-', '\\']
        idx = 0
        while not self.stop_spinner:
            sys.stdout.write(f"\r[*] {message} {spinner[idx % len(spinner)]} ")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(message) + 20) + "\r")
        sys.stdout.flush()

    def _find_active_path(self):
        """Busca la ruta de media activa con manejo de errores de comillas."""
        for path in self.target_paths:
            # Verificamos existencia con comillas para evitar fallos por espacios
            check_cmd = ["adb", "shell", f"ls -d '{path}'"]
            res = subprocess.run(check_cmd, capture_output=True, text=True)
            if res.returncode == 0 and "No such" not in res.stdout:
                return path.strip()
        return None

    def run(self):
        ForensicUtils.log("MEDIA", "INFO", "Iniciando fase de preservación multimedia...")
        remote_path = self._find_active_path()
        
        if not remote_path:
            ForensicUtils.log("MEDIA", "WARNING", "No se detectaron carpetas de multimedia legibles.")
            return False

        if not os.path.exists(self.media_output):
            os.makedirs(self.media_output, exist_ok=True)

        ForensicUtils.log_audit(self.audit_log, "MEDIA", "EXTRACTION_START", f"Source: {remote_path}")
        
        self.stop_spinner = False
        spinner_thread = threading.Thread(target=self._spinner_animation, args=("Extrayendo archivos multimedia...",))
        spinner_thread.start()

        try:
            # Usamos comillas simples en el comando ADB para la ruta remota
            # Capturamos stderr para diagnóstico
            pull_cmd = ["adb", "pull", remote_path, self.media_output]
            process = subprocess.run(pull_cmd, capture_output=True, text=True)
            
            self.stop_spinner = True
            spinner_thread.join()

            if process.returncode != 0:
                # Si falla el pull general, intentamos un método más granular
                ForensicUtils.log("MEDIA", "WARNING", "Pull masivo fallido. Intentando modo compatibilidad...")
                
                # Obtener lista de subcarpetas (WhatsApp Images, WhatsApp Video, etc)
                subfolders_res = subprocess.run(["adb", "shell", f"ls '{remote_path}'"], capture_output=True, text=True)
                subfolders = subfolders_res.stdout.splitlines()
                
                success_count = 0
                for folder in subfolders:
                    folder = folder.strip()
                    if not folder: continue
                    
                    remote_sub = f"{remote_path}/{folder}"
                    local_sub = os.path.join(self.media_output, folder)
                    
                    # Intentar pull individual
                    res = subprocess.run(["adb", "pull", remote_sub, local_sub], capture_output=True, text=True)
                    if res.returncode == 0:
                        success_count += 1
                
                if success_count == 0:
                    ForensicUtils.log("MEDIA", "ERROR", f"Error ADB: {process.stderr.strip()}")
                    return False

            # Conteo de verificación final
            file_count = 0
            for root, _, files in os.walk(self.media_output):
                file_count += len(files)
            
            if file_count > 0:
                ForensicUtils.log("MEDIA", "SUCCESS", f"Se han preservado {file_count} archivos multimedia.")
                ForensicUtils.log_audit(self.audit_log, "MEDIA", "EXTRACTION_COMPLETE", f"Total files: {file_count}")
                return True
            else:
                ForensicUtils.log("MEDIA", "WARNING", "La carpeta multimedia fue procesada pero no se obtuvieron archivos.")
                return False

        except Exception as e:
            self.stop_spinner = True
            if spinner_thread.is_alive():
                spinner_thread.join()
            ForensicUtils.log("MEDIA", "ERROR", f"Error crítico: {str(e)}")
            return False