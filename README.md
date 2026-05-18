Music Video Compiler v1.0
============================

Aplikasi untuk mengkompilasi musik + video + overlay + efek secara otomatis.

✨ Fitur:
• Auto compile music video
• Audio mixing & normalization
• Overlay teks & gambar
• Batch processing
• Effects engine

📌 Dibuat oleh: Satrio Adi Wibowo

Cara Penggunaan:
1. Double klik MusicVideoCompiler.exe
2. Pilih musik dan video/template
3. Atur pengaturan yang diinginkan
4. Klik Compile

Catatan:
- Pastikan FFmpeg sudah terinstall di komputer (atau gunakan installer)
- Untuk hasil terbaik, gunakan video resolusi tinggi

GitHub: https://github.com/Satrioadi017/music-video-compiler

---

Music Video Compiler © 2026 Satrio Adi Wibowo


# Music Video Compiler


## Installation

### 1. Install FFmpeg

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

### 2. Install Music Video Compiler

```bash
# Clone the repository
git clone https://github.com/Satrioadi017/music-video-compiler.git
cd music-video-compiler

# Install dependencies
pip install -r requirements.txt

# Install the application
pip install -e .
```

## Usage

### Run the Application

```bash
# Method 1: Using entry point
music-video-compiler

# Method 2: Using Python module
python -m music_video_compiler

# Method 3: Using run script
python run.py
```

### Quick Start Guide

1. **Add Audio Files** — Drag & drop atau klik "Add Audio Files" untuk menambahkan lagu
2. **Select Background Video** — Pilih video yang akan di-loop sebagai background
3. **Configure Effects** — Pilih efek visual dari 30+ pilihan (Tab Effects)
4. **Set Overlays** — Atur overlay judul lagu dan spectrum (Tab Overlays)
5. **Generate Timestamps** — Klik generate untuk membuat timestamps YouTube (Tab Timestamps)
6. **Configure Encoding** — Atur resolusi, FPS, GPU, dan bitrate (Tab Encoding)
7. **Start Render** — Klik "START RENDER" untuk memulai proses

### Batch Processing

1. Buka tab **Batch**
2. Atur jumlah variasi yang diinginkan
3. Aktifkan "Random Audio Order" dan/atau "Random Effects"
4. Pilih output directory
5. Klik "Start Mass Batch"

### Live Streaming Setup

1. Buka tab **Encoding**
2. Set Rate Control ke **CBR**
3. Set Keyframe Interval ke **2 seconds**
4. Set Video Bitrate sesuai resolusi:
   - 720p: 5M
   - 1080p: 8M
   - 4K: 30M

## Project Structure

```
music-video-compiler/
├── music_video_compiler/
│   ├── __init__.py          # Package initialization
│   ├── __main__.py          # Entry point
│   ├── gui.py               # PyQt5 GUI application
│   ├── ffmpeg_engine.py     # Core FFmpeg processing engine
│   ├── effects_engine.py    # 30+ visual effects
│   ├── overlay_engine.py    # Song title & multi-overlay system
│   ├── timestamp_generator.py  # YouTube timestamps & playlist PNG
│   ├── audio_mixer.py       # Advanced audio mixing
│   └── batch_processor.py   # Batch & mass processing
├── setup.py                 # Package setup
├── requirements.txt         # Dependencies
├── run.py                   # Quick run script
└── README.md
```

## License

MIT License
