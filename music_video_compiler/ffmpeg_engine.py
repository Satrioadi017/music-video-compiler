"""Core FFmpeg engine for video/audio processing."""

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


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
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p
    raise FileNotFoundError(
        "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH."
    )


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
    cmd = [
        ffprobe, "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", filepath
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    if "format" in data and "duration" in data["format"]:
        return float(data["format"]["duration"])
    for stream in data.get("streams", []):
        if "duration" in stream:
            return float(stream["duration"])
    return 0.0


def get_media_info(filepath: str) -> dict:
    """Get detailed info about a media file."""
    ffprobe = find_ffprobe()
    cmd = [
        ffprobe, "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", filepath
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)


def detect_gpu() -> GPUAccel:
    """Detect available GPU acceleration."""
    ffmpeg = find_ffmpeg()
    try:
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-encoders"],
            capture_output=True, text=True
        )
        encoders = result.stdout
        if "h264_nvenc" in encoders:
            test = subprocess.run(
                [ffmpeg, "-hide_banner", "-f", "lavfi", "-i",
                 "color=black:s=64x64:d=1", "-c:v", "h264_nvenc",
                 "-f", "null", "-"],
                capture_output=True, text=True
            )
            if test.returncode == 0:
                return GPUAccel.NVIDIA_NVENC
        if "h264_amf" in encoders:
            return GPUAccel.AMD_AMF
        if "h264_qsv" in encoders:
            return GPUAccel.INTEL_QSV
    except Exception:
        pass
    return GPUAccel.NONE


def build_encoding_args(settings: EncodingSettings) -> list[str]:
    """Build FFmpeg encoding arguments from settings."""
    args = []
    if settings.gpu_accel == GPUAccel.NVIDIA_NVENC:
        args.extend(["-c:v", "h264_nvenc"])
        if settings.rate_control == RateControl.CBR:
            args.extend(["-rc", "cbr", "-b:v", settings.video_bitrate])
        else:
            args.extend(["-rc", "vbr", "-cq", str(settings.crf),
                         "-b:v", settings.video_bitrate])
        args.extend(["-preset", "p4"])
    elif settings.gpu_accel == GPUAccel.AMD_AMF:
        args.extend(["-c:v", "h264_amf"])
        if settings.rate_control == RateControl.CBR:
            args.extend(["-rc", "cbr", "-b:v", settings.video_bitrate])
        else:
            args.extend(["-b:v", settings.video_bitrate])
    elif settings.gpu_accel == GPUAccel.INTEL_QSV:
        args.extend(["-c:v", "h264_qsv"])
        if settings.rate_control == RateControl.CBR:
            args.extend(["-b:v", settings.video_bitrate])
        else:
            args.extend(["-global_quality", str(settings.crf)])
    else:
        args.extend(["-c:v", "libx264"])
        if settings.rate_control == RateControl.CBR:
            args.extend([
                "-b:v", settings.video_bitrate,
                "-minrate", settings.video_bitrate,
                "-maxrate", settings.video_bitrate,
                "-bufsize", settings.video_bitrate,
            ])
        else:
            args.extend(["-crf", str(settings.crf)])
        args.extend(["-preset", settings.preset])

    args.extend([
        "-r", str(settings.fps),
        "-g", str(settings.fps * settings.keyframe_interval),
        "-pix_fmt", settings.pixel_format,
        "-c:a", "aac",
        "-b:a", settings.audio_bitrate,
        "-ar", str(settings.audio_sample_rate),
    ])
    return args


