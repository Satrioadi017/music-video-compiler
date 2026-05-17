"""Advanced audio mixing module."""

import os
import subprocess
from dataclasses import dataclass
from typing import Optional

from .ffmpeg_engine import find_ffmpeg, get_media_duration


@dataclass
class AudioMixSettings:
    master_volume: float = 1.0
    effect_audio_volume: float = 0.3
    video_audio_volume: float = 0.0
    front_audio_priority: bool = True
    normalize: bool = True
    fade_in_duration: float = 0.0
    fade_out_duration: float = 0.0
    compressor: bool = False
    eq_preset: str = "none"


EQ_PRESETS = {
    "none": "",
    "bass_boost": "bass=g=6:f=100:w=0.5",
    "treble_boost": "treble=g=4:f=4000:w=0.5",
    "vocal": "equalizer=f=1000:t=h:w=200:g=3,equalizer=f=3000:t=h:w=200:g=2",
    "warm": "bass=g=3:f=120:w=0.4,treble=g=-2:f=6000:w=0.5",
    "bright": "treble=g=3:f=5000:w=0.5,bass=g=-1:f=100:w=0.3",
    "flat": "equalizer=f=100:t=h:w=100:g=0",
    "club": "bass=g=5:f=80:w=0.4,equalizer=f=1000:t=h:w=500:g=2",
    "live": "equalizer=f=500:t=h:w=200:g=-2,treble=g=2:f=8000:w=0.5",
    "lofi": "bass=g=2:f=150:w=0.5,treble=g=-4:f=4000:w=0.5",
}


def mix_audio_tracks(
    main_audio: str,
    effect_audio: Optional[str],
    video_audio: Optional[str],
    output_path: str,
    settings: AudioMixSettings,
) -> None:
    """Mix multiple audio tracks with volume control."""
    ffmpeg = find_ffmpeg()
    inputs = ["-i", main_audio]
    filter_parts = []
    mix_inputs = []

    main_filter = f"[0:a]volume={settings.master_volume}"
    if settings.normalize:
        main_filter += ",loudnorm=I=-14:TP=-2:LRA=11"
    if settings.fade_in_duration > 0:
        main_filter += f",afade=t=in:d={settings.fade_in_duration}"
    if settings.fade_out_duration > 0:
        dur = get_media_duration(main_audio)
        start = max(0, dur - settings.fade_out_duration)
        main_filter += f",afade=t=out:st={start}:d={settings.fade_out_duration}"

    eq = EQ_PRESETS.get(settings.eq_preset, "")
    if eq:
        main_filter += f",{eq}"

    if settings.compressor:
        main_filter += ",acompressor=threshold=-20dB:ratio=4:attack=5:release=50"

    main_filter += "[main]"
    filter_parts.append(main_filter)
    mix_inputs.append("[main]")

    input_idx = 1

    if effect_audio and os.path.isfile(effect_audio):
        inputs.extend(["-i", effect_audio])
        ef = f"[{input_idx}:a]volume={settings.effect_audio_volume}"
        if settings.front_audio_priority:
            ef += ",apad"
        ef += "[effect]"
        filter_parts.append(ef)
        mix_inputs.append("[effect]")
        input_idx += 1

    if video_audio and os.path.isfile(video_audio):
        inputs.extend(["-i", video_audio])
        vf = f"[{input_idx}:a]volume={settings.video_audio_volume}[vidaudio]"
        filter_parts.append(vf)
        mix_inputs.append("[vidaudio]")
        input_idx += 1

    if len(mix_inputs) > 1:
        mix_labels = "".join(mix_inputs)
        filter_parts.append(
            f"{mix_labels}amix=inputs={len(mix_inputs)}:"
            f"duration=longest:dropout_transition=2[out]"
        )
        filter_complex = ";".join(filter_parts)
        cmd = [ffmpeg, "-y"] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
            output_path
        ]
    else:
        filter_complex = filter_parts[0].replace("[main]", "[out]")
        cmd = [ffmpeg, "-y"] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
            output_path
        ]

    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    _, stderr = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"Audio mix error: {stderr.decode()}")


def apply_crossfade(
    audio1: str,
    audio2: str,
    output_path: str,
    crossfade_duration: float = 2.0,
    curve_type: str = "tri",
) -> None:
    """Apply crossfade between two audio files."""
    ffmpeg = find_ffmpeg()
    cmd = [
        ffmpeg, "-y",
        "-i", audio1, "-i", audio2,
        "-filter_complex",
        f"[0:a][1:a]acrossfade=d={crossfade_duration}:"
        f"c1={curve_type}:c2={curve_type}[out]",
        "-map", "[out]",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def normalize_audio(input_path: str, output_path: str) -> None:
    """Normalize audio loudness to broadcast standard."""
    ffmpeg = find_ffmpeg()
    cmd = [
        ffmpeg, "-y",
        "-i", input_path,
        "-af", "loudnorm=I=-14:TP=-2:LRA=11",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def extract_audio_from_video(
    video_path: str,
    output_path: str,
    format_ext: str = "m4a",
) -> None:
    """Extract audio track from a video file."""
    ffmpeg = find_ffmpeg()
    cmd = [
        ffmpeg, "-y",
        "-i", video_path,
        "-vn", "-c:a", "aac", "-b:a", "192k",
        output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
