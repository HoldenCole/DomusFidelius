"""
generate_video.py
-----------------
Catholic TikTok Video Generator

Supports two image source modes:
  1. Local images   — "image": "IMG_7653.jpeg" in assets/images/
  2. Pinterest       — "pinterest_query": "traditional latin mass elevation"
                       Downloads and caches in assets/pinterest/

Pinterest images are fetched via pinterest-dl (pip install pinterest-dl).
If Pinterest fails or is unavailable, falls back to local images.

Usage:
    python generate_video.py

Requirements:
    pip install moviepy pillow numpy python-dotenv pinterest-dl
    ffmpeg must be installed on your system
"""

import os
import sys
import json
import hashlib
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
        VideoClip, AudioFileClip, CompositeVideoClip,
        ColorClip, ImageClip,
        concatenate_audioclips,
    )
    from moviepy.video.fx import CrossFadeIn, CrossFadeOut
    from moviepy.audio.fx import AudioFadeIn, AudioFadeOut
except ImportError:
    print("ERROR: moviepy not installed. Run: pip install moviepy")
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install pillow")
    sys.exit(1)

# Pinterest is optional — graceful fallback if not installed
try:
    from pinterest_dl import PinterestDL
    HAS_PINTEREST = True
except ImportError:
    HAS_PINTEREST = False

# ─── Configuration ────────────────────────────────────────────────────────────

OUTPUT_DIR = Path("Videos")
IMAGES_DIR = Path("assets/images")
PINTEREST_DIR = Path("assets/pinterest")
AUDIO_DIR = Path("assets/audio")
FONTS_DIR = Path("assets/fonts")

OUTPUT_DIR.mkdir(exist_ok=True)
PINTEREST_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
CROSSFADE_DURATION = 0.5

# Minimum resolution for Pinterest images (width, height)
PINTEREST_MIN_RES = (640, 640)
# Number of Pinterest results to fetch per query (picks the best one)
PINTEREST_NUM_RESULTS = 8

# ─── Scene Definitions ────────────────────────────────────────────────────────
# Each scene can use either:
#   "image": "filename.jpeg"              — local file in assets/images/
#   "pinterest_query": "search terms"     — search Pinterest, cache result
#   Both (pinterest_query + image)        — try Pinterest first, fall back to local
#
# "Martyrs of the Faith" — rapid-fire montage, 0.5-1s transitions.
# Each martyr: name + how they died, still image from Pinterest.

SCENES = [
    # ── Intro card ──
    {
        "id": "intro",
        "pinterest_query": "colosseum rome oil painting classical art",
        "text": "Martyrs of the Faith",
        "text_size": 95,
        "text_color": "gold",
        "duration": 2.5,
    },
    # ── The Martyrs ──
    {
        "id": "st_stephen",
        "pinterest_query": "stoning of saint stephen baroque painting art",
        "text": "St. Stephen",
        "text_subtitle": "Stoned to death  \u2020 33 AD",
        "text_size": 85,
        "text_color": "white",
        "duration": 2.0,
    },
    {
        "id": "st_peter",
        "pinterest_query": "crucifixion of saint peter caravaggio painting",
        "text": "St. Peter",
        "text_subtitle": "Crucified upside down  \u2020 64 AD",
        "text_size": 85,
        "text_color": "white",
        "duration": 2.0,
    },
    {
        "id": "st_paul",
        "pinterest_query": "beheading of saint paul renaissance painting art",
        "text": "St. Paul",
        "text_subtitle": "Beheaded  \u2020 67 AD",
        "text_size": 85,
        "text_color": "white",
        "duration": 2.0,
    },
    {
        "id": "st_lawrence",
        "pinterest_query": "martyrdom of saint lawrence gridiron baroque oil painting",
        "text": "St. Lawrence",
        "text_subtitle": "Burned on a gridiron  \u2020 258 AD",
        "text_size": 85,
        "text_color": "white",
        "duration": 2.0,
    },
    {
        "id": "st_sebastian",
        "pinterest_query": "saint sebastian tied arrows renaissance oil painting",
        "text": "St. Sebastian",
        "text_subtitle": "Beaten to death  \u2020 288 AD",
        "text_size": 85,
        "text_color": "white",
        "duration": 2.0,
    },
    {
        "id": "st_agnes",
        "pinterest_query": "saint agnes virgin martyr classical oil painting",
        "text": "St. Agnes",
        "text_subtitle": "Beheaded at age 12  \u2020 304 AD",
        "text_size": 85,
        "text_color": "white",
        "duration": 2.0,
    },
    {
        "id": "st_bartholomew",
        "pinterest_query": "martyrdom of saint bartholomew flayed renaissance painting",
        "text": "St. Bartholomew",
        "text_subtitle": "Flayed alive  \u2020 1st century",
        "text_size": 85,
        "text_color": "white",
        "duration": 2.0,
    },
    {
        "id": "st_thomas_becket",
        "pinterest_query": "murder of thomas becket cathedral medieval painting",
        "text": "St. Thomas Becket",
        "text_subtitle": "Murdered in his cathedral  \u2020 1170",
        "text_size": 80,
        "text_color": "white",
        "duration": 2.0,
    },
    {
        "id": "st_joan_of_arc",
        "pinterest_query": "joan of arc at the stake classical oil painting art",
        "text": "St. Joan of Arc",
        "text_subtitle": "Burned at the stake  \u2020 1431",
        "text_size": 85,
        "text_color": "white",
        "duration": 2.0,
    },
    {
        "id": "st_thomas_more",
        "pinterest_query": "saint thomas more portrait holbein painting",
        "text": "St. Thomas More",
        "text_subtitle": "Beheaded  \u2020 1535",
        "text_size": 85,
        "text_color": "white",
        "duration": 2.0,
    },
    {
        "id": "st_isaac_jogues",
        "pinterest_query": "north american martyrs jesuits painting classical art",
        "text": "St. Isaac Jogues",
        "text_subtitle": "Tomahawked  \u2020 1646",
        "text_size": 85,
        "text_color": "white",
        "duration": 2.0,
    },
    {
        "id": "st_maximilian_kolbe",
        "pinterest_query": "maximilian kolbe priest auschwitz catholic saint",
        "text": "St. Maximilian Kolbe",
        "text_subtitle": "Lethal injection, Auschwitz  \u2020 1941",
        "text_size": 80,
        "text_color": "white",
        "duration": 2.0,
    },
    # ── Closing card ──
    {
        "id": "closing",
        "pinterest_query": "crucifix golden light cathedral painting",
        "text": "The blood of martyrs\nis the seed of the Church.",
        "text_subtitle": "Tertullian",
        "text_size": 75,
        "text_color": "gold",
        "duration": 3.5,
    },
]


