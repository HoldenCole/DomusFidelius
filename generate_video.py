"""
generate_video.py
-----------------
Catholic / Western Civilization TikTok Video Generator

Usage:
    python generate_video.py

Requirements:
    pip install moviepy pillow requests numpy python-dotenv
    ffmpeg must be installed on your system

Environment variables (set in .env or shell):
    PEXELS_API_KEY=your_key_here
    USE_CACHED_FOOTAGE=true   (skip re-downloading if footage already cached)
"""

import os
import sys
import json
import time
import random
import requests
import numpy as np
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from moviepy import (
        VideoFileClip, AudioFileClip, CompositeVideoClip,
        concatenate_videoclips, ColorClip, ImageClip,
        concatenate_audioclips,
    )
    from moviepy.video.fx import CrossFadeIn, CrossFadeOut
    from moviepy.audio.fx import AudioFadeIn, AudioFadeOut
except ImportError:
    print("ERROR: moviepy not installed. Run: pip install moviepy")
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install pillow")
    sys.exit(1)

# ─── Configuration ────────────────────────────────────────────────────────────

OUTPUT_DIR = Path("Videos")
FOOTAGE_DIR = Path("assets/footage")
AUDIO_DIR = Path("assets/audio")
FONTS_DIR = Path("assets/fonts")

OUTPUT_DIR.mkdir(exist_ok=True)
FOOTAGE_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
CROSSFADE_DURATION = 0.4

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
USE_CACHED = os.environ.get("USE_CACHED_FOOTAGE", "false").lower() == "true"

# ─── Scene Definitions ────────────────────────────────────────────────────────

SCENES = [
    {
        "id": "cathedral",
        "search": "gothic cathedral interior candlelight",
        "text": '"Be still, and know\nthat I am God."',
        "text_subtitle": "— Psalm 46:10",
        "text_size": 78,
        "text_color": "white",
        "duration": 3.5,
    },
    {
        "id": "incense",
        "search": "incense smoke church altar",
        "text": '"Pray without ceasing."',
        "text_subtitle": "— 1 Thessalonians 5:17",
        "text_size": 80,
        "text_color": "white",
        "duration": 3.0,
    },
    {
        "id": "monastery",
        "search": "medieval monastery monks cloister",
        "text": '"Ora et Labora"',
        "text_subtitle": "— St. Benedict",
        "text_size": 90,
        "text_color": "white",
        "duration": 2.5,
    },
    {
        "id": "saints_statue",
        "search": "saint statue church cathedral",
        "text": '"The world offers you comfort.\nBut you were not made\nfor comfort.',
        "text_size": 68,
        "text_color": "white",
        "duration": 3.0,
    },
    {
        "id": "saints_quote",
        "search": "stone abbey cloister",
        "text": 'You were made for greatness."',
        "text_subtitle": "— Pope Benedict XVI",
        "text_size": 75,
        "text_color": "white",
        "duration": 2.5,
    },
    {
        "id": "stained_glass",
        "search": "stained glass window sunlight cathedral",
        "text": None,
        "duration": 2.5,
    },
    {
        "id": "crucifix",
        "search": "crucifix church light",
        "text": '"I am the Way, the Truth,\nand the Life."',
        "text_subtitle": "— John 14:6",
        "text_size": 75,
        "text_color": "white",
        "duration": 3.0,
    },
    {
        "id": "manuscript",
        "search": "illuminated manuscript medieval book",
        "text": None,
        "duration": 2.0,
    },
    {
        "id": "final_altar",
        "search": "cathedral altar candles golden light",
        "text": "Ad Majorem\nDei Gloriam",
        "text_subtitle": "For the Greater Glory of God",
        "text_size": 95,
        "text_color": "#D4AF37",
        "duration": 3.5,
    },
]

# ─── Pexels Footage Download ───────────────────────────────────────────────────

def search_pexels_video(query: str, min_duration: int = 5) -> str | None:
    """Search Pexels for a video and return download URL."""
    if not PEXELS_API_KEY:
        print("  ⚠️  No PEXELS_API_KEY set — skipping footage download")
        return None

    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 10, "orientation": "portrait"}

    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params=params,
            timeout=10
        )
        r.raise_for_status()
        data = r.json()

        if not data.get("videos"):
            print(f"  ⚠️  No results for: '{query}'")
            return None

        # Pick the first video with sufficient duration
        for video in data["videos"]:
            if video["duration"] >= min_duration:
                # Prefer HD files
                files = sorted(
                    video.get("video_files", []),
                    key=lambda f: f.get("width", 0),
                    reverse=True
                )
                for f in files:
                    if f.get("width", 0) <= 1920:
                        return f["link"]

        # Fall back to first result
        files = data["videos"][0].get("video_files", [])
        if files:
            return files[0]["link"]

    except Exception as e:
        print(f"  ❌ Pexels API error: {e}")

    return None


