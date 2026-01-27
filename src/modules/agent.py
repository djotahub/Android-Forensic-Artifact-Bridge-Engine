import os
import time
import subprocess
import json
import re
import xml.etree.ElementTree as ET
from src.utils import ForensicUtils

class UIAgent:
    """
    AGENTE DE ADQUISICIÓN LÓGICA INTELIGENTE (ISO 27037).
    - Detecta remitente por coordenadas (Izquierda vs Derecha).
    - Filtra ruido (horas, separadores de fecha).
    - Vincula capturas de pantalla con hashes.
    """
    def __init__(self, adb_manager, case_folders):
        self.adb = adb_manager
        self.evidence_dir = case_folders["evidence"]
        self.screenshot_dir = os.path.join(self.evidence_dir, "Screenshots")
        self.audit_log = os.path.join(case_folders["logs"], "audit.log")
        self.json_path = os.path.join(self.evidence_dir, "chat_data.json")
        
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
            
        self.captured_messages = [] 

    def take_screenshot(self, index):
        filename = f"SC_{str(index).zfill(4)}.png"
        local_path = os.path.join(self.screenshot_dir, filename)
        remote_path = "/data/local/tmp/screen.png"
        
        subprocess.run(["adb", "shell", "screencap", "-p", remote_path], check=True, capture_output=True)
        subprocess.run(["adb", "pull", remote_path, local_path], check=True, capture_output=True)
        
        img_hash = ForensicUtils.calculate_hash(local_path)
        ForensicUtils.log_audit(self.audit_log, "UI_AGENT", "SCREENSHOT", f"File: {filename} | Hash: {img_hash}")
        return filename, img_hash

    def get_ui_dump(self):
        temp_xml = "temp_view_dump.xml"
        remote_xml = "/data/local/tmp/view.xml"
        subprocess.run(["adb", "shell", "uiautomator", "dump", remote_xml], check=True, capture_output=True)
        subprocess.run(["adb", "pull", remote_xml, temp_xml], check=True, capture_output=True)
        return temp_xml

    def _is_time_string(self, text):
        """Detecta si el texto es solo una hora (ej: 14:30 o 2:05 pm)."""
        # Regex simple para horas
        if re.match(r'^\d{1,2}:\d{2}(\s?[ap]\.?m\.?)?$', text.lower().strip()):
            return True
        return False

    def _analyze_node(self, node):
        """
        Analiza coordenadas para determinar remitente.
        Retorna: (sender_type, text)
        """
        text = node.attrib.get('text', '')
        bounds = node.attrib.get('bounds', '') # Ej: [54,1050][800,1150]
        
        if not text or len(text) < 1: return None, None
        
        # Filtros de ruido comunes en WhatsApp
        ignored = ["WhatsApp", "Escribe un mensaje", "Cámara", "Micrófono", "Hoy", "Ayer"]
        if text in ignored: return None, None
        
        # Si es solo una hora, lo ignoramos (ya tenemos el timestamp del dispositivo)
        if self._is_time_string(text): return None, None

        sender = "DESCONOCIDO"
        
        # Lógica de Coordenadas
        # Formato bounds: [x1,y1][x2,y2]
        try:
            coords = re.findall(r'\d+', bounds)
            if len(coords) == 4:
                x1 = int(coords[0]) # Borde izquierdo
                
                # UMBRAL: En la mayoría de celulares, si empieza después de 200px, es mensaje propio
                # (Ajustable según resolución, pero 200 es un estándar seguro para 'Right Side')
                if x1 > 200:
                    sender = "YO (Enviado)"
                else:
                    sender = "ELLOS (Recibido)"
        except:
            pass

        return sender, text

    def run(self, pages=15):
        ForensicUtils.log("AGENT", "INFO", "Iniciando Extracción Inteligente...")
        
        print("\n" + "="*60)
        print(" PREPARACIÓN:")
        print(" 1. Desbloquea el teléfono.")
        print(" 2. Abre el chat en WhatsApp.")
        print("="*60)
        input("\n[*] Presiona ENTER para comenzar...")

        for p in range(pages):
            ntp_time = ForensicUtils.get_ntp_time()
            device_time = subprocess.check_output(["adb", "shell", "date", "+'%Y-%m-%dT%H:%M:%S'"]).decode().strip()
            
            img_name, img_hash = self.take_screenshot(p)
            xml_file = self.get_ui_dump()
            
            if not os.path.exists(xml_file): continue
                
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                new_entries = 0
                
                # Iterar nodos
                for node in root.iter():
                    sender, text = self._analyze_node(node)
                    
                    if text:
                        # Deduplicación (Evitar repetir mensajes al hacer scroll)
                        is_duplicate = False
                        if self.captured_messages:
                            # Miramos los últimos 15 para ver si ya lo guardamos
                            lookback = self.captured_messages[-15:]
                            for m in lookback:
                                if m["text"] == text and m["sender"] == sender:
                                    is_duplicate = True
                                    break
                        
                        if not is_duplicate:
                            msg_obj = {
                                "sender": sender,  # <--- AHORA DICE QUIEN FUE
                                "text": text,
                                "img_ref": img_name,
                                "img_hash": img_hash,
                                "device_time": device_time,
                                "ntp_time": ntp_time,
                                "page": p
                            }
                            self.captured_messages.append(msg_obj)
                            new_entries += 1
                
                ForensicUtils.log("AGENT", "SUCCESS", f"Página {p+1}: {new_entries} mensajes capturados.")
                
                # Scroll
                subprocess.run(["adb", "shell", "input", "swipe", "500", "500", "500", "1500", "400"])
                
                if os.path.exists(xml_file): os.remove(xml_file)
                time.sleep(1.5)
                
            except Exception as e:
                ForensicUtils.log("AGENT", "ERROR", f"Error parseando XML: {e}")

        # Guardar JSON
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.captured_messages, f, indent=4, ensure_ascii=False)
        
        ForensicUtils.log("AGENT", "SUCCESS", f"Finalizado. Total mensajes: {len(self.captured_messages)}")
        return True