# ─── Pinterest Sourcing ──────────────────────────────────────────────────────

def _query_cache_key(query: str) -> str:
    """Deterministic filename-safe hash for a Pinterest query."""
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def _load_pinterest_cache() -> dict:
    """Load the Pinterest cache index (query -> local filename)."""
    cache_file = PINTEREST_DIR / "_cache.json"
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    return {}


def _save_pinterest_cache(cache: dict):
    """Persist the Pinterest cache index."""
    cache_file = PINTEREST_DIR / "_cache.json"
    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)


def fetch_pinterest_image(query: str) -> Path | None:
    """Search Pinterest for a query, download the best image, cache it.

    Returns the local Path to the cached image, or None on failure.
    """
    if not HAS_PINTEREST:
        print(f"    pinterest-dl not installed — skipping Pinterest")
        return None

    cache = _load_pinterest_cache()
    cache_key = _query_cache_key(query)

    # Check cache first
    if cache_key in cache:
        cached_path = PINTEREST_DIR / cache[cache_key]
        if cached_path.exists():
            print(f"    Pinterest cache hit: {cached_path.name}")
            return cached_path
        else:
            # Cache entry is stale, remove it
            del cache[cache_key]

    print(f"    Pinterest search: \"{query}\"")
    try:
        scraper = PinterestDL.with_api(
            timeout=15,
            verbose=False,
            max_retries=3,
            retry_delay=1.0,
        )

        media_list = scraper.search(
            query=query,
            num=PINTEREST_NUM_RESULTS,
            min_resolution=PINTEREST_MIN_RES,
            delay=0.3,
        )

        if not media_list:
            print(f"    No Pinterest results for: \"{query}\"")
            return None

        # Filter out unsupported formats (heic, heif, svg, gif)
        import requests
        unsupported = (".heic", ".heif", ".svg", ".gif")
        candidates = sorted(
            media_list,
            key=lambda m: m.resolution[0] * m.resolution[1],
            reverse=True,
        )
        best = None
        for candidate in candidates:
            url_lower = candidate.src.lower()
            if any(url_lower.endswith(ext) for ext in unsupported):
                continue
            best = candidate
            break

        if best is None:
            print(f"    No compatible image format found")
            return None

        print(f"    Found: {best.resolution[0]}x{best.resolution[1]} "
              f"(pin #{best.id})")

        # Download the image directly via requests
        img_url = best.src
        print(f"    Downloading: {img_url[:80]}...")
        resp = requests.get(img_url, timeout=15, headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })
        resp.raise_for_status()

        # Determine extension from content type or URL
        content_type = resp.headers.get("content-type", "")
        if "png" in content_type or img_url.lower().endswith(".png"):
            ext = ".png"
        elif "webp" in content_type or img_url.lower().endswith(".webp"):
            ext = ".webp"
        else:
            ext = ".jpg"

        stable_name = f"{cache_key}{ext}"
        stable_path = PINTEREST_DIR / stable_name
        stable_path.write_bytes(resp.content)

        # Convert webp/png to jpg for consistency
        if ext in (".webp", ".png"):
            jpg_name = f"{cache_key}.jpg"
            jpg_path = PINTEREST_DIR / jpg_name
            Image.open(stable_path).convert("RGB").save(jpg_path, "JPEG", quality=95)
            stable_path.unlink()
            stable_path = jpg_path
            stable_name = jpg_name

        # Verify the image can actually be opened
        try:
            Image.open(stable_path).convert("RGB")
        except Exception:
            print(f"    Downloaded file is not a valid image, removing")
            stable_path.unlink()
            return None

        cache[cache_key] = stable_name
        _save_pinterest_cache(cache)

        print(f"    Saved: {stable_path.name} "
              f"({stable_path.stat().st_size // 1024} KB)")
        return stable_path

    except Exception as e:
        print(f"    Pinterest error: {e}")
        return None


