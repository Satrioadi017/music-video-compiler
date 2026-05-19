import logging
import os
import subprocess
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MEDIA_DIR = Path("/tmp/social_media/videos")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


class VideoGenerator:
    def __init__(self):
        self.ffmpeg_path = "ffmpeg"

    async def create_video_from_images(
        self,
        image_paths: list[str],
        audio_path: Optional[str] = None,
        output_name: Optional[str] = None,
        resolution: str = "1920x1080",
        fps: int = 30,
        duration_per_image: float = 3.0,
        transition: str = "fade",
    ) -> str:
        output_name = output_name or f"{uuid.uuid4()}.mp4"
        output_path = str(MEDIA_DIR / output_name)

        filter_parts = []
        inputs = []
        for i, img_path in enumerate(image_paths):
            inputs.extend(["-loop", "1", "-t", str(duration_per_image), "-i", img_path])
            filter_parts.append(
                f"[{i}:v]scale={resolution}:force_original_aspect_ratio=decrease,"
                f"pad={resolution}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[v{i}]"
            )

        concat_inputs = "".join(f"[v{i}]" for i in range(len(image_paths)))
        filter_complex = ";".join(filter_parts)
        filter_complex += f";{concat_inputs}concat=n={len(image_paths)}:v=1:a=0[outv]"

        cmd = [self.ffmpeg_path, "-y"]
        cmd.extend(inputs)

        if audio_path:
            cmd.extend(["-i", audio_path])

        cmd.extend(["-filter_complex", filter_complex, "-map", "[outv]"])

        if audio_path:
            cmd.extend(["-map", f"{len(image_paths)}:a", "-shortest"])

        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            output_path,
        ])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise RuntimeError(f"Video generation failed: {result.stderr[:500]}")
            return output_path
        except subprocess.TimeoutExpired:
            raise RuntimeError("Video generation timed out")

    async def create_text_video(
        self,
        text_slides: list[dict],
        resolution: str = "1920x1080",
        fps: int = 30,
        bg_color: str = "black",
        font_color: str = "white",
        font_size: int = 48,
        audio_path: Optional[str] = None,
    ) -> str:
        output_path = str(MEDIA_DIR / f"{uuid.uuid4()}.mp4")
        width, height = resolution.split("x")

        filter_parts = []
        for i, slide in enumerate(text_slides):
            duration = slide.get("duration", 5)
            text = slide.get("text", "").replace("'", "'\\''")
            filter_parts.append(
                f"color=c={bg_color}:s={resolution}:d={duration}:r={fps},"
                f"drawtext=text='{text}':"
                f"fontcolor={font_color}:fontsize={font_size}:"
                f"x=(w-text_w)/2:y=(h-text_h)/2"
            )

        filter_complex = ";".join(
            f"{part}[v{i}]" for i, part in enumerate(filter_parts)
        )
        concat = "".join(f"[v{i}]" for i in range(len(text_slides)))
        filter_complex += f";{concat}concat=n={len(text_slides)}:v=1:a=0[outv]"

        cmd = [
            self.ffmpeg_path, "-y",
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            output_path,
        ]

        if audio_path:
            cmd.insert(-1, "-i")
            cmd.insert(-1, audio_path)
            cmd.insert(-1, "-shortest")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise RuntimeError(f"Text video generation failed: {result.stderr[:500]}")
            return output_path
        except subprocess.TimeoutExpired:
            raise RuntimeError("Text video generation timed out")

    async def add_overlay(
        self,
        video_path: str,
        overlay_text: str,
        position: str = "bottom",
        font_size: int = 36,
        font_color: str = "white",
    ) -> str:
        output_path = str(MEDIA_DIR / f"{uuid.uuid4()}_overlay.mp4")

        positions = {
            "top": "x=(w-text_w)/2:y=50",
            "center": "x=(w-text_w)/2:y=(h-text_h)/2",
            "bottom": "x=(w-text_w)/2:y=h-text_h-50",
        }
        pos = positions.get(position, positions["bottom"])
        safe_text = overlay_text.replace("'", "'\\''")

        cmd = [
            self.ffmpeg_path, "-y",
            "-i", video_path,
            "-vf", f"drawtext=text='{safe_text}':fontcolor={font_color}:fontsize={font_size}:{pos}",
            "-c:v", "libx264",
            "-c:a", "copy",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"Overlay failed: {result.stderr[:500]}")
        return output_path

    async def resize_video(self, video_path: str, resolution: str = "1080x1920") -> str:
        output_path = str(MEDIA_DIR / f"{uuid.uuid4()}_resized.mp4")
        cmd = [
            self.ffmpeg_path, "-y",
            "-i", video_path,
            "-vf", f"scale={resolution}:force_original_aspect_ratio=decrease,pad={resolution}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-c:a", "copy",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(f"Resize failed: {result.stderr[:500]}")
        return output_path
