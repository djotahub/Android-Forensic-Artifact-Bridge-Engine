import os
import json
import datetime
from src.utils import ForensicUtils

class ReportGenerator:
    """
    Generador de Informes Forenses Profesionales (HTML Estático).
    Diseñado para presentación judicial con cadena de custodia visible.
    """
    def __init__(self, case_folders, metadata):
        self.case_folders = case_folders
        self.metadata = metadata
        self.report_path = os.path.join(case_folders["report"], "Informe_Forense_Final.html")

    def _generate_html(self, chat_data, findings_data, media_data):
        css = """
        @page { size: A4; margin: 2cm; }
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; line-height: 1.5; font-size: 12px; }
        .container { max-width: 100%; margin: 0 auto; }
        
        /* Header */
        .header { border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 24px; text-transform: uppercase; }
        .header .sub { font-size: 10px; color: #666; }
        
        /* Metadata Table */
        table.meta { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        table.meta td { border: 1px solid #ddd; padding: 8px; width: 50%; }
        table.meta th { background-color: #f8f9fa; text-align: left; padding: 8px; border: 1px solid #ddd; }
        
        /* Sections */
        h2 { background-color: #2c3e50; color: white; padding: 5px 10px; font-size: 16px; margin-top: 30px; }
        
        /* Evidence: Chats */
        .chat-table { width: 100%; border-collapse: collapse; }
        .chat-row { border-bottom: 1px solid #ccc; page-break-inside: avoid; }
        .chat-row td { padding: 10px; vertical-align: top; }
        .col-info { width: 25%; font-size: 10px; color: #555; background: #fdfdfd; border-right: 1px solid #eee; }
        .col-content { width: 45%; }
        .col-evidence { width: 30%; text-align: center; background: #fafafa; border-left: 1px solid #eee; }
        
        .sender-me { color: #27ae60; font-weight: bold; }
        .sender-them { color: #2980b9; font-weight: bold; }
        
        .hash-tag { font-family: 'Courier New', monospace; font-size: 8px; display: block; margin-top: 5px; color: #7f8c8d; word-break: break-all; }
        .img-preview { max-width: 100%; max-height: 150px; border: 1px solid #999; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
        
        /* Evidence: Multimedia Table */
        .media-table { width: 100%; font-size: 10px; border-collapse: collapse; }
        .media-table th { background: #eee; text-align: left; padding: 5px; border-bottom: 2px solid #ddd; }
        .media-table td { padding: 5px; border-bottom: 1px solid #eee; }
        .geo-link { color: white; background: #e74c3c; padding: 2px 5px; text-decoration: none; border-radius: 3px; }
        
        /* Alerts */
        .alert-box { border: 1px solid #e74c3c; background: #fdedec; padding: 10px; margin-bottom: 5px; border-left: 5px solid #e74c3c; }
        """
        
        # --- HEADER ---
        html = f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Informe Pericial</title><style>{css}</style></head><body>
        <div class="container">
            <div class="header">
                <h1>Informe de Adquisición Digital Forense</h1>
                <div class="sub">Generado por Centrux WA-X v2.0 | ISO 27037 Compliant</div>
            </div>
            
            <table class="meta">
                <tr><th>Dispositivo</th><td>{self.metadata.get('fabricante')} {self.metadata.get('modelo')}</td></tr>
                <tr><th>Serial (S/N)</th><td>{self.metadata.get('serial_number')}</td></tr>
                <tr><th>Sistema Operativo</th><td>Android {self.metadata.get('android_version')} (SDK {self.metadata.get('sdk_level')})</td></tr>
                <tr><th>Versión WhatsApp</th><td>{self.metadata.get('whatsapp_version')}</td></tr>
                <tr><th>Fecha Adquisición</th><td>{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</td></tr>
            </table>
        """

        # --- SECCIÓN 1: INTELIGENCIA ---
        if findings_data:
            html += "<h2>1. HALLAZGOS DE INTELIGENCIA (KEYWORDS)</h2>"
            for hit in findings_data:
                html += f"""
                <div class="alert-box">
                    <strong>PALABRA CLAVE: {hit['keyword'].upper()}</strong><br>
                    Contexto: "{hit['original_text']}"<br>
                    <small>Remitente: {hit['sender']} | Hora: {hit['time']}</small>
                </div>"""
        
        # --- SECCIÓN 2: EVIDENCIA DOCUMENTAL (CHATS) ---
        html += f"<h2>2. REGISTRO DE MENSAJERÍA ({len(chat_data)} eventos)</h2>"
        html += '<table class="chat-table">'
        
        for msg in chat_data:
            img_path = f"../01_Evidence/Screenshots/{msg['img_ref']}"
            sender_class = "sender-me" if "YO" in msg['sender'] else "sender-them"
            
            html += f"""
            <tr class="chat-row">
                <td class="col-info">
                    <strong>Dispositivo:</strong> {msg['device_time'].replace('T', ' ')}<br>
                    <strong>Servidor NTP:</strong> {msg['ntp_time'].replace('T', ' ')}<br>
                    <strong>ID Captura:</strong> {msg['img_ref']}
                </td>
                <td class="col-content">
                    <span class="{sender_class}">{msg['sender']}</span><br>
                    {msg['text']}
                </td>
                <td class="col-evidence">
                    <a href="{img_path}" target="_blank"><img src="{img_path}" class="img-preview"></a>
                    <span class="hash-tag">SHA256: {msg['img_hash']}</span>
                </td>
            </tr>
            """
        html += "</table>"

        # --- SECCIÓN 3: EVIDENCIA MULTIMEDIA Y METADATOS ---
        if media_data:
            html += f"<h2>3. ANÁLISIS DE MULTIMEDIA ({len(media_data)} archivos relevantes)</h2>"
            html += """<table class="media-table">
            <thead><tr><th>Archivo</th><th>Cámara / Origen</th><th>Fecha Original</th><th>Geolocalización</th><th>Integridad (SHA-256)</th></tr></thead>
            <tbody>"""
            
            for m in media_data:
                gps_block = "N/A"
                if m['gps']:
                    gps_block = f"<a href='https://maps.google.com/?q={m['gps']}' target='_blank' class='geo-link'>VER MAPA</a><br>{m['gps']}"
                
                # Link relativo correcto desde la carpeta Report a Media (subir un nivel y entrar a media)
                # Ojo: media_extractor guarda en absolute path o relative? Asumimos estructura standard.
                # Como metadata_analyst guarda 'rel_path' relativo a report_dir, lo usamos directo.
                
                html += f"""
                <tr>
                    <td><b><a href="{m['rel_path']}" target="_blank">{m['filename']}</a></b></td>
                    <td>{m['camera']}</td>
                    <td>{m['date_original']}</td>
                    <td>{gps_block}</td>
                    <td><span class="hash-tag">{m['hash']}</span></td>
                </tr>
                """
            html += "</tbody></table>"
        else:
            html += "<h2>3. ANÁLISIS DE MULTIMEDIA</h2><p>No se encontraron metadatos relevantes (EXIF/GPS) en los archivos extraídos.</p>"

        # --- FOOTER ---
        html += """
        <div style="margin-top: 50px; border-top: 2px solid #000; padding-top: 10px;">
            <p><strong>FIN DEL INFORME</strong></p>
            <p style="font-size: 10px;">Este documento fue generado automáticamente por una herramienta de preservación forense. 
            La integridad de este reporte está vinculada al Manifiesto de Cierre del caso.</p>
        </div>
        </div></body></html>
        """
        return html

    def generate(self):
        # Rutas de entrada
        json_chat = os.path.join(self.case_folders["evidence"], "chat_data.json")
        json_intel = os.path.join(self.case_folders["report"], "Hallazgos_Inteligencia.json")
        json_meta = os.path.join(self.case_folders["report"], "Analisis_Metadatos.json")
        
        if not os.path.exists(json_chat): 
            ForensicUtils.log("REPORT", "ERROR", "No se encontró chat_data.json")
            return False

        try:
            # Cargar datos
            with open(json_chat, "r", encoding="utf-8") as f: chat_data = json.load(f)
            
            findings_data = []
            if os.path.exists(json_intel):
                with open(json_intel, "r", encoding="utf-8") as f: findings_data = json.load(f)
            
            media_data = []
            if os.path.exists(json_meta):
                with open(json_meta, "r", encoding="utf-8") as f: media_data = json.load(f)
            
            # Generar HTML
            html = self._generate_html(chat_data, findings_data, media_data)
            
            with open(self.report_path, "w", encoding="utf-8") as f: 
                f.write(html)
            
            ForensicUtils.log("REPORT", "SUCCESS", f"Informe Forense generado en: {self.report_path}")
            return True
        except Exception as e:
            ForensicUtils.log("REPORT", "ERROR", f"Error generando reporte: {e}")
            return False