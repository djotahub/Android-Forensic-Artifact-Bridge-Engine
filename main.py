import os
import sys
import datetime
import json
from src.utils import ForensicUtils
from src.modules.adb_manager import ADBManager
from src.modules.crypto import WhatsAppDecryptor
from src.modules.downgrade import DowngradeAttack
from src.modules.lpe import LPEAttack
from src.modules.agent import UIAgent
from src.modules.media_extractor import MediaExtractor
from src.modules.analyst import DataAnalyst          # <--- Nuevo
from src.modules.metadata_analyst import MetadataAnalyst # <--- Nuevo
from src.modules.report_generator import ReportGenerator # <--- Nuevo

def create_case_structure(case_id):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_id = "".join([c for c in case_id if c.isalnum() or c in ('-', '_')]).strip()
    if not safe_id: safe_id = "CASO"
    
    base_dir = os.path.join("cases", f"{safe_id}_{timestamp}")
    
    folders = {
        "base": base_dir,
        "evidence": os.path.join(base_dir, "01_Evidence"),
        "logs": os.path.join(base_dir, "02_Logs"),
        "report": os.path.join(base_dir, "03_Report"),
        "media": os.path.join(base_dir, "04_Media")
    }
    
    for path in folders.values():
        os.makedirs(path, exist_ok=True)
        
    return folders

def main():
    ForensicUtils.banner()
    
    case_id = input("[?] Ingrese ID de Caso / Expediente: ")
    perito = input("[?] Nombre del Perito Responsable: ")
    
    folders = create_case_structure(case_id)
    audit_file = os.path.join(folders["logs"], "audit.log")
    
    ForensicUtils.log("SYSTEM", "INFO", f"Sesión iniciada. Evidencia en: {folders['base']}")
    ForensicUtils.log_audit(audit_file, "SYSTEM", "SESSION_START", f"Perito: {perito} | Caso: {case_id}")
    
    adb = ADBManager()
    if not adb.check_connection():
        ForensicUtils.log("MAIN", "CRITICAL", "Dispositivo no detectado o no autorizado.")
        return

    metadata = adb.get_device_metadata()
    with open(os.path.join(folders["logs"], "device_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    
    sdk = adb.get_android_version()
    rooted = adb.is_rooted()
    
    device_str = f"{metadata.get('fabricante', 'N/A')} {metadata.get('modelo', 'N/A')}"
    ForensicUtils.log("TRIAGE", "INFO", f"ID: {device_str} | SDK: {sdk} | Root: {rooted}")

    extraction_success = False
    method_used = None

    # --- CASCADA DE EXTRACCIÓN ---
    if rooted:
        ForensicUtils.log("STRATEGY", "SUCCESS", "Vector A (Root) disponible.")
        extraction_success = True 
        method_used = "ROOT_ACCESS"
    else:
        ForensicUtils.log("STRATEGY", "SKIP", "Vector A: No root.")

    if not extraction_success:
        if sdk < 31:
            ForensicUtils.log("STRATEGY", "INFO", "Vector B: Downgrade Attack...")
            attacker = DowngradeAttack(adb)
            if attacker.run(folders["evidence"]):
                extraction_success = True
                method_used = "DOWNGRADE_ATTACK"
        else:
            ForensicUtils.log("STRATEGY", "SKIP", "Vector B: Incompatible con Android 12+.")

    if not extraction_success:
        ForensicUtils.log("STRATEGY", "WARNING", "Vector C: LPE Exploits...")
        lpe = LPEAttack(adb)
        if lpe.run(folders["evidence"]):
            extraction_success = True
            method_used = "LPE_EXPLOIT"
        else:
            ForensicUtils.log("STRATEGY", "SKIP", "Vector C: Sin vulnerabilidades detectadas.")

    if not extraction_success:
        ForensicUtils.log("STRATEGY", "CRITICAL", "Activando Vector D (Agente UI)...")
        agent = UIAgent(adb, folders)
        if agent.run(pages=15):
            extraction_success = True
            method_used = "UI_SCRAPING"

    # --- FASE DE MULTIMEDIA ---
    ForensicUtils.log("SYSTEM", "INFO", "Extracción de Multimedia...")
    media = MediaExtractor(adb, folders)
    media.run()

    # --- POST-PROCESAMIENTO Y ANÁLISIS ---
    if extraction_success:
        # 1. Inteligencia de Datos (Keywords)
        analyst = DataAnalyst(folders)
        analyst.run()

        # 2. Análisis de Metadatos (EXIF)
        meta_analyst = MetadataAnalyst(folders)
        meta_analyst.run()

        # 3. Generación de Reporte Visual HTML
        ForensicUtils.log("SYSTEM", "INFO", "Generando Reporte Forense HTML...")
        reporter = ReportGenerator(folders, metadata)
        reporter.generate()

        # 4. Cierre y Manifiesto
        manifest_path = ForensicUtils.generate_manifest(folders["base"])
        manifest_hash = ForensicUtils.calculate_hash(manifest_path)
        
        # Reporte Ejecutivo TXT
        report_path = os.path.join(folders["report"], "Resumen_Ejecutivo.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"INFORME PERICIAL: CENTRUX WA-X v2.0 PRO\n")
            f.write(f"=======================================\n")
            f.write(f"ID CASO: {case_id}\n")
            f.write(f"FECHA: {datetime.datetime.now()}\n")
            f.write(f"METODO EXITOSO: {method_used}\n")
            f.write(f"INTEGRIDAD (SHA256): {manifest_hash}\n")
            f.write(f"=======================================\n")
        
        ForensicUtils.log("MAIN", "SUCCESS", f"Caso cerrado. Evidencia en: {folders['base']}")
    else:
        ForensicUtils.log("MAIN", "ERROR", "Adquisición fallida.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Operación abortada.")
        sys.exit(0)