def concat_audio_files(
    audio_files: list[str],
    output_path: str,
    crossfade_duration: float = 0.0,
    progress_callback=None,
) -> list[tuple[float, str]]:
    """Concatenate audio files, optionally with crossfade.

    Returns list of (start_time, filename) tuples for timestamps.
    """
    ffmpeg = find_ffmpeg()
    timestamps: list[tuple[float, str]] = []

    if crossfade_duration <= 0:
        list_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        )
        current_time = 0.0
        for i, af in enumerate(audio_files):
            safe_path = af.replace("'", "'\\''")
            list_file.write(f"file '{safe_path}'\n")
            name = Path(af).stem
            timestamps.append((current_time, name))
            duration = get_media_duration(af)
            current_time += duration
            if progress_callback:
                progress_callback(int((i + 1) / len(audio_files) * 50))
        list_file.close()

        cmd = [
            ffmpeg, "-y", "-f", "concat", "-safe", "0",
            "-i", list_file.name, "-c:a", "aac", "-b:a", "192k",
            "-ar", "44100", output_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        os.unlink(list_file.name)
    else:
        current_time = 0.0
        temp_files = []
        current_output = audio_files[0]
        timestamps.append((0.0, Path(audio_files[0]).stem))
        dur = get_media_duration(audio_files[0])
        current_time = dur

        for i in range(1, len(audio_files)):
            name = Path(audio_files[i]).stem
            next_dur = get_media_duration(audio_files[i])
            current_time -= crossfade_duration
            timestamps.append((max(0, current_time), name))
            current_time += next_dur

            temp_out = tempfile.mktemp(suffix=".m4a")
            temp_files.append(temp_out)

            cmd = [
                ffmpeg, "-y",
                "-i", current_output, "-i", audio_files[i],
                "-filter_complex",
                f"[0:a][1:a]acrossfade=d={crossfade_duration}:c1=tri:c2=tri[out]",
                "-map", "[out]", "-c:a", "aac", "-b:a", "192k",
                temp_out
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            current_output = temp_out
            if progress_callback:
                progress_callback(int((i + 1) / len(audio_files) * 50))

        shutil.copy2(current_output, output_path)
        for tf in temp_files:
            if os.path.exists(tf):
                os.unlink(tf)

    return timestamps


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
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
               f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
               f"fps={settings.fps}",
    ]
    cmd.extend(build_encoding_args(settings))
    cmd.extend(["-an", output_path])
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _, stderr = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {stderr.decode()}")


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
        output_path
    ]
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _, stderr = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg merge error: {stderr.decode()}")


def image_to_video(
    image_path: str,
    duration: float,
    output_path: str,
    settings: EncodingSettings,
) -> None:
    """Convert an image to a video of specified duration."""
    ffmpeg = find_ffmpeg()
    w, h = settings.resolution.width, settings.resolution.height
    cmd = [
        ffmpeg, "-y",
        "-loop", "1",
        "-i", image_path,
        "-t", str(duration),
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
               f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
               f"fps={settings.fps}",
    ]
    cmd.extend(build_encoding_args(settings))
    cmd.extend(["-an", output_path])
    subprocess.run(cmd, capture_output=True, check=True)


def create_slideshow(
    images: list[str],
    duration_per_image: float,
    output_path: str,
    settings: EncodingSettings,
    transition: str = "fade",
    transition_duration: float = 1.0,
) -> None:
    """Create a slideshow from multiple images with transitions."""
    ffmpeg = find_ffmpeg()
    w, h = settings.resolution.width, settings.resolution.height

    inputs = []
    for img in images:
        inputs.extend(["-loop", "1", "-t", str(duration_per_image), "-i", img])

    filter_parts = []
    for i in range(len(images)):
        filter_parts.append(
            f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
            f"setsar=1,fps={settings.fps}[v{i}]"
        )

    if len(images) == 1:
        filter_complex = filter_parts[0]
        map_label = "[v0]"
    else:
        xfade_parts = []
        prev = "v0"
        for i in range(1, len(images)):
            offset = duration_per_image * i - transition_duration * i
            out_label = f"xf{i}"
            xfade_parts.append(
                f"[{prev}][v{i}]xfade=transition={transition}:"
                f"duration={transition_duration}:offset={max(0, offset)}[{out_label}]"
            )
            prev = out_label
        filter_complex = ";".join(filter_parts + xfade_parts)
        map_label = f"[{prev}]"

    cmd = [ffmpeg, "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-map", map_label,
    ]
    cmd.extend(build_encoding_args(settings))
    cmd.extend(["-an", output_path])
    subprocess.run(cmd, capture_output=True, check=True)


