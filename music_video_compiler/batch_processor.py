"""Batch and mass processing module for video compilation."""

import os
import random
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .ffmpeg_engine import (
    EncodingSettings,
    concat_audio_files,
    get_media_duration,
    loop_video_to_duration,
    merge_video_audio,
)
from .effects_engine import (
    VisualEffect,
    get_random_effect,
)


@dataclass
class BatchItem:
    audio_files: list[str] = field(default_factory=list)
    video_file: str = ""
    output_name: str = ""
    effects: list[VisualEffect] = field(default_factory=list)
    shuffle_audio: bool = False


@dataclass
class BatchSettings:
    output_dir: str = ""
    encoding: EncodingSettings = field(default_factory=EncodingSettings)
    random_effects: bool = False
    random_audio_order: bool = False
    crossfade_duration: float = 0.0
    num_variations: int = 1


@dataclass
class BatchProgress:
    total_items: int = 0
    completed_items: int = 0
    current_item: str = ""
    current_progress: int = 0
    errors: list[str] = field(default_factory=list)
    is_cancelled: bool = False


class BatchProcessor:
    """Process multiple video compilation jobs."""

    def __init__(self):
        self.progress = BatchProgress()
        self._cancel_flag = False

    def cancel(self):
        """Request cancellation of current batch."""
        self._cancel_flag = True
        self.progress.is_cancelled = True

    def process_batch(
        self,
        items: list[BatchItem],
        settings: BatchSettings,
        progress_callback=None,
    ) -> list[str]:
        """Process a batch of video compilation items.

        Returns list of output file paths.
        """
        self._cancel_flag = False
        self.progress = BatchProgress(total_items=len(items))
        outputs: list[str] = []

        os.makedirs(settings.output_dir, exist_ok=True)

        for i, item in enumerate(items):
            if self._cancel_flag:
                break

            self.progress.current_item = item.output_name or f"batch_{i + 1}"
            self.progress.current_progress = 0

            try:
                output = self._process_single_item(item, settings, i)
                outputs.append(output)
                self.progress.completed_items += 1
            except Exception as e:
                error_msg = f"Error processing {self.progress.current_item}: {e}"
                self.progress.errors.append(error_msg)

            if progress_callback:
                progress_callback(self.progress)

        return outputs

    def process_mass_batch(
        self,
        audio_files: list[str],
        video_file: str,
        settings: BatchSettings,
        progress_callback=None,
    ) -> list[str]:
        """Process mass batch with variations.

        Creates multiple outputs with different audio orders and effects.
        """
        self._cancel_flag = False
        self.progress = BatchProgress(total_items=settings.num_variations)
        outputs: list[str] = []

        os.makedirs(settings.output_dir, exist_ok=True)

        for var in range(settings.num_variations):
            if self._cancel_flag:
                break

            self.progress.current_item = f"variation_{var + 1}"

            shuffled_audio = list(audio_files)
            if settings.random_audio_order:
                random.shuffle(shuffled_audio)

            effects: list[VisualEffect] = []
            if settings.random_effects:
                effects = [get_random_effect()]

            item = BatchItem(
                audio_files=shuffled_audio,
                video_file=video_file,
                output_name=f"compilation_v{var + 1}",
                effects=effects,
                shuffle_audio=False,
            )

            try:
                output = self._process_single_item(item, settings, var)
                outputs.append(output)
                self.progress.completed_items += 1
            except Exception as e:
                self.progress.errors.append(
                    f"Error on variation {var + 1}: {e}"
                )

            if progress_callback:
                progress_callback(self.progress)

        return outputs

    def _process_single_item(
        self,
        item: BatchItem,
        settings: BatchSettings,
        index: int,
    ) -> str:
        """Process a single batch item."""
        audio_files = list(item.audio_files)
        if item.shuffle_audio:
            random.shuffle(audio_files)

        temp_audio = tempfile.mktemp(suffix=".m4a")
        timestamps = concat_audio_files(
            audio_files,
            temp_audio,
            crossfade_duration=settings.crossfade_duration,
        )

        total_duration = get_media_duration(temp_audio)

        temp_video = tempfile.mktemp(suffix=".mp4")
        loop_video_to_duration(
            item.video_file,
            total_duration,
            temp_video,
            settings.encoding,
        )

        output_name = item.output_name or f"output_{index + 1}"
        output_path = os.path.join(settings.output_dir, f"{output_name}.mp4")

        merge_video_audio(
            temp_video,
            temp_audio,
            output_path,
            settings.encoding,
        )

        for f in [temp_audio, temp_video]:
            if os.path.exists(f):
                os.unlink(f)

        timestamps_file = os.path.join(
            settings.output_dir, f"{output_name}_timestamps.txt"
        )
        from .timestamp_generator import generate_youtube_timestamps
        ts_text = generate_youtube_timestamps(timestamps)
        with open(timestamps_file, "w", encoding="utf-8") as f:
            f.write(ts_text)

        return output_path


def get_supported_audio_extensions() -> list[str]:
    """Get list of supported audio file extensions."""
    return [
        ".mp3", ".wav", ".flac", ".aac", ".m4a",
        ".ogg", ".wma", ".opus", ".aiff",
    ]


def get_supported_video_extensions() -> list[str]:
    """Get list of supported video file extensions."""
    return [
        ".mp4", ".avi", ".mkv", ".mov", ".wmv",
        ".flv", ".webm", ".m4v", ".ts",
    ]


def get_supported_image_extensions() -> list[str]:
    """Get list of supported image file extensions."""
    return [".jpg", ".jpeg", ".png", ".webp", ".jfif", ".bmp", ".tiff"]


def scan_audio_files(directory: str) -> list[str]:
    """Scan directory for audio files."""
    extensions = get_supported_audio_extensions()
    files = []
    for f in sorted(Path(directory).iterdir()):
        if f.suffix.lower() in extensions:
            files.append(str(f))
    return files


def scan_video_files(directory: str) -> list[str]:
    """Scan directory for video files."""
    extensions = get_supported_video_extensions()
    files = []
    for f in sorted(Path(directory).iterdir()):
        if f.suffix.lower() in extensions:
            files.append(str(f))
    return files


def scan_image_files(directory: str) -> list[str]:
    """Scan directory for image files."""
    extensions = get_supported_image_extensions()
    files = []
    for f in sorted(Path(directory).iterdir()):
        if f.suffix.lower() in extensions:
            files.append(str(f))
    return files
