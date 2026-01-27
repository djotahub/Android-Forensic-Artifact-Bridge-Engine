import os
from Crypto.Cipher import AES
from src.utils import ForensicUtils

class WhatsAppDecryptor:
    """
    Motor de desencriptado para bases de datos WhatsApp (Crypt14, Crypt15, Crypt16).
    Implementa AES-256-GCM según especificaciones del PRD.
    """

    def __init__(self):
        # Offsets definidos en la documentación técnica para Crypt14+
        self.KEY_OFFSET = 126       # Inicio de la llave AES en el archivo 'key'
        self.KEY_SIZE = 32          # Longitud de la llave (256 bits)
        self.IV_OFFSET = 67         # Inicio del Vector de Inicialización en el db
        self.IV_SIZE = 12           # Longitud del IV (GCM standard)
        self.TAG_SIZE = 16          # Longitud del Tag de autenticación
        self.HEADER_SIZE = 191      # Tamaño del header a ignorar en el db

    def validate_paths(self, key_path: str, db_path: str) -> bool:
        if not os.path.exists(key_path):
            ForensicUtils.log("CRYPTO", "ERROR", f"Key file no encontrado: {key_path}")
            return False
        if not os.path.exists(db_path):
            ForensicUtils.log("CRYPTO", "ERROR", f"DB file no encontrado: {db_path}")
            return False
        return True

    def decrypt(self, key_path: str, db_path: str, output_path: str) -> bool:
        """
        Ejecuta la desencriptación AES-GCM.
        """
        if not self.validate_paths(key_path, db_path):
            return False

        try:
            ForensicUtils.log("CRYPTO", "INFO", f"Iniciando desencriptado de {os.path.basename(db_path)}...")

            # 1. Procesar archivo KEY
            with open(key_path, "rb") as kf:
                key_data = kf.read()
                # Extraer la sub-llave AES real (t1) desde el offset 126
                aes_key = key_data[self.KEY_OFFSET : self.KEY_OFFSET + self.KEY_SIZE]

            # 2. Procesar archivo DATABASE ENCRIPTADA
            with open(db_path, "rb") as db:
                db_data = db.read()

            # 3. Extraer componentes del stream binario
            iv = db_data[self.IV_OFFSET : self.IV_OFFSET + self.IV_SIZE]
            tag = db_data[-self.TAG_SIZE:]
            ciphertext = db_data[self.HEADER_SIZE : -self.TAG_SIZE]

            # 4. Inicializar Cipher
            cipher = AES.new(aes_key, AES.MODE_GCM, nonce=iv)
            
            # 5. Desencriptar y Verificar Integridad
            decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)

            # 6. Guardar Resultado
            with open(output_path, "wb") as out:
                out.write(decrypted_data)
            
            # Calcular hash del resultado
            out_hash = ForensicUtils.calculate_hash(output_path)
            ForensicUtils.log("CRYPTO", "SUCCESS", f"Base desencriptada en: {output_path} (SHA256: {out_hash[:8]}...)")
            return True

        except ValueError:
            ForensicUtils.log("CRYPTO", "ERROR", "Fallo de Integridad: La llave no corresponde o el archivo está corrupto (Tag Mismatch).")
            return False
        except Exception as e:
            ForensicUtils.log("CRYPTO", "ERROR", f"Error de sistema: {str(e)}")
            return False