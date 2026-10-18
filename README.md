# 🎬 AVI Conversor

Aplicación de escritorio con interfaz gráfica moderna para convertir archivos de video `.avi` a `.mp4` con preservación de fechas originales, rotación individual por video, vista previa de orientación y máxima compatibilidad con el Reproductor Multimedia de Windows.

## ✨ Características

- 🎥 **Conversión de AVI a MP4:** Optimizado con FFmpeg embebido (no requiere instalaciones adicionales).
- 📅 **Preservación total de fechas:** Conserva la fecha de creación y modificación original del sistema de archivos, así como los metadatos internos del video.
- ⚡ **Procesamiento por lotes en paralelo:** Convierte múltiples videos simultáneamente exportando cada uno como archivo individual independiente.
- 👁️ **Vista previa de orientación:** Permite ver una miniatura rápida para detectar si el video está en orientación vertical u horizontal antes de convertir.
- 🔄 **Rotación individual por video:** Ajusta la orientación de cada archivo por separado (Sin rotación, 90° derecha, 180°, 270° izquierda).
- 📺 **100% Compatible con Windows Media Player:** Codificado en H.264 YUV 4:2:0 estándar con audio AAC estéreo a 44.1 kHz y `faststart`, garantizando que abre en cualquier reproductor sin errores de códec (`0x80004005`).
- 🎛️ **Opciones de calidad configurables:** Personaliza resolución, códec de video/audio, CRF y preset de velocidad (o usa los valores predeterminados recomendados).
- 📊 **Progreso en tiempo real:** Barra de progreso general fijada en la parte inferior y porcentaje individual por archivo.
- 📁 **Carpeta de destino configurable:** Elige fácilmente dónde guardar los videos convertidos.
- ⏹️ **Cancelación y cierre limpios:** Detención inmediata de procesos FFmpeg sin dejar procesos residuales bloqueando archivos.

## 📋 Requisitos

- Python 3.11+
- Windows 10/11

## 🚀 Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/EmmaNieves/.avi_conversor.git
cd .avi_conversor
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## 💻 Uso

Ejecuta el archivo principal:
```bash
python main.py
```

## ⚙️ Opciones predeterminadas recomendadas

| Parámetro | Valor predeterminado |
|-----------|----------------------|
| Códec de video | H.264 (`libx264`) - YUV 4:2:0 |
| Códec de audio | AAC (Estéreo, 44.1 kHz, 192 kbps) |
| Resolución | Original (o 1080p, 720p, 480p) |
| Calidad (CRF) | 23 (equilibrio óptimo calidad/peso) |
| Velocidad | Veryfast (rápido y balanceado) |
| Rotación | Sin rotación (configurable por video) |
| Carpeta de destino | `C:\Videos\Convertidos` |