def resolve_scene_image(scene: dict) -> Path | None:
    """Resolve a scene's image: try Pinterest first, then local fallback."""
    pinterest_query = scene.get("pinterest_query")
    local_image = scene.get("image")

    # Try Pinterest if a query is provided
    if pinterest_query:
        path = fetch_pinterest_image(pinterest_query)
        if path:
            return path

    # Fall back to local image
    if local_image:
        local_path = IMAGES_DIR / local_image
        if local_path.exists():
            print(f"    Using local: {local_image}")
            return local_path

    return None


# ─── Still Image Clip ────────────────────────────────────────────────────────

def load_and_prepare_image(image_path: Path) -> np.ndarray:
    """Load image, convert to RGB numpy array."""
    img = Image.open(image_path).convert("RGB")
    return np.array(img)


def center_crop_to_aspect(img_array: np.ndarray,
                          out_w: int, out_h: int) -> np.ndarray:
    """Center-crop image to target aspect ratio, then resize."""
    h, w = img_array.shape[:2]
    target_ratio = out_w / out_h
    img_ratio = w / h

    if img_ratio > target_ratio:
        new_w = int(h * target_ratio)
        x1 = (w - new_w) // 2
        cropped = img_array[:, x1:x1 + new_w]
    else:
        new_h = int(w / target_ratio)
        y1 = (h - new_h) // 2
        cropped = img_array[y1:y1 + new_h, :]

    pil_img = Image.fromarray(cropped)
    pil_img = pil_img.resize((out_w, out_h), Image.LANCZOS)
    return np.array(pil_img)


def make_still_clip(image_path: Path, duration: float):
    """Create a still (non-moving) clip from a photograph."""
    img_array = load_and_prepare_image(image_path)
    frame = center_crop_to_aspect(img_array, VIDEO_WIDTH, VIDEO_HEIGHT)
    clip = ImageClip(frame, duration=duration).with_fps(FPS)
    return clip


# ─── Color Grading ─────────────────────────────────────────────────────────────

