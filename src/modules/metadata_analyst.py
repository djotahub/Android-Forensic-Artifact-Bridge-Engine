import os
import json
import re
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from src.utils import ForensicUtils

class MetadataAnalyst:
    """
    Analizador de Metadatos EXIF con Inteligencia de Origen.
    Distingue entre archivos 'lavados' por WhatsApp y archivos originales (Documentos)
    que pueden contener evidencia geolocalizada crítica.
    """
    def __init__(self, case_folders):
        self.media_dir = case_folders.get("media")
        self.report_dir = case_folders.get("report")

    def _get_exif_data(self, image):
        """Extrae data EXIF cruda de forma segura."""
        exif_data = {}
        try:
            info = image._getexif()
            if info:
                for tag, value in info.items():
                    decoded = TAGS.get(tag, tag)
                    if decoded == "GPSInfo":
                        gps_data = {}
                        for t in value:
                            sub_decoded = GPSTAGS.get(t, t)
                            gps_data[sub_decoded] = value[t]
                        exif_data[decoded] = gps_data
                    else:
                        if isinstance(value, bytes):
                            try:
                                value = value.decode()
                            except:
                                value = str(value)
                        exif_data[decoded] = value
        except:
            pass
        return exif_data

    def _get_lat_lon(self, exif_data):
        """Convierte coordenadas GPS a formato decimal legible."""
        lat = None
        lon = None
        if "GPSInfo" in exif_data:
            try:
                gps_info = exif_data["GPSInfo"]
                def convert_to_degrees(value):
                    d = float(value[0])
                    m = float(value[1])
                    s = float(value[2])
                    return d + (m / 60.0) + (s / 3600.0)

                gps_latitude = gps_info.get("GPSLatitude")
                gps_latitude_ref = gps_info.get("GPSLatitudeRef")
                gps_longitude = gps_info.get("GPSLongitude")
                gps_longitude_ref = gps_info.get("GPSLongitudeRef")

                if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
                    lat = convert_to_degrees(gps_latitude)
                    if gps_latitude_ref != "N": lat = 0 - lat
                    lon = convert_to_degrees(gps_longitude)
                    if gps_longitude_ref != "E": lon = 0 - lon
            except:
                pass
        return lat, lon

    def _classify_origin(self, filename):
        """
        Analiza el nombre del archivo para determinar si pasó por el proceso de compresión.
        """
        # Patrón típico de WhatsApp: IMG-YYYYMMDD-WAXXXX.jpg
        if re.search(r'-WA\d+', filename) or (filename.startswith("IMG-") and "WA" in filename):
            return "PROCESADO (Metadata Stripped)"
        
        # Patrones de cámara original o descarga
        if re.match(r'^\d{8}_\d{6}', filename) or filename.startswith("DSC") or "Screenshot" in filename:
            return "POSIBLE ORIGINAL (High Value)"
            
        return "INDETERMINADO"

    def run(self):
        ForensicUtils.log("META", "INFO", "Iniciando análisis forense de metadatos (EXIF)...")
        
        if not self.media_dir or not os.path.exists(self.media_dir):
            return

        findings = []
        scan_count = 0
        gps_count = 0

        # Filtramos archivos que no son imágenes útiles
        excluded_ext = ['.thumb', '.dat', '.opus', '.sticker'] 

        for root, _, files in os.walk(self.media_dir):
            for file in files:
                if any(file.endswith(ext) for ext in excluded_ext): continue
                
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    scan_count += 1
                    try:
                        filepath = os.path.join(root, file)
                        origin_status = self._classify_origin(file)
                        
                        # Integridad: Hash del archivo
                        file_hash = ForensicUtils.calculate_hash(filepath)
                        
                        # EXIF
                        img = Image.open(filepath)
                        exif = self._get_exif_data(img)
                        lat, lon = self._get_lat_lon(exif)
                        
                        gps_str = None
                        if lat:
                            gps_str = f"{lat}, {lon}"
                            gps_count += 1
                            origin_status = "CRÍTICO: GEO-EVIDENCIA POSITIVA"

                        # Guardamos si tiene datos o si parece original
                        has_meta = "Make" in exif or "DateTimeOriginal" in exif
                        
                        if lat or has_meta or "ORIGINAL" in origin_status:
                            entry = {
                                "filename": file,
                                "rel_path": os.path.relpath(filepath, self.report_dir),
                                "hash": file_hash,
                                "status": origin_status,
                                "camera": f"{exif.get('Make', '')} {exif.get('Model', '')}".strip(),
                                "date_original": str(exif.get("DateTimeOriginal", "N/A")),
                                "gps": gps_str
                            }
                            findings.append(entry)
                    except:
                        pass 

        # Guardar resultados JSON para el generador de reportes
        output_file = os.path.join(self.report_dir, "Analisis_Metadatos.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(findings, f, indent=4)
            
        if gps_count > 0:
            ForensicUtils.log("META", "SUCCESS", f"¡ALERTA! Se encontraron {gps_count} imágenes con coordenadas GPS.")
        else:
            ForensicUtils.log("META", "INFO", f"Escaneadas {scan_count} imágenes. Sin GPS (Normal en media procesada).")