def download_footage(scene: dict) -> Path | None:
    """Download footage for a scene, using cache if available."""
    scene_id = scene["id"]
    cache_path = FOOTAGE_DIR / f"{scene_id}.mp4"

    # Use reused footage from another scene
    if "reuse" in scene:
        reuse_path = FOOTAGE_DIR / f"{scene['reuse']}.mp4"
        if reuse_path.exists():
            return reuse_path

    if cache_path.exists() and USE_CACHED:
        print(f"  ✅ Using cached: {scene_id}")
        return cache_path

    print(f"  🔍 Searching footage: {scene['search']}")
    url = search_pexels_video(scene["search"])

    if not url:
        # Try a simplified query
        simplified = " ".join(scene["search"].split()[:2])
        print(f"  🔍 Retry with: {simplified}")
        url = search_pexels_video(simplified)

    if not url:
        print(f"  ❌ Could not find footage for: {scene_id}")
        return None

    print(f"  ⬇️  Downloading: {scene_id}")
    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(cache_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  ✅ Saved: {cache_path}")
        return cache_path
    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        return None


# ─── Color Grading ─────────────────────────────────────────────────────────────

def build_vignette(width: int, height: int) -> np.ndarray:
    """Create a vignette mask (darker at edges)."""
    cx, cy = width / 2, height / 2
    Y, X = np.ogrid[:height, :width]
    dist = np.sqrt(((X - cx) / cx) ** 2 + ((Y - cy) / cy) ** 2)
    vignette = np.clip(1 - dist * 0.55, 0.3, 1.0)
    return vignette[:, :, np.newaxis]  # shape (H, W, 1)


VIGNETTE = None  # lazily initialized


def apply_grade(frame: np.ndarray) -> np.ndarray:
    global VIGNETTE
    frame = frame.astype(np.float32)

    # Warm tone: boost red, reduce blue
    frame[:, :, 0] = np.clip(frame[:, :, 0] * 1.12, 0, 255)
    frame[:, :, 2] = np.clip(frame[:, :, 2] * 0.88, 0, 255)

    # Crush shadows (gamma)
    frame = np.clip((frame / 255.0) ** 1.15 * 255, 0, 255)

    # Film grain
    grain = np.random.normal(0, 6, frame.shape).astype(np.float32)
    frame = np.clip(frame + grain, 0, 255)

    # Vignette
    h, w = frame.shape[:2]
    if VIGNETTE is None or VIGNETTE.shape[:2] != (h, w):
        VIGNETTE = build_vignette(w, h)
    frame = frame * VIGNETTE

    return np.clip(frame, 0, 255).astype(np.uint8)


# ─── Text Overlay ──────────────────────────────────────────────────────────────

def load_font(size: int):
    """Load best available serif font."""
    font_candidates = [
        str(FONTS_DIR / "Cinzel-Regular.ttf"),
        str(FONTS_DIR / "Cinzel-Bold.ttf"),
        "/Library/Fonts/Trajan Pro 3 Regular.ttf",  # macOS
        "/Library/Fonts/Times New Roman.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",  # Linux
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    try:
        return ImageFont.truetype("times.ttf", size)
    except Exception:
        print(f"  ⚠️  Using default font (install Cinzel for best results)")
        return ImageFont.load_default()


def hex_to_rgb(color: str) -> tuple:
    if color.startswith("#"):
        h = color.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    if color == "white":
        return (255, 255, 255)
    if color == "gold":
        return (212, 175, 55)
    return (255, 255, 255)


def render_text_frame(
    text: str,
    subtitle: str | None,
    width: int,
    height: int,
    font_size: int,
    color: str,
    alpha: float = 1.0
) -> np.ndarray:
    """Render a transparent RGBA frame with text centered."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = load_font(font_size)
    rgb = hex_to_rgb(color)
    rgba = (*rgb, int(255 * alpha))
    shadow_rgba = (0, 0, 0, int(160 * alpha))

    # Draw main text (centered)
    lines = text.split("\n")
    line_height = font_size + 12
    total_text_h = line_height * len(lines)
    y_start = (height - total_text_h) // 2

    for i, line in enumerate(lines):
        # Calculate text width for centering
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
        except AttributeError:
            tw = len(line) * (font_size // 2)

        x = (width - tw) // 2
        y = y_start + i * line_height

        # Shadow
        draw.text((x + 3, y + 3), line, font=font, fill=shadow_rgba)
        # Main text
        draw.text((x, y), line, font=font, fill=rgba)

    # Draw subtitle below if present
    if subtitle:
        sub_font_size = font_size // 2
        sub_font = load_font(sub_font_size)
        sub_rgb = (255, 255, 255)
        sub_rgba = (*sub_rgb, int(220 * alpha))

        try:
            bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
            sw = bbox[2] - bbox[0]
        except AttributeError:
            sw = len(subtitle) * (sub_font_size // 2)

        sub_y = y_start + total_text_h + 20
        sx = (width - sw) // 2
        draw.text((sx + 2, sub_y + 2), subtitle, font=sub_font, fill=(0, 0, 0, int(160 * alpha)))
        draw.text((sx, sub_y), subtitle, font=sub_font, fill=sub_rgba)

    return np.array(img)


def make_text_clip(scene: dict, duration: float, w: int, h: int) -> ImageClip | None:
    """Create a fading text overlay clip for a scene."""
    text = scene.get("text")
    if not text:
        return None

    subtitle = scene.get("text_subtitle")
    font_size = scene.get("text_size", 80)
    color = scene.get("text_color", "white")

    fade = 0.3
    hold = max(duration - 2 * fade, 0.2)

    def make_frame(t):
        if t < fade:
            alpha = t / fade
        elif t > fade + hold:
            alpha = max(0, 1 - (t - fade - hold) / fade)
        else:
            alpha = 1.0
        return render_text_frame(text, subtitle, w, h, font_size, color, alpha)

    # Pre-render the full-alpha frame as the base image
    base_frame = make_frame(1.0)
    base_rgb = base_frame[:, :, :3]
    base_mask = base_frame[:, :, 3].astype(np.float64) / 255.0

    clip = ImageClip(base_rgb, duration=duration, transparent=False)
    mask_clip = ImageClip(base_mask, duration=duration, is_mask=True)

    clip = clip.with_mask(mask_clip)

    # Apply fade in/out via opacity
    clip = clip.with_effects([
        CrossFadeIn(fade),
        CrossFadeOut(fade),
    ])

    return clip


# ─── Audio ────────────────────────────────────────────────────────────────────

def find_audio() -> Path | None:
    """Find the best available Gregorian chant audio file."""
    preferred = [
        "kyrie_eleison.mp3",
        "dies_irae.mp3",
        "salve_regina.mp3",
        "adoro_te_devote.mp3",
    ]
    for name in preferred:
        path = AUDIO_DIR / name
        if path.exists():
            return path

    # Search for any mp3 in audio dir
    for path in AUDIO_DIR.glob("*.mp3"):
        return path

    print("  ⚠️  No audio found in assets/audio/. Video will be silent.")
    print("      Add a Gregorian chant .mp3 from archive.org or similar.")
    return None


# ─── Clip Processor ───────────────────────────────────────────────────────────

def process_clip(footage_path: Path, scene: dict) -> VideoFileClip | None:
    """Load, crop to 9:16, grade, and trim a footage clip."""
    try:
        clip = VideoFileClip(str(footage_path), audio=False)
    except Exception as e:
        print(f"  ❌ Could not load {footage_path}: {e}")
        return None

    target_duration = scene["duration"]

    # Trim: pick a random start point if video is longer
    if clip.duration > target_duration + 1:
        max_start = clip.duration - target_duration
        start = random.uniform(0, min(max_start, clip.duration * 0.5))
        clip = clip.subclipped(start, start + target_duration)
    else:
        clip = clip.subclipped(0, min(clip.duration, target_duration))

    # Crop to 9:16
    src_ratio = clip.w / clip.h
    target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT

    if src_ratio > target_ratio:
        # Wider than needed — crop sides
        new_w = int(clip.h * target_ratio)
        x1 = (clip.w - new_w) // 2
        clip = clip.cropped(x1=x1, y1=0, x2=x1 + new_w, y2=clip.h)
    else:
        # Taller than needed — crop top/bottom
        new_h = int(clip.w / target_ratio)
        y1 = (clip.h - new_h) // 4  # slightly favor upper portion
        clip = clip.cropped(x1=0, y1=y1, x2=clip.w, y2=y1 + new_h)

    clip = clip.resized((VIDEO_WIDTH, VIDEO_HEIGHT))

    # Apply color grade
    clip = clip.image_transform(apply_grade)

    return clip


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n🎬 Catholic TikTok Video Generator")
    print("=" * 45)

    # Step 1: Download footage
    print("\n📥 Step 1: Sourcing footage...")
    footage_map = {}
    for scene in SCENES:
        scene_id = scene["id"]
        if "reuse" in scene:
            print(f"  ♻️  {scene_id} → reusing {scene['reuse']}")
            continue
        path = download_footage(scene)
        footage_map[scene_id] = path
        time.sleep(0.5)  # polite rate limiting

    # Step 2: Build video clips
    print("\n🎞️  Step 2: Processing clips...")
    video_clips = []
    text_clips = []

    for scene in SCENES:
        scene_id = scene["id"]
        reuse_id = scene.get("reuse", scene_id)
        footage_path = footage_map.get(reuse_id)

        if footage_path is None:
            print(f"  ⚠️  No footage for {scene_id} — using black frame")
            clip = ColorClip(
                size=(VIDEO_WIDTH, VIDEO_HEIGHT),
                color=[10, 8, 5],
                duration=scene["duration"]
            ).with_fps(FPS)
        else:
            clip = process_clip(footage_path, scene)
            if clip is None:
                clip = ColorClip(
                    size=(VIDEO_WIDTH, VIDEO_HEIGHT),
                    color=[10, 8, 5],
                    duration=scene["duration"]
                ).with_fps(FPS)

        video_clips.append(clip)

        # Create text overlay
        text_clip = make_text_clip(scene, scene["duration"], VIDEO_WIDTH, VIDEO_HEIGHT)
        text_clips.append(text_clip)

        print(f"  ✅ {scene_id} ({scene['duration']}s)")

    # Step 3: Concatenate with crossfades
    print("\n✂️  Step 3: Assembling with crossfades...")
    if len(video_clips) == 0:
        print("❌ No clips to assemble.")
        return

    final_clips = []
    t = 0
    for i, (vclip, tclip) in enumerate(zip(video_clips, text_clips)):
        # Apply crossfade in/out
        effects = []
        if i > 0:
            effects.append(CrossFadeIn(CROSSFADE_DURATION))
        if i < len(video_clips) - 1:
            effects.append(CrossFadeOut(CROSSFADE_DURATION))
        if effects:
            vclip = vclip.with_effects(effects)

        vclip = vclip.with_start(t)

        if tclip:
            tclip = tclip.with_start(t)
            final_clips.append(vclip)
            final_clips.append(tclip)
        else:
            final_clips.append(vclip)

        t += vclip.duration - CROSSFADE_DURATION

    final_video = CompositeVideoClip(final_clips, size=(VIDEO_WIDTH, VIDEO_HEIGHT))

    # Step 4: Add audio
    print("\n🎵 Step 4: Adding Gregorian chant...")
    audio_path = find_audio()
    if audio_path:
        try:
            audio = AudioFileClip(str(audio_path))
            vid_duration = final_video.duration

            # Loop if needed
            if audio.duration < vid_duration:
                loops = int(np.ceil(vid_duration / audio.duration))
                audio = concatenate_audioclips([audio] * loops)

            audio = audio.subclipped(0, vid_duration)

            # Fade in and out
            audio = audio.with_effects([
                AudioFadeIn(3.0),
                AudioFadeOut(3.0),
            ])
            final_video = final_video.with_audio(audio)
            print(f"  ✅ Audio: {audio_path.name}")
        except Exception as e:
            print(f"  ❌ Audio failed: {e}")

    # Step 5: Export
    output_path = OUTPUT_DIR / "final_video.mp4"
    print(f"\n💾 Step 5: Exporting to {output_path}...")
    print(f"   Duration: {final_video.duration:.1f}s")

    try:
        final_video.write_videofile(
            str(output_path),
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            preset="slow",
            ffmpeg_params=["-crf", "20", "-pix_fmt", "yuv420p"],
            logger="bar",
        )
        print(f"\n✅ Video saved: {output_path}")
        print(f"   Size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        raise

    # Step 6: Git commit
    print("\n📤 Step 6: Committing to Git...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    os.system('git add Videos/final_video.mp4')
    os.system(f'git commit -m "Add Catholic TikTok video - {date_str}"')
    print("  ✅ Committed (run 'git push' manually to push to remote)")

    print("\n🏁 Done!\n")


if __name__ == "__main__":
    main()