def build_vignette(width: int, height: int) -> np.ndarray:
    """Create a vignette mask (darker at edges)."""
    cx, cy = width / 2, height / 2
    Y, X = np.ogrid[:height, :width]
    dist = np.sqrt(((X - cx) / cx) ** 2 + ((Y - cy) / cy) ** 2)
    vignette = np.clip(1 - dist * 0.55, 0.3, 1.0)
    return vignette[:, :, np.newaxis].astype(np.float32)


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
        "/Library/Fonts/Trajan Pro 3 Regular.ttf",
        "/Library/Fonts/Times New Roman.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
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
        print("  Warning: Using default font (install Cinzel for best results)")
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

    lines = text.split("\n")
    line_height = font_size + 12
    total_text_h = line_height * len(lines)
    y_start = (height - total_text_h) // 2

    for i, line in enumerate(lines):
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
        except AttributeError:
            tw = len(line) * (font_size // 2)

        x = (width - tw) // 2
        y = y_start + i * line_height

        draw.text((x + 3, y + 3), line, font=font, fill=shadow_rgba)
        draw.text((x, y), line, font=font, fill=rgba)

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
        draw.text((sx + 2, sub_y + 2), subtitle, font=sub_font,
                  fill=(0, 0, 0, int(160 * alpha)))
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

    base_frame = render_text_frame(text, subtitle, w, h, font_size, color, 1.0)
    base_rgb = base_frame[:, :, :3]
    base_mask = base_frame[:, :, 3].astype(np.float64) / 255.0

    clip = ImageClip(base_rgb, duration=duration, transparent=False)
    mask_clip = ImageClip(base_mask, duration=duration, is_mask=True)

    clip = clip.with_mask(mask_clip)
    clip = clip.with_effects([
        CrossFadeIn(fade),
        CrossFadeOut(fade),
    ])

    return clip


def make_text_sequence_clip(scene: dict, w: int, h: int):
    """Create a clip with rapidly cycling saint names (text_sequence)."""
    sequence = scene["text_sequence"]
    font_size = scene.get("text_size", 90)
    color = scene.get("text_color", "white")
    total_duration = scene["duration"]

    sub_clips = []
    t = 0.0
    for name, dur in sequence:
        frame = render_text_frame(name, None, w, h, font_size, color, 1.0)
        rgb = frame[:, :, :3]
        mask = frame[:, :, 3].astype(np.float64) / 255.0

        clip = ImageClip(rgb, duration=dur, transparent=False)
        mask_clip = ImageClip(mask, duration=dur, is_mask=True)
        clip = clip.with_mask(mask_clip)

        fade = 0.15
        clip = clip.with_effects([
            CrossFadeIn(fade),
            CrossFadeOut(fade),
        ])
        clip = clip.with_start(t)
        sub_clips.append(clip)
        t += dur

    return CompositeVideoClip(sub_clips, size=(w, h)).with_duration(total_duration)


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

    for path in AUDIO_DIR.glob("*.mp3"):
        return path

    print("  Warning: No audio found in assets/audio/. Video will be silent.")
    print("           Add a Gregorian chant .mp3 from archive.org or similar.")
    return None


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("\n Catholic TikTok Video Generator")
    print("=" * 65)

    if HAS_PINTEREST:
        print("  Pinterest sourcing: ENABLED")
    else:
        print("  Pinterest sourcing: DISABLED (pip install pinterest-dl)")

    # Step 1: Resolve images and build clips
    print("\n Step 1: Resolving images and building clips...")
    video_clips = []
    text_clips = []

    for scene in SCENES:
        scene_id = scene["id"]
        print(f"  Scene: {scene_id}")

        image_path = resolve_scene_image(scene)

        if image_path is None:
            print(f"    No image available — using dark frame")
            clip = ColorClip(
                size=(VIDEO_WIDTH, VIDEO_HEIGHT),
                color=[10, 8, 5],
                duration=scene["duration"]
            ).with_fps(FPS)
        else:
            clip = make_still_clip(image_path, scene["duration"])
            clip = clip.image_transform(apply_grade)

        video_clips.append(clip)

        # Handle text: either a single overlay or a rapid sequence
        if "text_sequence" in scene:
            tclip = make_text_sequence_clip(
                scene, VIDEO_WIDTH, VIDEO_HEIGHT
            )
        else:
            tclip = make_text_clip(
                scene, scene["duration"], VIDEO_WIDTH, VIDEO_HEIGHT
            )
        text_clips.append(tclip)

        print(f"    Done")

    # Step 2: Assemble with crossfades
    print("\n Step 2: Assembling with crossfade transitions...")
    if not video_clips:
        print("ERROR: No clips to assemble.")
        return

    final_clips = []
    t = 0
    for i, (vclip, tclip) in enumerate(zip(video_clips, text_clips)):
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

    final_video = CompositeVideoClip(
        final_clips, size=(VIDEO_WIDTH, VIDEO_HEIGHT)
    )

    # Step 3: Add audio
    print("\n Step 3: Adding Gregorian chant...")
    audio_path = find_audio()
    if audio_path:
        try:
            audio = AudioFileClip(str(audio_path))
            vid_duration = final_video.duration

            if audio.duration < vid_duration:
                loops = int(np.ceil(vid_duration / audio.duration))
                audio = concatenate_audioclips([audio] * loops)

            audio = audio.subclipped(0, vid_duration)
            audio = audio.with_effects([
                AudioFadeIn(3.0),
                AudioFadeOut(3.0),
            ])
            final_video = final_video.with_audio(audio)
            print(f"  Audio: {audio_path.name}")
        except Exception as e:
            print(f"  Audio failed: {e}")

    # Step 4: Export
    output_path = OUTPUT_DIR / "final_video.mp4"
    print(f"\n Step 4: Exporting to {output_path}...")
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
        print(f"\n Video saved: {output_path}")
        print(f"   Size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
    except Exception as e:
        print(f"\n Export failed: {e}")
        raise

    print("\n Done!\n")


if __name__ == "__main__":
    main()
