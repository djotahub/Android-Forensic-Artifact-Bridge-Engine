import json
import os
from src.utils import ForensicUtils

class DataAnalyst:
    """
    Motor de Inteligencia de Datos.
    Realiza búsquedas de palabras clave (Keyword Spotting) sobre la evidencia extraída.
    """
    def __init__(self, case_folders):
        self.evidence_dir = case_folders["evidence"]
        self.report_dir = case_folders["report"]
        self.json_path = os.path.join(self.evidence_dir, "chat_data.json")
        
        # Lista de palabras sospechosas por defecto (se puede cargar desde archivo externo)
        self.keywords = [
            "drogas", "arma", "dinero", "pago", "matar", "ubicación", 
            "location", "transferencia", "cbu", "alias", "banco", "meet"
        ]

    def set_custom_keywords(self, keyword_list):
        if keyword_list:
            self.keywords = [k.lower().strip() for k in keyword_list.split(",")]

    def run(self):
        ForensicUtils.log("ANALYST", "INFO", "Iniciando análisis de inteligencia de datos...")
        
        if not os.path.exists(self.json_path):
            ForensicUtils.log("ANALYST", "WARNING", "No hay datos de chat para analizar.")
            return False

        hits = []
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                messages = json.load(f)

            for msg in messages:
                text = msg.get("text", "").lower()
                for kw in self.keywords:
                    if kw in text:
                        hit = {
                            "keyword": kw,
                            "original_text": msg.get("text"),
                            "sender": msg.get("sender"),
                            "time": msg.get("device_time"),
                            "img_ref": msg.get("img_ref")
                        }
                        hits.append(hit)
                        # No rompemos el loop para encontrar múltiples keywords en un mismo mensaje

            # Generar Reporte de Hallazgos
            if hits:
                output_file = os.path.join(self.report_dir, "Hallazgos_Inteligencia.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(hits, f, indent=4, ensure_ascii=False)
                
                ForensicUtils.log("ANALYST", "SUCCESS", f"Se encontraron {len(hits)} coincidencias sospechosas.")
                return hits
            else:
                ForensicUtils.log("ANALYST", "INFO", "Análisis completado sin hallazgos de palabras clave.")
                return []

        except Exception as e:
            ForensicUtils.log("ANALYST", "ERROR", f"Fallo en el análisis: {e}")
            return []