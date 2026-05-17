"""Overlay engine for song titles, multi-overlay support, and spectrum visualization."""

import os
import subprocess
from dataclasses import dataclass
from enum import Enum

from .ffmpeg_engine import find_ffmpeg, EncodingSettings, build_encoding_args


class OverlayPosition(Enum):
    TOP_LEFT = ("10", "10", "Top Left")
    TOP_CENTER = ("(w-text_w)/2", "10", "Top Center")
    TOP_RIGHT = ("w-text_w-10", "10", "Top Right")
    CENTER_LEFT = ("10", "(h-text_h)/2", "Center Left")
    CENTER = ("(w-text_w)/2", "(h-text_h)/2", "Center")
    CENTER_RIGHT = ("w-text_w-10", "(h-text_h)/2", "Center Right")
    BOTTOM_LEFT = ("10", "h-text_h-10", "Bottom Left")
    BOTTOM_CENTER = ("(w-text_w)/2", "h-text_h-10", "Bottom Center")
    BOTTOM_RIGHT = ("w-text_w-10", "h-text_h-10", "Bottom Right")

    def __init__(self, x_expr: str, y_expr: str, label: str):
        self.x_expr = x_expr
        self.y_expr = y_expr
        self.label = label


class OverlayType(Enum):
    PNG_TRANSPARENT = "PNG Transparent"
    GIF_ANIMATED = "GIF Animated"
    VIDEO_GREENSCREEN = "Video Greenscreen"
    VIDEO_BLACKSCREEN = "Video Blackscreen"


@dataclass
class SongTitleOverlaySettings:
    enabled: bool = True
    position: OverlayPosition = OverlayPosition.BOTTOM_LEFT
    font_file: str = ""
    font_size: int = 36
    font_color: str = "white"
    bg_color: str = "black@0.6"
    display_duration: float = 5.0
    fade_in: float = 0.5
    fade_out: float = 0.5
    margin_x: int = 20
    margin_y: int = 20
    border_width: int = 2
    shadow_color: str = "black@0.8"
    shadow_x: int = 2
    shadow_y: int = 2


@dataclass
class MultiOverlayItem:
    file_path: str
    overlay_type: OverlayType = OverlayType.PNG_TRANSPARENT
    position_x: str = "0"
    position_y: str = "0"
    opacity: float = 1.0
    scale: float = 1.0
    similarity: float = 0.3
    blend: float = 0.5
    loop: bool = True


@dataclass
class SpectrumOverlaySettings:
    enabled: bool = False
    mode: str = "combined"
    color_scheme: str = "intensity"
    width: int = 640
    height: int = 120
    position: OverlayPosition = OverlayPosition.BOTTOM_CENTER
    opacity: float = 0.8


def build_song_title_filter(
    timestamps: list[tuple[float, str]],
    settings: SongTitleOverlaySettings,
) -> str:
    """Build FFmpeg drawtext filter for song title overlays."""
    if not settings.enabled or not timestamps:
        return ""

    font_arg = ""
    if settings.font_file and os.path.isfile(settings.font_file):
        safe_font = settings.font_file.replace("\\", "/").replace(":", "\\:")
        font_arg = f"fontfile='{safe_font}':"
    else:
        font_arg = "font='Arial':"

    filters = []
    for start_time, title in timestamps:
        safe_title = (
            title.replace("'", "\\'")
            .replace(":", "\\:")
            .replace("\\", "\\\\")
        )

        end_time = start_time + settings.display_duration
        fade_in_end = start_time + settings.fade_in
        fade_out_start = end_time - settings.fade_out

        x_expr = settings.position.x_expr
        y_expr = settings.position.y_expr

        drawtext = (
            f"drawtext="
            f"{font_arg}"
            f"text='{safe_title}':"
            f"fontsize={settings.font_size}:"
            f"fontcolor={settings.font_color}:"
            f"borderw={settings.border_width}:"
            f"bordercolor={settings.shadow_color}:"
            f"shadowx={settings.shadow_x}:"
            f"shadowy={settings.shadow_y}:"
            f"shadowcolor={settings.shadow_color}:"
            f"box=1:boxcolor={settings.bg_color}:boxborderw=8:"
            f"x={x_expr}:y={y_expr}:"
            f"enable='between(t,{start_time},{end_time})':"
            f"alpha='if(lt(t,{fade_in_end}),(t-{start_time})/{settings.fade_in},"
            f"if(gt(t,{fade_out_start}),({end_time}-t)/{settings.fade_out},1))'"
        )
        filters.append(drawtext)

    return ",".join(filters)


