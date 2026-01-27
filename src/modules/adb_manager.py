import subprocess
import shutil
import re
import time
from src.utils import ForensicUtils

class ADBManager:
    """
    Gestor ADB con Exponential Backoff y Extracción Exhaustiva de Metadatos.
    Recupera la identidad completa del dispositivo (Hardware, Red, Energía).
    """
    
    def __init__(self):
        self.adb_available = shutil.which("adb") is not None

    def _exec(self, command_list, retries=3):
        """Ejecutor interno con Exponential Backoff para estabilidad."""
        attempt = 0
        while attempt < retries:
            try:
                res = subprocess.run(command_list, capture_output=True, text=True, timeout=10)
                if res.returncode == 0:
                    return res.stdout.strip()
                else:
                    if attempt == retries - 1: return "ERROR"
            except Exception:
                pass
            
            wait_time = 2 ** attempt
            if attempt > 0:
                # Solo logueamos reintentos graves para no ensuciar
                pass 
            time.sleep(wait_time)
            attempt += 1
        
        return "ERROR_TIMEOUT"

    def check_connection(self):
        if not self.adb_available:
            ForensicUtils.log("ADB", "ERROR", "ADB no detectado.")
            return False
        res = self._exec(["adb", "devices"])
        return "\tdevice" in res

    def get_device_metadata(self):
        """Extrae radiografía completa del dispositivo (Versión Exhaustiva)."""
        ForensicUtils.log("ADB", "INFO", "Iniciando extracción profunda de metadatos...")
        metadata = {}
        
        # --- 1. Identificación de Hardware ---
        metadata["fabricante"] = self._exec(["adb", "shell", "getprop", "ro.product.manufacturer"])
        metadata["modelo"] = self._exec(["adb", "shell", "getprop", "ro.product.model"])
        metadata["nombre_codigo"] = self._exec(["adb", "shell", "getprop", "ro.product.name"])
        metadata["serial_number"] = self._exec(["adb", "shell", "getprop", "ro.serialno"])
        
        # --- 2. Software y Seguridad ---
        metadata["android_version"] = self._exec(["adb", "shell", "getprop", "ro.build.version.release"])
        metadata["sdk_level"] = self._exec(["adb", "shell", "getprop", "ro.build.version.sdk"])
        metadata["security_patch"] = self._exec(["adb", "shell", "getprop", "ro.build.version.security_patch"])
        metadata["kernel"] = self._exec(["adb", "shell", "uname", "-r"])
        
        # --- 3. Estado de Telefonía (Red) ---
        imei_call = self._exec(["adb", "shell", "service", "call", "iphonesubinfo", "1"])
        # Limpiamos un poco el resultado crudo del servicio
        metadata["imei_raw"] = imei_call if "Result" in imei_call else "RESTRICTED/UNAVAILABLE"
        metadata["sim_state"] = self._exec(["adb", "shell", "getprop", "gsm.sim.state"])
        metadata["operador"] = self._exec(["adb", "shell", "getprop", "gsm.operator.alpha"])

        # --- 4. Estado del Sistema (Energía y Tiempo) ---
        battery = self._exec(["adb", "shell", "dumpsys", "battery"])
        level = re.search(r"level: (\d+)", battery)
        metadata["bateria_nivel"] = level.group(1) if level else "N/A"
        
        metadata["tiempo_encendido"] = self._exec(["adb", "shell", "uptime"])
        
        # --- 5. Almacenamiento ---
        # Obtenemos solo la línea relevante de /data
        storage = self._exec(["adb", "shell", "df", "-h", "/data"])
        metadata["almacenamiento_info"] = storage.split("\n")[-1] if "\n" in storage else "N/A"

        # --- 6. Aplicación Objetivo ---
        wa_info = self._exec(["adb", "shell", "dumpsys", "package", "com.whatsapp"])
        ver_match = re.search(r"versionName=([\d.]+)", wa_info)
        metadata["whatsapp_version"] = ver_match.group(1) if ver_match else "NOT_INSTALLED"
        
        # --- 7. Accesibilidad ---
        acc = self._exec(["adb", "shell", "settings", "get", "secure", "enabled_accessibility_services"])
        metadata["accessibility_services"] = acc

        ForensicUtils.log("ADB", "SUCCESS", "Radiografía de hardware completada.")
        return metadata

    def get_android_version(self):
        try:
            val = self._exec(["adb", "shell", "getprop", "ro.build.version.sdk"])
            return int(val) if val.isdigit() else 0
        except:
            return 0

    def is_rooted(self):
        res = subprocess.run(["adb", "shell", "su", "-c", "id"], capture_output=True, text=True)
        return "uid=0(root)" in res.stdout