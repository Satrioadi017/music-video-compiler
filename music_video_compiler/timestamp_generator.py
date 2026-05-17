"""YouTube timestamp and playlist PNG generator."""

import os
from dataclasses import dataclass
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None


@dataclass
class TimestampSettings:
    format_template: str = "{index}. {title}"
    include_duration: bool = False
    number_start: int = 1
    separator: str = " - "


@dataclass
class PlaylistPNGSettings:
    width: int = 1280
    height: int = 720
    bg_color: tuple = (20, 20, 30)
    text_color: tuple = (255, 255, 255)
    accent_color: tuple = (255, 100, 50)
    title_color: tuple = (255, 200, 50)
    font_path: str = ""
    font_size: int = 24
    title_font_size: int = 36
    line_spacing: int = 8
    margin_x: int = 40
    margin_y: int = 40
    title_text: str = "PLAYLIST"
    show_numbers: bool = True
    show_timestamps: bool = True
    show_duration: bool = False
    columns: int = 1
    max_items_per_column: int = 30
    bg_image_path: str = ""
    bg_opacity: float = 0.7
    border_color: tuple = (255, 100, 50)
    border_width: int = 2


def format_time(seconds: float) -> str:
    """Convert seconds to HH:MM:SS or MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_duration(seconds: float) -> str:
    """Format duration in a readable way."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"({minutes}:{secs:02d})"


def generate_youtube_timestamps(
    timestamps: list[tuple[float, str]],
    settings: Optional[TimestampSettings] = None,
) -> str:
    """Generate YouTube-formatted timestamps text.

    Args:
        timestamps: List of (start_time_seconds, title) tuples
        settings: Formatting settings

    Returns:
        Formatted timestamp string for YouTube description
    """
    if settings is None:
        settings = TimestampSettings()

    lines = []
    for i, (start_time, title) in enumerate(timestamps):
        time_str = format_time(start_time)
        index = i + settings.number_start

        line = settings.format_template.format(
            index=index,
            title=title,
            time=time_str,
        )
        line = f"{time_str}{settings.separator}{line}"
        lines.append(line)

    return "\n".join(lines)


def generate_playlist_description(
    timestamps: list[tuple[float, str]],
    title: str = "Music Compilation",
    channel: str = "",
) -> str:
    """Generate a complete YouTube description with timestamps."""
    desc_parts = [
        f"🎵 {title}",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📋 TRACKLIST / TIMESTAMPS:",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    for i, (start_time, song_title) in enumerate(timestamps, 1):
        time_str = format_time(start_time)
        desc_parts.append(f"{time_str} - {i:02d}. {song_title}")

    desc_parts.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"Total tracks: {len(timestamps)}",
    ])

    if channel:
        desc_parts.append(f"Channel: {channel}")

    desc_parts.extend([
        "",
        "🔔 Subscribe for more compilations!",
        "👍 Like & Share if you enjoy!",
        "",
        "#MusicCompilation #Playlist #Music",
    ])

    return "\n".join(desc_parts)


def generate_playlist_png(
    timestamps: list[tuple[float, str]],
    output_path: str,
    settings: Optional[PlaylistPNGSettings] = None,
) -> str:
    """Generate a playlist PNG image.

    Returns the output file path.
    """
    if Image is None:
        raise ImportError(
            "Pillow is required for PNG generation. "
            "Install it with: pip install Pillow"
        )

    if settings is None:
        settings = PlaylistPNGSettings()

    img = Image.new("RGB", (settings.width, settings.height), settings.bg_color)

    if settings.bg_image_path and os.path.isfile(settings.bg_image_path):
        try:
            bg = Image.open(settings.bg_image_path).convert("RGB")
            bg = bg.resize((settings.width, settings.height), Image.LANCZOS)
            overlay = Image.new("RGB", (settings.width, settings.height), settings.bg_color)
            img = Image.blend(bg, overlay, settings.bg_opacity)
        except Exception:
            pass

    draw = ImageDraw.Draw(img)

    try:
        if settings.font_path and os.path.isfile(settings.font_path):
            title_font = ImageFont.truetype(settings.font_path, settings.title_font_size)
            body_font = ImageFont.truetype(settings.font_path, settings.font_size)
        else:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", settings.title_font_size)
                body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", settings.font_size)
            except OSError:
                title_font = ImageFont.load_default()
                body_font = ImageFont.load_default()
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    if settings.border_width > 0:
        bw = settings.border_width
        draw.rectangle(
            [bw // 2, bw // 2, settings.width - bw // 2, settings.height - bw // 2],
            outline=settings.border_color,
            width=bw,
        )

    y = settings.margin_y
    title_bbox = draw.textbbox((0, 0), settings.title_text, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (settings.width - title_w) // 2
    draw.text((title_x, y), settings.title_text, fill=settings.title_color, font=title_font)
    y += (title_bbox[3] - title_bbox[1]) + 15

    line_y = y
    draw.line(
        [(settings.margin_x, line_y), (settings.width - settings.margin_x, line_y)],
        fill=settings.accent_color, width=2,
    )
    y += 15

    col_width = (settings.width - 2 * settings.margin_x) // settings.columns
    items_per_col = len(timestamps) // settings.columns
    remainder = len(timestamps) % settings.columns

    col_x = settings.margin_x
    item_y = y

    for i, (start_time, title) in enumerate(timestamps):
        col_idx = 0
        items_before = 0
        for c in range(settings.columns):
            col_items = items_per_col + (1 if c < remainder else 0)
            if i < items_before + col_items:
                col_idx = c
                break
            items_before += col_items

        if i == items_before:
            item_y = y
            col_x = settings.margin_x + col_idx * col_width

        time_str = format_time(start_time)
        num_str = f"{i + 1:02d}. " if settings.show_numbers else ""
        ts_str = f"{time_str} - " if settings.show_timestamps else ""
        line_text = f"{num_str}{ts_str}{title}"

        max_chars = (col_width - 20) // max(settings.font_size // 2, 1)
        if len(line_text) > max_chars:
            line_text = line_text[:max_chars - 3] + "..."

        draw.text(
            (col_x, item_y),
            time_str if settings.show_timestamps else "",
            fill=settings.accent_color,
            font=body_font,
        )
        ts_offset = len(time_str) * (settings.font_size // 2 + 2) if settings.show_timestamps else 0

        draw.text(
            (col_x + ts_offset, item_y),
            f" {num_str}{title}",
            fill=settings.text_color,
            font=body_font,
        )

        text_bbox = draw.textbbox((0, 0), line_text, font=body_font)
        item_y += (text_bbox[3] - text_bbox[1]) + settings.line_spacing

    footer_text = f"Total: {len(timestamps)} tracks"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=body_font)
    footer_y = settings.height - settings.margin_y - (footer_bbox[3] - footer_bbox[1])

    draw.line(
        [(settings.margin_x, footer_y - 10),
         (settings.width - settings.margin_x, footer_y - 10)],
        fill=settings.accent_color, width=1,
    )
    draw.text(
        (settings.margin_x, footer_y),
        footer_text,
        fill=settings.accent_color,
        font=body_font,
    )

    img.save(output_path, "PNG", quality=95)
    return output_path


def save_timestamps_to_file(
    timestamps: list[tuple[float, str]],
    output_path: str,
    settings: Optional[TimestampSettings] = None,
) -> str:
    """Save timestamps to a text file."""
    text = generate_youtube_timestamps(timestamps, settings)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    return output_path