def build_multi_overlay_filter(
    overlays: list[MultiOverlayItem],
    base_width: int,
    base_height: int,
) -> tuple[list[str], str]:
    """Build FFmpeg filter for multiple overlays.

    Returns (extra_inputs, filter_string).
    """
    if not overlays:
        return [], ""

    extra_inputs: list[str] = []
    filter_parts: list[str] = []
    current_label = "0:v"

    for i, overlay in enumerate(overlays):
        input_idx = i + 1
        extra_inputs.extend(["-i", overlay.file_path])

        ow = int(base_width * overlay.scale)
        oh = int(base_height * overlay.scale)

        if overlay.overlay_type == OverlayType.VIDEO_GREENSCREEN:
            filter_parts.append(
                f"[{input_idx}:v]scale={ow}:{oh},"
                f"colorkey=green:{overlay.similarity}:{overlay.blend}"
                f"[ovl{i}]"
            )
        elif overlay.overlay_type == OverlayType.VIDEO_BLACKSCREEN:
            filter_parts.append(
                f"[{input_idx}:v]scale={ow}:{oh},"
                f"colorkey=black:{overlay.similarity}:{overlay.blend}"
                f"[ovl{i}]"
            )
        elif overlay.overlay_type == OverlayType.GIF_ANIMATED:
            filter_parts.append(
                f"[{input_idx}:v]scale={ow}:{oh},format=rgba,"
                f"colorchannelmixer=aa={overlay.opacity}[ovl{i}]"
            )
        else:
            filter_parts.append(
                f"[{input_idx}:v]scale={ow}:{oh},format=rgba,"
                f"colorchannelmixer=aa={overlay.opacity}[ovl{i}]"
            )

        out_label = f"tmp{i}" if i < len(overlays) - 1 else "outv"
        filter_parts.append(
            f"[{current_label}][ovl{i}]overlay="
            f"x={overlay.position_x}:y={overlay.position_y}:"
            f"shortest=1[{out_label}]"
        )
        current_label = out_label

    return extra_inputs, ";".join(filter_parts)


def apply_song_titles_to_video(
    input_video: str,
    output_video: str,
    timestamps: list[tuple[float, str]],
    settings: SongTitleOverlaySettings,
    encoding: EncodingSettings,
) -> None:
    """Apply song title overlays to a video."""
    ffmpeg = find_ffmpeg()
    filter_str = build_song_title_filter(timestamps, settings)

    if not filter_str:
        import shutil
        shutil.copy2(input_video, output_video)
        return

    cmd = [
        ffmpeg, "-y",
        "-i", input_video,
        "-vf", filter_str,
    ]
    cmd.extend(build_encoding_args(encoding))
    cmd.append(output_video)

    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _, stderr = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"Title overlay error: {stderr.decode()}")


def apply_spectrum_overlay(
    input_video: str,
    input_audio: str,
    output_video: str,
    settings: SpectrumOverlaySettings,
    encoding: EncodingSettings,
) -> None:
    """Apply audio spectrum visualization overlay to video."""
    if not settings.enabled:
        return

    ffmpeg = find_ffmpeg()
    x_expr = settings.position.x_expr.replace("text_w", str(settings.width))
    x_expr = x_expr.replace("text_h", str(settings.height))
    y_expr = settings.position.y_expr.replace("text_w", str(settings.width))
    y_expr = y_expr.replace("text_h", str(settings.height))

    filter_complex = (
        f"[1:a]showspectrum=s={settings.width}x{settings.height}:"
        f"mode={settings.mode}:color={settings.color_scheme},"
        f"format=rgba,colorchannelmixer=aa={settings.opacity}[spec];"
        f"[0:v][spec]overlay=x={x_expr}:y={y_expr}:shortest=1[outv]"
    )

    cmd = [
        ffmpeg, "-y",
        "-i", input_video,
        "-i", input_audio,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "1:a",
    ]
    cmd.extend(build_encoding_args(encoding))
    cmd.append(output_video)

    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _, stderr = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"Spectrum overlay error: {stderr.decode()}")
