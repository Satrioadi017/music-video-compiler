"""Core FFmpeg engine for video/audio processing."""

import json
import os
import re
import shutil
import subprocess
import tempfile
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional


# ====================== FIX UNICODE WINDOWS ======================
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass
if sys.stderr:
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass
# ================================================================


class Resolution(Enum):
    HD_720 = ("1280x720", "720p")
    FHD_1080 = ("1920x1080", "1080p")
    UHD_4K = ("3840x2160", "4K")
    VERTICAL_720 = ("720x1280", "Vertical 720p (Shorts)")
    VERTICAL_1080 = ("1080x1920", "Vertical 1080p (Shorts)")

    def __init__(self, size: str, label: str):
        self.size = size
        self.label = label

    @property
    def width(self) -> int:
        return int(self.size.split("x")[0])

    @property
    def height(self) -> int:
        return int(self.size.split("x")[1])


class GPUAccel(Enum):
    NONE = "none"
    NVIDIA_NVENC = "nvenc"
    AMD_AMF = "amf"
    INTEL_QSV = "qsv"


class RateControl(Enum):
    VBR = "vbr"
    CBR = "cbr"


@dataclass
class EncodingSettings:
    resolution: Resolution = Resolution.FHD_1080
    fps: int = 30
    gpu_accel: GPUAccel = GPUAccel.NONE
    rate_control: RateControl = RateControl.VBR
    video_bitrate: str = "8M"
    audio_bitrate: str = "192k"
    audio_sample_rate: int = 44100
    keyframe_interval: int = 2
    crf: int = 18
    preset: str = "medium"
    pixel_format: str = "yuv420p"


