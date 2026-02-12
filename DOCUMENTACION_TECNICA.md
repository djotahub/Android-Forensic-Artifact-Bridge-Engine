# DOCUMENTACIÓN TÉCNICA Y GUÍA OPERATIVA: AFAB-ENGINE

## 1. Resumen 

El **AFAB-Engine** es una solución avanzada para la adquisición y preservación de evidencia digital en dispositivos Android. Implementa protocolos de integridad basados en la norma **ISO/IEC 27037:2012**, asegurando que cada proceso de extracción mantenga la trazabilidad y la inalterabilidad de los datos desde el dispositivo origen hasta el informe final.

## 2. Manual Operativo de Campo

### 2.1 Preparación del Dispositivo Objetivo

Antes de iniciar cualquier vector de ataque, se deben asegurar los siguientes estados en el dispositivo:

1. **Modo Avión Activo:** Previene la alteración de la base de datos por mensajes entrantes y bloquea la sincronización de red de la hora (fundamental para la estabilidad del Vector B).
    
2. **Eliminación de Perímetros:** El bloqueo de pantalla debe configurarse en **"NINGUNO"**. La presencia de PINs, patrones o huellas bloquea el Keystore de Android, lo que suele derivar en errores de flujo de datos (549 bytes) en extracciones via ADB.
    
3. **Depuración USB:** Habilitar en las Opciones de Desarrollador y autorizar la huella RSA de la estación pericial de forma permanente.
    

### 2.2 Protocolo de "Time Travel" (Casos de Bloqueo de Fecha)

Para superar el bloqueo de "Fecha Incorrecta" en versiones Legacy de aplicaciones:

- Desactivar "Fecha y hora automática".
    
- Configurar manualmente el reloj al año **2014** (específicamente 01/01/2014).
    
- Si el error persiste, ajustar en el rango **2013-2015** hasta que la aplicación permita la carga del motor de datos.
    

## 3. Descripción de Vectores de Ataque (Orquestación en Cascada)

### Vector A: Acceso Root Directo

- **Mecánica:** Utiliza privilegios `UID 0` para copiar archivos protegidos directamente desde el sandbox del sistema (`/data/data/`).
    
- **Uso:** Dispositivos con privilegios de superusuario activos.
    

### Vector B: Downgrade Attack

- **Mecánica:** Sustitución temporal de la aplicación por una versión vulnerable (v2.11.431) manteniendo los datos de usuario mediante el flag `-k`.
    
- **Optimización:** Utiliza el Backup Manager (`bmgr`) para forzar transporte local y eludir restricciones de seguridad en el flujo de datos.
    

### Vector C: LPE (Local Privilege Escalation)

- **Mecánica:** Inyección de binarios en directorios temporales para explotar vulnerabilidades de Kernel.
    
- **Requisito:** Precisa de binarios compatibles con la arquitectura y chipset del objetivo (ej. Exynos, MediaTek) alojados en `bin/payloads/exploit_lpe`.
    

### Vector D: UI Agent (Adquisición Lógica Visual)

- **Mecánica:** Utiliza servicios de accesibilidad para realizar un scrapeo automatizado de la interfaz de usuario.
    
- **Integridad:** Cada mensaje se vincula a una captura de pantalla con su respectivo hash SHA-256.
    

## 4. Estructura de Salida y Cadena de Custodia

El sistema organiza la evidencia en cuatro directorios jerárquicos:

1. **`01_Evidence/`**: Archivos crudos (`msgstore.db`, `key`) y bases de datos procesadas.
    
2. **`02_Logs/`**: Manifiesto de integridad (`manifest.json`) y registros de auditoría de comandos.
    
3. **`03_Report/`**: Informe final en formato HTML para visualización profesional.
    
4. **`04_Media/`**: Galería de archivos multimedia recuperados y catalogados.
    

## 5. Protocolos de Integridad

- **Hashing SHA-256:** Firma digital automática de cada archivo en el momento de la extracción.
    
- **Validación NTP:** Sincronización con servidores de tiempo externos para garantizar marcas temporales precisas.
    
- **Audit Log:** Registro técnico de cada interacción realizada entre el host y el hardware objetivo.
    

**AFAB: Android Forensic Artifact Bridge Engine**

_Integridad y Rigor en la Preservación Digital._