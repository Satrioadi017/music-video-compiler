import asyncio
import logging
import os
import signal
import subprocess
from datetime import datetime, timezone
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class LiveStreamService:
    def __init__(self):
        self.active_processes: dict[str, subprocess.Popen] = {}

    def build_ffmpeg_command(
        self,
        video_source: str,
        audio_source: Optional[str],
        rtmp_urls: dict,
        resolution: str = "1920x1080",
        bitrate: str = "4500k",
        fps: int = 30,
        overlay_config: Optional[dict] = None,
    ) -> list[str]:
        width, height = resolution.split("x")

        cmd = ["ffmpeg", "-y", "-re"]

        if video_source.startswith("rtmp://") or video_source.startswith("http"):
            cmd.extend(["-i", video_source])
        else:
            cmd.extend(["-stream_loop", "-1", "-i", video_source])

        if audio_source:
            if audio_source != video_source:
                cmd.extend(["-stream_loop", "-1", "-i", audio_source])

        vf_filters = [f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"]

        if overlay_config:
            if overlay_config.get("text"):
                text = overlay_config["text"].replace("'", "'\\''")
                vf_filters.append(
                    f"drawtext=text='{text}':"
                    f"fontcolor={overlay_config.get('color', 'white')}:"
                    f"fontsize={overlay_config.get('font_size', 24)}:"
                    f"x={overlay_config.get('x', '10')}:"
                    f"y={overlay_config.get('y', '10')}"
                )
            if overlay_config.get("timestamp"):
                vf_filters.append(
                    "drawtext=text='%{localtime}':fontcolor=white:fontsize=20:x=w-tw-10:y=10"
                )

        cmd.extend(["-vf", ",".join(vf_filters)])

        outputs = list(rtmp_urls.values())
        if len(outputs) == 1:
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-b:v", bitrate,
                "-maxrate", bitrate,
                "-bufsize", f"{int(bitrate.replace('k', '')) * 2}k" if bitrate.endswith("k") else bitrate,
                "-g", str(fps * 2),
                "-keyint_min", str(fps),
                "-c:a", "aac",
                "-b:a", "128k",
                "-ar", "44100",
                "-f", "flv",
                outputs[0],
            ])
        else:
            tee_outputs = "|".join(
                f"[f=flv]{url}" for url in outputs
            )
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-b:v", bitrate,
                "-maxrate", bitrate,
                "-g", str(fps * 2),
                "-c:a", "aac",
                "-b:a", "128k",
                "-ar", "44100",
                "-f", "tee",
                "-map", "0:v",
                "-map", "0:a?" if not audio_source or audio_source == video_source else "1:a",
                tee_outputs,
            ])

        return cmd

    def start_stream(self, stream_id: str, cmd: list[str]) -> int:
        logger.info(f"Starting stream {stream_id}: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )
        self.active_processes[stream_id] = process
        return process.pid

    def stop_stream(self, stream_id: str) -> bool:
        process = self.active_processes.get(stream_id)
        if not process:
            return False

        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        finally:
            self.active_processes.pop(stream_id, None)

        return True

    def restart_stream(self, stream_id: str, cmd: list[str]) -> int:
        self.stop_stream(stream_id)
        return self.start_stream(stream_id, cmd)

    def get_stream_status(self, stream_id: str) -> dict:
        process = self.active_processes.get(stream_id)
        if not process:
            return {"running": False, "pid": None}

        poll = process.poll()
        if poll is not None:
            self.active_processes.pop(stream_id, None)
            return {"running": False, "pid": process.pid, "exit_code": poll}

        return {"running": True, "pid": process.pid}

    def is_stream_running(self, stream_id: str) -> bool:
        status = self.get_stream_status(stream_id)
        return status["running"]


livestream_service = LiveStreamService()