def find_ffmpeg() -> str:
    """Find FFmpeg binary path."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    common_paths = [
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "C:\\ffmpeg\\bin\\ffmpeg.exe",
        os.path.expanduser("~/ffmpeg/bin/ffmpeg"),
        "C:\\Users\\user\\Downloads\\ffmpeg-8.1.1-full_build\\bin\\ffmpeg.exe",
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p
    raise FileNotFoundError("FFmpeg not found. Please install FFmpeg and add to PATH.")


def find_ffprobe() -> str:
    """Find FFprobe binary path."""
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        return ffprobe
    ffmpeg_path = find_ffmpeg()
    ffprobe_path = ffmpeg_path.replace("ffmpeg", "ffprobe")
    if os.path.isfile(ffprobe_path):
        return ffprobe_path
    raise FileNotFoundError("FFprobe not found.")


def get_media_duration(filepath: str) -> float:
    """Get duration of a media file in seconds."""
    ffprobe = find_ffprobe()
    cmd = [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", filepath]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    data = json.loads(result.stdout)
    if "format" in data and "duration" in data["format"]:
        return float(data["format"]["duration"])
    for stream in data.get("streams", []):
        if "duration" in stream:
            return float(stream["duration"])
    return 0.0


def safe_list(data):
    """Helper untuk menghindari 'NoneType' object is not iterable"""
    if data is None:
        return []
    if isinstance(data, str):
        return [data]
    return list(data)


def detect_gpu() -> GPUAccel:
    """Detect available GPU with safe fallback."""
    ffmpeg = find_ffmpeg()
    try:
        result = subprocess.run([ffmpeg, "-encoders"], 
                              capture_output=True, text=True, timeout=10)
        output = result.stdout.lower()
        
        if "h264_nvenc" in output or "nvenc" in output:
            print("🔍 NVIDIA NVENC terdeteksi, sedang diuji...")
            test_cmd = [ffmpeg, "-f", "lavfi", "-i", "color=c=black:s=1280x720:d=1",
                       "-c:v", "h264_nvenc", "-t", "1", "-f", "null", "-"]
            test_result = subprocess.run(test_cmd, capture_output=True, timeout=5)
            if test_result.returncode == 0:
                print("✅ NVIDIA GPU (NVENC) siap digunakan")
                return GPUAccel.NVIDIA_NVENC
            else:
                print("⚠️ NVIDIA gagal → pakai CPU")
        
        if "h264_amf" in output or "amf" in output:
            print("✅ AMD GPU (AMF) terdeteksi")
            return GPUAccel.AMD_AMF
            
        if "h264_qsv" in output or "qsv" in output:
            print("✅ Intel GPU (QSV) terdeteksi")
            return GPUAccel.INTEL_QSV

    except Exception as e:
        print(f"GPU detection warning: {e}")

    print("⚠️ Menggunakan CPU encoding (lebih stabil)")
    return GPUAccel.NONE


def build_encoding_args(settings: EncodingSettings) -> list[str]:
    """Build encoding arguments."""
    args = []
    if settings.gpu_accel == GPUAccel.NVIDIA_NVENC:
        args.extend(["-c:v", "h264_nvenc"])
    elif settings.gpu_accel == GPUAccel.AMD_AMF:
        args.extend(["-c:v", "h264_amf"])
        if settings.preset in ["ultrafast", "superfast", "veryfast"]:
            args.extend(["-quality", "speed"])
        elif settings.preset in ["slow", "slower"]:
            args.extend(["-quality", "quality"])
        else:
            args.extend(["-quality", "balanced"])
    elif settings.gpu_accel == GPUAccel.INTEL_QSV:
        args.extend(["-c:v", "h264_qsv"])
    else:
        args.extend(["-c:v", "libx264"])
        args.extend(["-preset", settings.preset])

    if settings.rate_control == RateControl.CBR:
        args.extend(["-b:v", settings.video_bitrate, "-maxrate", settings.video_bitrate, "-bufsize", "16M"])
    else:
        args.extend(["-crf", str(settings.crf)])

    args.extend([
        "-pix_fmt", settings.pixel_format,
        "-r", str(settings.fps),
        "-g", str(settings.fps * settings.keyframe_interval),
        "-fflags", "+genpts+discardcorrupt",
        "-avoid_negative_ts", "make_zero",
    ])
    return args


def add_title_overlay(
    input_video: str,
    output_video: str,
    title_text: str,
    settings: EncodingSettings,
    position: str = "center",
    font_size: int = 60,
    duration: float = None
) -> None:
    """Add text title overlay with better Windows compatibility."""
    ffmpeg = find_ffmpeg()
    
    escaped_text = title_text.replace("'", "\\'").replace(":", "\\:").replace(",", "\\,")
    
    if position == "top":
        y_pos = "50"
    elif position == "bottom":
        y_pos = "h-th-50"
    else:
        y_pos = "(h-th)/2"
    
    drawtext = (
        f"drawtext=fontfile='C:/Windows/Fonts/arial.ttf':"
        f"text='{escaped_text}':"
        f"fontcolor=white:fontsize={font_size}:"
        f"bordercolor=black:borderw=4:"
        f"x=(w-tw)/2:y={y_pos}:"
        f"enable='between(t,0,{duration if duration else 5})'"
    )

    cmd = [
        ffmpeg, "-y", "-i", input_video,
        "-vf", drawtext,
        "-c:a", "copy",
    ]
    cmd.extend(build_encoding_args(settings))
    cmd.append(output_video)

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    
    if result.returncode != 0:
        print("⚠️ Title overlay gagal, mencoba versi sederhana...")
        simple_cmd = [
            ffmpeg, "-y", "-i", input_video,
            "-vf", f"drawtext=text='{escaped_text}':fontcolor=white:fontsize=50:x=(w-tw)/2:y=50",
            "-c:a", "copy",
        ]
        simple_cmd.extend(build_encoding_args(settings))
        simple_cmd.append(output_video)
        result = subprocess.run(simple_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if result.returncode != 0:
            raise RuntimeError(f"Title overlay failed:\n{result.stderr[-800:]}")


def add_intro_outro(
    main_video_path: str,
    intro_path: Optional[str],
    outro_path: Optional[str],
    output_path: str,
    settings: EncodingSettings
) -> str:
    """Add intro and/or outro video."""
    ffmpeg = find_ffmpeg()
    temp_files = []
    current_input = main_video_path

    if intro_path and os.path.exists(intro_path):
        temp_intro = tempfile.mktemp(suffix="_with_intro.mp4")
        temp_files.append(temp_intro)
        cmd = [ffmpeg, "-y", "-i", intro_path, "-i", current_input,
               "-filter_complex", "concat=n=2:v=1:a=1", "-c:v", "libx264", "-c:a", "aac", temp_intro]
        subprocess.run(cmd, check=True)
        current_input = temp_intro

    if outro_path and os.path.exists(outro_path):
        temp_outro = tempfile.mktemp(suffix="_with_outro.mp4")
        temp_files.append(temp_outro)
        cmd = [ffmpeg, "-y", "-i", current_input, "-i", outro_path,
               "-filter_complex", "concat=n=2:v=1:a=1", "-c:v", "libx264", "-c:a", "aac", temp_outro]
        subprocess.run(cmd, check=True)
        current_input = temp_outro

    shutil.copy2(current_input, output_path)

    for f in temp_files:
        if os.path.exists(f):
            try:
                os.unlink(f)
            except:
                pass
    return output_path


def create_slideshow(
    image_files: List[str],
    duration_per_image: float,
    output_path: str,
    settings: EncodingSettings,
    transition: str = "fade"
) -> None:
    """Create slideshow video from images."""
    image_files = safe_list(image_files)
    if not image_files:
        raise ValueError("No images provided for slideshow")

    ffmpeg = find_ffmpeg()
    w, h = settings.resolution.width, settings.resolution.height

    list_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding='utf-8')
    for img in image_files:
        safe_path = img.replace("\\", "/").replace("'", "'\\''")
        list_file.write(f"file '{safe_path}'\n")
        list_file.write(f"duration {duration_per_image}\n")
    list_file.write(f"file '{image_files[-1]}'\n")
    list_file.close()

    vf = f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos," \
         f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,format=yuv420p"

    cmd = [
        ffmpeg, "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file.name,
        "-vf", vf,
    ]
    cmd.extend(build_encoding_args(settings))
    cmd.extend(["-an", output_path])

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    try:
        os.unlink(list_file.name)
    except:
        pass

    if result.returncode != 0:
        raise RuntimeError(f"Slideshow creation failed:\n{result.stderr[-1000:]}")


def loop_video_to_duration(
    video_path: str,
    duration: float,
    output_path: str,
    settings: EncodingSettings,
    progress_callback=None,
) -> None:
    """Loop a video to match a target duration."""
    ffmpeg = find_ffmpeg()
    w, h = settings.resolution.width, settings.resolution.height

    cmd = [
        ffmpeg, "-y",
        "-stream_loop", "-1",
        "-i", video_path,
        "-t", str(duration),
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,"
               f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
               f"fps={settings.fps},format=yuv420p",
    ]
    cmd.extend(build_encoding_args(settings))
    cmd.extend(["-an", output_path])

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    stdout, _ = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg loop error:\n{stdout[-1500:]}")


def merge_video_audio(
    video_path: str,
    audio_path: str,
    output_path: str,
    settings: EncodingSettings,
    progress_callback=None,
) -> None:
    """Merge video and audio into final output."""
    ffmpeg = find_ffmpeg()
    cmd = [
        ffmpeg, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", settings.audio_bitrate,
        "-ar", str(settings.audio_sample_rate),
        "-shortest",
        "-fflags", "+genpts+discardcorrupt",
        output_path
    ]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace',
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    stdout, _ = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg merge error:\n{stdout[-1500:]}")


def concat_audio_files(
    audio_files: list[str],
    output_path: str,
    crossfade_duration: float = 0.0,
    progress_callback=None,
) -> list[tuple[float, str]]:
    """Concatenate audio files with strong compatibility handling."""
    ffmpeg = find_ffmpeg()
    timestamps: list[tuple[float, str]] = []

    audio_files = safe_list(audio_files)

    if not audio_files:
        raise ValueError("No audio files provided")

    normalized_files = []
    for i, af in enumerate(audio_files):
        norm_path = tempfile.mktemp(suffix="_norm.m4a")
        normalized_files.append(norm_path)

        norm_cmd = [
            ffmpeg, "-y", "-i", af,
            "-ar", "44100", "-ac", "2",
            "-c:a", "aac", "-b:a", "192k",
            "-fflags", "+genpts+discardcorrupt",
            norm_path
        ]
        result = subprocess.run(norm_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if result.returncode != 0:
            print(f"Warning: Normalize failed for {Path(af).name}, using original.")
            normalized_files[-1] = af
        else:
            print(f"Normalized: {Path(af).name}")

        if progress_callback:
            progress_callback(int((i + 1) / len(audio_files) * 40))

    audio_files = [f for f in normalized_files if os.path.exists(f)]

    list_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding='utf-8')
    current_time = 0.0

    for i, af in enumerate(audio_files):
        safe_path = af.replace("\\", "/").replace("'", "'\\''")
        list_file.write(f"file '{safe_path}'\n")
        name = Path(af).stem
        timestamps.append((current_time, name))
        duration = get_media_duration(af)
        current_time += duration

        if progress_callback:
            progress_callback(40 + int((i + 1) / len(audio_files) * 60))

    list_file.close()

    cmd = [
        ffmpeg, "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file.name,
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-fflags", "+genpts+discardcorrupt",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    
    if result.returncode != 0:
        raise RuntimeError(f"Concat error:\n{result.stderr[-1500:]}")

    try:
        os.unlink(list_file.name)
    except:
        pass
    for nf in normalized_files:
        if os.path.exists(nf) and nf not in audio_files:
            try:
                os.unlink(nf)
            except:
                pass

    return timestamps