def add_intro_outro(
    main_video: str,
    output_path: str,
    settings: EncodingSettings,
    intro_path: Optional[str] = None,
    outro_path: Optional[str] = None,
    audio_mode: str = "normal",
) -> None:
    """Add intro and/or outro to the main video.

    audio_mode: 'normal', 'seamless', 'mixed'
    """
    ffmpeg = find_ffmpeg()
    w, h = settings.resolution.width, settings.resolution.height

    segments = []
    if intro_path:
        intro_scaled = tempfile.mktemp(suffix=".mp4")
        cmd = [
            ffmpeg, "-y", "-i", intro_path,
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                   f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,fps={settings.fps}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
            "-pix_fmt", "yuv420p", intro_scaled
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        segments.append(intro_scaled)

    main_scaled = tempfile.mktemp(suffix=".mp4")
    cmd = [
        ffmpeg, "-y", "-i", main_video,
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
               f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,fps={settings.fps}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-pix_fmt", "yuv420p", main_scaled
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    segments.append(main_scaled)

    if outro_path:
        outro_scaled = tempfile.mktemp(suffix=".mp4")
        cmd = [
            ffmpeg, "-y", "-i", outro_path,
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                   f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,fps={settings.fps}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
            "-pix_fmt", "yuv420p", outro_scaled
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        segments.append(outro_scaled)

    list_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    )
    for seg in segments:
        list_file.write(f"file '{seg}'\n")
    list_file.close()

    cmd = [
        ffmpeg, "-y", "-f", "concat", "-safe", "0",
        "-i", list_file.name, "-c", "copy", output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    os.unlink(list_file.name)
    for seg in segments:
        if os.path.exists(seg):
            os.unlink(seg)


def apply_video_transition(
    video1: str,
    video2: str,
    output_path: str,
    transition: str = "fade",
    duration: float = 1.0,
    settings: Optional[EncodingSettings] = None,
) -> None:
    """Apply transition between two video clips."""
    if settings is None:
        settings = EncodingSettings()

    ffmpeg = find_ffmpeg()
    dur1 = get_media_duration(video1)
    offset = max(0, dur1 - duration)
    w, h = settings.resolution.width, settings.resolution.height

    cmd = [
        ffmpeg, "-y",
        "-i", video1, "-i", video2,
        "-filter_complex",
        f"[0:v]scale={w}:{h},fps={settings.fps},setsar=1[v0];"
        f"[1:v]scale={w}:{h},fps={settings.fps},setsar=1[v1];"
        f"[v0][v1]xfade=transition={transition}:duration={duration}:"
        f"offset={offset}[outv];"
        f"[0:a][1:a]acrossfade=d={duration}[outa]",
        "-map", "[outv]", "-map", "[outa]",
    ]
    cmd.extend(build_encoding_args(settings))
    cmd.append(output_path)
    subprocess.run(cmd, capture_output=True, check=True)


def run_ffmpeg_with_progress(
    cmd: list[str],
    total_duration: float,
    progress_callback=None,
) -> None:
    """Run FFmpeg command with progress tracking."""
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")

    stderr_lines = []
    if process.stderr:
        for line in process.stderr:
            stderr_lines.append(line)
            match = time_pattern.search(line)
            if match and progress_callback and total_duration > 0:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds = int(match.group(3))
                centiseconds = int(match.group(4))
                current = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
                progress = min(100, int(current / total_duration * 100))
                progress_callback(progress)

    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {''.join(stderr_lines[-10:])}")
