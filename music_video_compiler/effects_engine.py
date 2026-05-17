"""Visual effects engine with 30+ effects for video processing."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import random


class EffectCategory(Enum):
    WEATHER = "Weather"
    LIGHT = "Light"
    COLOR = "Color"
    RETRO = "Retro"
    PARTICLE = "Particle"
    DISTORTION = "Distortion"
    OVERLAY = "Overlay"
    SPECTRUM = "Spectrum"


@dataclass
class EffectSettings:
    intensity: float = 0.5
    speed: float = 1.0
    opacity: float = 0.7
    size: float = 1.0
    color: str = "white"
    quality: str = "high"
    custom_params: dict = field(default_factory=dict)


@dataclass
class VisualEffect:
    name: str
    category: EffectCategory
    description: str
    ffmpeg_filter: str
    settings: EffectSettings = field(default_factory=EffectSettings)
    enabled: bool = False

    def get_filter_string(self) -> str:
        """Generate FFmpeg filter string with current settings."""
        return self.ffmpeg_filter.format(
            intensity=self.settings.intensity,
            speed=self.settings.speed,
            opacity=self.settings.opacity,
            size=self.settings.size,
            color=self.settings.color,
        )


# ─── Effect Registry ─────────────────────────────────────────────────────────

ALL_EFFECTS: list[VisualEffect] = [
    # Weather effects
    VisualEffect(
        name="Rain",
        category=EffectCategory.WEATHER,
        description="Realistic rain drops falling effect",
        ffmpeg_filter=(
            "drawbox=x=0:y=0:w=iw:h=ih:color=black@0.1:t=fill,"
            "noise=alls={intensity:.0f}:allf=t+u"
        ),
    ),
    VisualEffect(
        name="Heavy Rain",
        category=EffectCategory.WEATHER,
        description="Heavy rain with streaks",
        ffmpeg_filter=(
            "noise=alls={intensity:.0f}:allf=t+u,"
            "eq=brightness=-0.05:contrast=1.1"
        ),
    ),
    VisualEffect(
        name="Snow",
        category=EffectCategory.WEATHER,
        description="Gentle snowfall particles",
        ffmpeg_filter=(
            "noise=alls={intensity:.0f}:allf=t,"
            "eq=brightness=0.03:contrast=0.95"
        ),
    ),
    VisualEffect(
        name="Blizzard",
        category=EffectCategory.WEATHER,
        description="Intense snow storm",
        ffmpeg_filter=(
            "noise=alls={intensity:.0f}:allf=t+u,"
            "eq=brightness=0.06:contrast=0.9"
        ),
    ),
    VisualEffect(
        name="Fog",
        category=EffectCategory.WEATHER,
        description="Atmospheric fog overlay",
        ffmpeg_filter=(
            "gblur=sigma={intensity}:steps=3,"
            "eq=brightness=0.04:contrast=0.85"
        ),
    ),
    VisualEffect(
        name="Mist",
        category=EffectCategory.WEATHER,
        description="Light misty atmosphere",
        ffmpeg_filter=(
            "gblur=sigma={intensity}:steps=2,"
            "eq=brightness=0.02:contrast=0.92"
        ),
    ),
    # Light effects
    VisualEffect(
        name="Light Leak",
        category=EffectCategory.LIGHT,
        description="Cinematic light leak effect",
        ffmpeg_filter=(
            "curves=r='0/0 0.3/0.35 0.7/0.8 1/1':"
            "g='0/0 0.5/0.5 1/1':"
            "b='0/0 0.3/0.25 1/0.9',"
            "eq=brightness=0.05:saturation=1.2"
        ),
    ),
    VisualEffect(
        name="Lens Flare",
        category=EffectCategory.LIGHT,
        description="Simulated lens flare",
        ffmpeg_filter=(
            "eq=brightness=0.08:contrast=1.1:saturation=1.15,"
            "unsharp=5:5:1.0:5:5:0.0"
        ),
    ),
    VisualEffect(
        name="Bokeh",
        category=EffectCategory.LIGHT,
        description="Bokeh light circles effect",
        ffmpeg_filter=(
            "gblur=sigma={intensity}:steps=4,"
            "eq=brightness=0.03:contrast=1.15:saturation=1.1"
        ),
    ),
    VisualEffect(
        name="Soft Glow",
        category=EffectCategory.LIGHT,
        description="Soft dreamy glow",
        ffmpeg_filter=(
            "gblur=sigma=3:steps=2,"
            "eq=brightness=0.06:contrast=0.95:saturation=1.1"
        ),
    ),
    VisualEffect(
        name="Neon Glow",
        category=EffectCategory.LIGHT,
        description="Vibrant neon light glow",
        ffmpeg_filter=(
            "eq=brightness=0.05:contrast=1.3:saturation=1.8,"
            "unsharp=5:5:1.5"
        ),
    ),
    VisualEffect(
        name="Starburst",
        category=EffectCategory.LIGHT,
        description="Star-shaped light burst",
        ffmpeg_filter=(
            "eq=brightness=0.1:contrast=1.2:saturation=1.1,"
            "unsharp=7:7:2.0"
        ),
    ),
    # Color grading effects
    VisualEffect(
        name="Warm Tone",
        category=EffectCategory.COLOR,
        description="Warm orange/golden color grading",
        ffmpeg_filter=(
            "curves=r='0/0 0.5/0.55 1/1':"
            "g='0/0 0.5/0.48 1/0.95':"
            "b='0/0 0.5/0.42 1/0.85',"
            "eq=saturation=1.15"
        ),
    ),
    VisualEffect(
        name="Cool Tone",
        category=EffectCategory.COLOR,
        description="Cool blue/teal color grading",
        ffmpeg_filter=(
            "curves=r='0/0 0.5/0.45 1/0.9':"
            "g='0/0 0.5/0.48 1/0.95':"
            "b='0/0 0.5/0.55 1/1',"
            "eq=saturation=1.1"
        ),
    ),
    VisualEffect(
        name="Cinematic",
        category=EffectCategory.COLOR,
        description="Hollywood cinematic look",
        ffmpeg_filter=(
            "curves=r='0/0 0.15/0.12 0.5/0.5 0.85/0.88 1/1':"
            "g='0/0 0.15/0.1 0.5/0.47 0.85/0.85 1/0.97':"
            "b='0/0 0.15/0.15 0.5/0.52 0.85/0.82 1/0.95',"
            "eq=contrast=1.1:saturation=0.9"
        ),
    ),
    VisualEffect(
        name="Sepia",
        category=EffectCategory.COLOR,
        description="Classic sepia tone",
        ffmpeg_filter=(
            "colorchannelmixer="
            "0.393:0.769:0.189:0:"
            "0.349:0.686:0.168:0:"
            "0.272:0.534:0.131:0"
        ),
    ),
    VisualEffect(
        name="Monochrome",
        category=EffectCategory.COLOR,
        description="Black and white",
        ffmpeg_filter="hue=s=0,eq=contrast=1.1",
    ),
    VisualEffect(
        name="High Contrast",
        category=EffectCategory.COLOR,
        description="Dramatic high contrast",
        ffmpeg_filter="eq=contrast=1.4:brightness=0.02:saturation=1.2",
    ),
    VisualEffect(
        name="Pastel",
        category=EffectCategory.COLOR,
        description="Soft pastel colors",
        ffmpeg_filter=(
            "eq=brightness=0.08:contrast=0.85:saturation=0.7,"
            "curves=all='0/0.05 0.5/0.55 1/0.95'"
        ),
    ),
    VisualEffect(
        name="Sunset",
        category=EffectCategory.COLOR,
        description="Golden sunset color grading",
        ffmpeg_filter=(
            "curves=r='0/0 0.3/0.4 0.7/0.85 1/1':"
            "g='0/0 0.3/0.28 0.7/0.7 1/0.9':"
            "b='0/0 0.3/0.15 0.7/0.5 1/0.7',"
            "eq=saturation=1.3"
        ),
    ),
    # Retro effects
    VisualEffect(
        name="VHS Retro",
        category=EffectCategory.RETRO,
        description="Classic VHS tape look with tracking lines",
        ffmpeg_filter=(
            "noise=alls=20:allf=t+u,"
            "eq=contrast=1.1:brightness=0.02:saturation=0.85,"
            "unsharp=3:3:-0.5"
        ),
    ),
    VisualEffect(
        name="VHS Glitch",
        category=EffectCategory.RETRO,
        description="VHS with glitch artifacts",
        ffmpeg_filter=(
            "noise=alls=30:allf=t+u,"
            "rgbashift=rh=2:bh=-2,"
            "eq=contrast=1.15:saturation=0.8"
        ),
    ),
    VisualEffect(
        name="8mm Film",
        category=EffectCategory.RETRO,
        description="Old 8mm film camera look",
        ffmpeg_filter=(
            "noise=alls=15:allf=t,"
            "curves=r='0/0.02 0.5/0.55 1/0.98':"
            "g='0/0.01 0.5/0.48 1/0.95':"
            "b='0/0 0.5/0.4 1/0.85',"
            "eq=saturation=0.7:contrast=1.15"
        ),
    ),
    VisualEffect(
        name="Analog TV",
        category=EffectCategory.RETRO,
        description="Old analog television",
        ffmpeg_filter=(
            "noise=alls=25:allf=t+u,"
            "eq=contrast=1.2:saturation=0.7:brightness=-0.02"
        ),
    ),
    VisualEffect(
        name="Polaroid",
        category=EffectCategory.RETRO,
        description="Polaroid instant photo look",
        ffmpeg_filter=(
            "curves=r='0/0.02 0.5/0.56 1/0.98':"
            "g='0/0.02 0.5/0.52 1/0.96':"
            "b='0/0 0.5/0.45 1/0.88',"
            "eq=brightness=0.05:contrast=0.95:saturation=0.85"
        ),
    ),
    # Distortion effects
    VisualEffect(
        name="Glitch",
        category=EffectCategory.DISTORTION,
        description="Digital glitch distortion",
        ffmpeg_filter=(
            "rgbashift=rh=3:rv=3:gh=-2:gv=1:bh=-3:bv=-2,"
            "noise=alls=10:allf=t+u"
        ),
    ),
    VisualEffect(
        name="Chromatic Aberration",
        category=EffectCategory.DISTORTION,
        description="RGB channel split",
        ffmpeg_filter="rgbashift=rh=4:bh=-4:rv=0:bv=0",
    ),
    VisualEffect(
        name="Scan Lines",
        category=EffectCategory.DISTORTION,
        description="CRT scan lines overlay",
        ffmpeg_filter=(
            "noise=alls=5:allf=t,"
            "eq=contrast=1.1:brightness=-0.01"
        ),
    ),
    VisualEffect(
        name="Pixelate",
        category=EffectCategory.DISTORTION,
        description="Pixel art style",
        ffmpeg_filter=(
            "scale=iw/{intensity:.0f}:ih/{intensity:.0f}:flags=neighbor,"
            "scale=iw*{intensity:.0f}:ih*{intensity:.0f}:flags=neighbor"
        ),
    ),
    VisualEffect(
        name="Wave Distortion",
        category=EffectCategory.DISTORTION,
        description="Wavy ripple distortion",
        ffmpeg_filter=(
            "noise=alls=8:allf=t,"
            "eq=contrast=1.05"
        ),
    ),
    # Particle effects
    VisualEffect(
        name="Fire Particles",
        category=EffectCategory.PARTICLE,
        description="Glowing fire embers",
        ffmpeg_filter=(
            "curves=r='0/0 0.3/0.4 0.7/0.9 1/1':"
            "g='0/0 0.3/0.2 0.7/0.6 1/0.8':"
            "b='0/0 0.3/0.05 0.7/0.15 1/0.3',"
            "eq=brightness=0.03:contrast=1.15:saturation=1.4"
        ),
    ),
    VisualEffect(
        name="Sparks",
        category=EffectCategory.PARTICLE,
        description="Electric spark particles",
        ffmpeg_filter=(
            "noise=alls=15:allf=t,"
            "eq=brightness=0.05:contrast=1.3:saturation=1.2"
        ),
    ),
    VisualEffect(
        name="Dust",
        category=EffectCategory.PARTICLE,
        description="Floating dust particles",
        ffmpeg_filter=(
            "noise=alls=8:allf=t,"
            "eq=brightness=0.02:contrast=1.05"
        ),
    ),
    VisualEffect(
        name="Fireflies",
        category=EffectCategory.PARTICLE,
        description="Glowing firefly particles",
        ffmpeg_filter=(
            "noise=alls=5:allf=t,"
            "eq=brightness=0.04:contrast=1.1:saturation=1.1,"
            "gblur=sigma=0.5"
        ),
    ),
    # Overlay effects
    VisualEffect(
        name="Film Grain",
        category=EffectCategory.OVERLAY,
        description="Natural film grain texture",
        ffmpeg_filter="noise=alls=12:allf=t+u",
    ),
    VisualEffect(
        name="Vignette",
        category=EffectCategory.OVERLAY,
        description="Dark corner vignette",
        ffmpeg_filter="vignette=PI/4:mode=forward",
    ),
    VisualEffect(
        name="Strong Vignette",
        category=EffectCategory.OVERLAY,
        description="Heavy dramatic vignette",
        ffmpeg_filter="vignette=PI/3:mode=forward",
    ),
    VisualEffect(
        name="Letterbox",
        category=EffectCategory.OVERLAY,
        description="Cinema letterbox bars",
        ffmpeg_filter=(
            "drawbox=x=0:y=0:w=iw:h=ih*0.1:color=black@1:t=fill,"
            "drawbox=x=0:y=ih*0.9:w=iw:h=ih*0.1:color=black@1:t=fill"
        ),
    ),
    # Spectrum effects
    VisualEffect(
        name="Audio Spectrum",
        category=EffectCategory.SPECTRUM,
        description="Audio frequency spectrum bars",
        ffmpeg_filter="showspectrum=s=640x120:mode=combined:color=intensity",
    ),
    VisualEffect(
        name="Audio Waves",
        category=EffectCategory.SPECTRUM,
        description="Audio waveform visualization",
        ffmpeg_filter="showwaves=s=640x120:mode=line:rate=25",
    ),
    VisualEffect(
        name="Audio Frequency",
        category=EffectCategory.SPECTRUM,
        description="Frequency spectrum analyzer",
        ffmpeg_filter="showfreqs=s=640x120:mode=line:fscale=log",
    ),
]


def get_effects_by_category(category: EffectCategory) -> list[VisualEffect]:
    """Get all effects in a specific category."""
    return [e for e in ALL_EFFECTS if e.category == category]


def get_effect_by_name(name: str) -> Optional[VisualEffect]:
    """Get an effect by its name."""
    for e in ALL_EFFECTS:
        if e.name == name:
            return e
    return None


def get_random_effect(
    exclude_categories: Optional[list[EffectCategory]] = None,
) -> VisualEffect:
    """Get a random effect, optionally excluding certain categories."""
    pool = ALL_EFFECTS
    if exclude_categories:
        pool = [e for e in ALL_EFFECTS if e.category not in exclude_categories]
    effect = random.choice(pool)
    return VisualEffect(
        name=effect.name,
        category=effect.category,
        description=effect.description,
        ffmpeg_filter=effect.ffmpeg_filter,
        settings=EffectSettings(
            intensity=random.uniform(0.3, 0.8),
            speed=random.uniform(0.7, 1.3),
            opacity=random.uniform(0.5, 0.9),
        ),
        enabled=True,
    )


def build_effect_filter_chain(effects: list[VisualEffect]) -> str:
    """Build a combined FFmpeg filter chain from multiple effects."""
    active = [e for e in effects if e.enabled]
    if not active:
        return ""

    filters = []
    for effect in active:
        try:
            f = effect.get_filter_string()
            if f:
                filters.append(f)
        except (KeyError, ValueError):
            filters.append(effect.ffmpeg_filter)

    return ",".join(filters)


def get_all_effect_names() -> list[str]:
    """Get names of all available effects."""
    return [e.name for e in ALL_EFFECTS]


def get_categories() -> list[EffectCategory]:
    """Get all effect categories."""
    return list(EffectCategory)
