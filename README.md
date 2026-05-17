# Music Video Compiler

Professional Music Compilation Video Creator — Buat Video Kompilasi Musik dalam Hitungan Menit!

Gabungkan ratusan lagu dengan video looping, lengkap dengan playlist otomatis, timestamps YouTube, overlay judul lagu, dan transisi profesional. Sempurna untuk upload atau live stream 24/7.

## Features

### Core Features
- **Audio + Video Auto Merge** — Gabungkan ratusan lagu dengan video looping otomatis
- **YouTube Timestamps** — Generate timestamps otomatis untuk deskripsi YouTube
- **Playlist PNG** — Generate playlist image dengan font, warna, dan layout kustom
- **Song Title Overlay** — Tampilkan judul lagu dinamis (9 posisi, custom font & warna)
- **Intro & Outro Video** — Video pembuka/penutup dengan 3 mode audio (Normal, Seamless, Mixed)
- **Slideshow Mode** — Gabungkan gambar dengan efek transisi

### 30+ Visual Effects
- **Weather**: Rain, Heavy Rain, Snow, Blizzard, Fog, Mist
- **Light**: Light Leak, Lens Flare, Bokeh, Soft Glow, Neon Glow, Starburst
- **Color**: Warm Tone, Cool Tone, Cinematic, Sepia, Monochrome, High Contrast, Pastel, Sunset
- **Retro**: VHS Retro, VHS Glitch, 8mm Film, Analog TV, Polaroid
- **Distortion**: Glitch, Chromatic Aberration, Scan Lines, Pixelate, Wave Distortion
- **Particle**: Fire Particles, Sparks, Dust, Fireflies
- **Overlay**: Film Grain, Vignette, Strong Vignette, Letterbox
- **Spectrum**: Audio Spectrum, Audio Waves, Audio Frequency

### Advanced Features
- **Random Effect (Anti-Template)** — Efek berbeda otomatis untuk setiap video
- **Crossfade Audio** — Transisi halus antar lagu (0.5-5 detik)
- **Dual Overlay (Efek + Spectrum)** — Dua kategori overlay terpisah
- **Multi-Overlay Support** — PNG transparan, GIF animated, video greenscreen/blackscreen
- **Batch & Mass Processing** — Proses banyak video sekaligus
- **Master+Copy Strategy** — Render hemat waktu
- **GPU Acceleration** — NVIDIA NVENC, AMD AMF, Intel QSV (hingga 5x lebih cepat)
- **Resolution & FPS Control** — 720p, 1080p, 4K, Vertical Shorts, FPS 24/25/30/50/60
- **Live Stream Ready (CBR)** — Mode CBR untuk live streaming 24/7
- **Audio Mixing** — Volume control, EQ presets, compressor, normalizer
- **Professional Transitions** — Fade, Dissolve, Slide, Wipe
- **Image to Video** — Konversi JPG, PNG, WEBP, JFIF ke video

## Requirements

- **Python 3.9+**
- **FFmpeg** (must be installed and in PATH)
- **PyQt5** (GUI framework)
- **Pillow** (for playlist PNG generation)

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
