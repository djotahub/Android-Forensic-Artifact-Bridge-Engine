# AFAB - Android Forensic Artifact Bridge Engine

### Sistema de Adquisición Lógica y Preservación Digital (ISO/IEC 27037:2012)

**Especificación Técnica y Guía Operativa de Campo**

## 1. Introducción Técnica

El **AFAB-Engine** (Android Forensic Artifact Bridge) es una plataforma modular de ingeniería forense diseñada para la extracción, preservación y análisis de artefactos digitales en dispositivos móviles Android. El sistema actúa como un puente (**Bridge**) de comunicación de bajo nivel entre el hardware objetivo y la estación pericial, utilizando un motor (**Engine**) de orquestación en cascada para superar perímetros de seguridad avanzados.

Este software está optimizado para la recuperación de datos en el ecosistema de **WhatsApp (com.whatsapp)** y **WhatsApp Business (com.whatsapp.w4b)**, integrando protocolos de integridad criptográfica que garantizan la admisibilidad de la evidencia en sede judicial.

## 2. Requisitos de Infraestructura y Sistema

### 2.1 Estación de Peritaje (Host)

- **Sistema Operativo:** Windows 10/11 (Pro/Enterprise) o distribuciones Linux (Kernel 5.15+).
    
- **Entorno de Ejecución:** Python 3.10.x o superior.
    
- **Java Runtime:** JRE 8 o superior (Indispensable para el procesamiento de backups `.ab`).
    
- **Controladores:** Drivers OEM certificados por el fabricante del dispositivo objetivo.
    

### 2.2 Dependencias de Software

El motor requiere la instalación de las librerías especificadas en `requirements.txt`:

- **pycryptodome:** Algoritmos AES-256-GCM para descifrado de bases de datos.
    
- **adb-shell:** Comunicación directa con el demonio de Android.
    
- **Pillow:** Análisis de metadatos EXIF e integridad de imágenes.
    
- **colorama:** Gestión de logs de auditoría visual.
    

## 3. Instalación y Configuración Paso a Paso

### Paso 1: Clonación del Repositorio

```
git clone https://github.com/djotahub/Android-Forensic-Artifact-Bridge-Engine.git
cd Android-Forensic-Artifact-Bridge-Engine
```

### Paso 2: Despliegue del Entorno Virtual (Aislamiento Forense)

Es imperativo aislar las dependencias para evitar contaminación de librerías:

```
python -m venv venv
# Activación en Windows:
.\venv\Scripts\activate
# Activación en Linux:
source venv/bin/activate
```

### Paso 3: Instalación de Librerías Core

```
pip install -r requirements.txt
```

### Paso 4: Carga de Payloads de Terceros (Fase Crítica)

El operador debe suministrar manualmente los binarios propietarios en la ruta `bin/payloads/`:

- **LegacyWhatsApp.apk:** Versión 2.11.431 (Versión vulnerable con `ALLOW_BACKUP` activo).
    
- **abe.jar:** Android Backup Extractor (Para la conversión de blobs `.ab` a contenedores `.tar`).
    
- **exploit_lpe:** Binario de explotación (ej. mtk-su) para el Vector C.
    

## 4. Manual Operativo de Usuario

### 4.1 Preparación del Dispositivo Objetivo

1. Inicie el dispositivo y acceda a **Ajustes > Acerca del teléfono**.
    
2. Pulse 7 veces sobre **Número de Compilación** para activar el modo programador.
    
3. En **Opciones de Desarrollador**, active:
    
    - Depuración por USB.
        
    - Instalar vía USB (si el vendor lo requiere).
        
    - Depuración USB (Ajustes de Seguridad) (En dispositivos Xiaomi/Poco).
        
4. Conecte el cable de datos y autorice la huella RSA en la pantalla del móvil.
    

### 4.2 Ejecución de la Extracción

Inicie el orquestador principal:

```
python main.py
```

El sistema solicitará dos parámetros obligatorios para la cadena de custodia:

- **ID de Expediente:** Nombre técnico de la carpeta de salida.
    
- **Nombre del Perito:** Responsable legal de la adquisición.
    

### 4.3 Interpretación de los Resultados

Al finalizar, el Bridge genera una estructura de cuatro directorios:

- **01_Evidence/:** Bases de datos desencriptadas y logs de chat en JSON.
    
- **02_Logs/:** Documentación técnica, metadatos de hardware y manifiesto de integridad.
    
- **03_Report/:** Informe Forense HTML interactivo. Ábralo en cualquier navegador para visualizar conversaciones con hashes visibles.
    
- **04_Media/:** Archivos multimedia extraídos y catalogados.
    

## 5. Arquitectura de los Vectores de Ataque

El Engine decide la ruta de extracción de forma jerárquica:

- **Vector A (Root):** Si el dispositivo posee UID 0, realiza un volcado directo del sandbox.
    
- **Vector B (Downgrade):** Realiza un swap de binarios preservando el directorio de datos. Es el método más efectivo para Android 7-11.
    
- **Vector C (LPE):** Intenta una escalada de privilegios locales inyectando exploits de kernel.
    
- **Vector D (UI Agent):** Método de última instancia para Android 12-14. Realiza una adquisición lógica mediante el agente de accesibilidad, capturando y hasheando el flujo visual de la pantalla.
    

## 6. Protocolos de Integridad (ISO 27037)

Para garantizar la inalterabilidad de la prueba, el software ejecuta:

- **Validación NTP:** Sincronización horaria con `pool.ntp.org` para detectar manipulaciones en el RTC del dispositivo.
    
- **Hashing SHA-256 Inmediato:** Cada archivo extraído recibe una firma digital única en el momento de su creación.
    
- **Audit Log:** Registro exhaustivo de cada comando enviado al hardware con su respectivo código de retorno.
    

## 7. Resolución de Conflictos Técnicos

- **INSTALL_FAILED_VERSION_DOWNGRADE:** El sistema tiene bloqueada la regresión de versión. El Engine saltará automáticamente al Vector D.
    
- **Dispositivo no detectado:** Verifique que el cable soporte transferencia de datos y que los drivers del fabricante estén correctamente instalados en el Host.
    
- **Backup vacío (0 bytes):** Asegúrese de que no haya una "Contraseña de respaldo de escritorio" configurada en las Opciones de Desarrollador.
    

**AFAB: Android Forensic Artifact Bridge Engine** _Engineering for Truth and Digital Integrity_
