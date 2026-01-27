import hashlib
import datetime
import os
import json
import socket
import struct
from colorama import init, Fore, Style

# Inicializar colorama para logs en consola
init(autoreset=True)

class ForensicUtils:
    """
    SISTEMA DE PRESERVACIÓN DIGITAL (ISO 27037).
    Maneja integridad criptográfica, validación temporal y auditoría.
    """
    
    @staticmethod
    def banner():
        print(Fore.CYAN + Style.BRIGHT + """
    ╔══════════════════════════════════════════════════════╗
    ║       CENTRUX WA-X: DIGITAL PRESERVATION SYSTEM      ║
    ║        ISO 27037 - ACQUISITION & PRESERVATION        ║
    ╚══════════════════════════════════════════════════════╝
        """)

    @staticmethod
    def get_ntp_time():
        """Obtiene la hora de un servidor NTP para evitar manipulación (Anti-Tampering)."""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            data = b'\x1b' + 47 * b'\0'
            client.settimeout(2)
            # Consulta a servidores de red externos
            client.sendto(data, ("pool.ntp.org", 123))
            data, address = client.recvfrom(1024)
            if data:
                t = struct.unpack('!12I', data)[10]
                t -= 2208988800 # Ajuste de era Unix
                return datetime.datetime.fromtimestamp(t).isoformat()
        except:
            return "NTP_UNAVAILABLE"

    @staticmethod
    def log_audit(audit_file, component, action, details=""):
        """Genera un registro de auditoría con precisión de milisegundos."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = f"[{timestamp}] [{component}] ACTION: {action} | DETAILS: {details}\n"
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(entry)

    @staticmethod
    def calculate_hash(file_path):
        """Calcula el SHA-256 de un archivo para garantizar su inalterabilidad."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def generate_manifest(case_path):
        """Crea el manifiesto final con los hashes de todos los archivos del caso."""
        manifest = {}
        for root, _, files in os.walk(case_path):
            for file in files:
                if file == "manifest.json": continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, case_path)
                manifest[rel_path] = ForensicUtils.calculate_hash(full_path)
        
        # El manifiesto se guarda en la carpeta de Logs
        manifest_path = os.path.join(case_path, "02_Logs/manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=4)
        return manifest_path

    @staticmethod
    def log(component, status, message):
        """Muestra mensajes formateados en la consola del perito."""
        colors = {"SUCCESS": Fore.GREEN, "ERROR": Fore.RED, "WARNING": Fore.YELLOW, "INFO": Fore.BLUE}
        color = colors.get(status, Fore.WHITE)
        print(f"{color}[{component}] {status}: {message}")