"""
generate_video.py
-----------------
Catholic / Western Civilization TikTok Video Generator

Uses local Marian artwork images with Ken Burns (pan/zoom) effects
instead of stock footage from Pexels.

Usage:
    python generate_video.py

Requirements:
    pip install moviepy pillow numpy python-dotenv
    ffmpeg must be installed on your system
"""

import os
import sys
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

# ─── Configuration ────────────────────────────────────────────────────────────

OUTPUT_DIR = Path("Videos")
IMAGES_DIR = Path("assets/images")
AUDIO_DIR = Path("assets/audio")
FONTS_DIR = Path("assets/fonts")

OUTPUT_DIR.mkdir(exist_ok=True)

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
CROSSFADE_DURATION = 0.4

# ─── Scene Definitions ────────────────────────────────────────────────────────
# Each scene uses a local image file with a Ken Burns motion direction.
# Ken Burns "direction" controls how the camera moves:
#   "zoom_in"   — starts wide, slowly zooms into center
#   "zoom_out"  — starts tight on center, pulls out
#   "pan_up"    — slow upward pan
#   "pan_down"  — slow downward pan
#   "pan_left"  — slow leftward pan
#   "pan_right" — slow rightward pan

SCENES = [
    {
        "id": "our_lady_of_sorrows",
        "image": "IMG_7648.jpeg",
        "ken_burns": "zoom_in",
        "text": "Behold thy Mother",
        "text_size": 90,
        "text_color": "white",
        "duration": 4.0,
    },
    {
        "id": "mystical_rose",
        "image": "IMG_7649.jpeg",
        "ken_burns": "pan_up",
        "text": "Full of Grace",
        "text_size": 90,
        "text_color": "white",
        "duration": 4.0,
    },
    {
        "id": "virgin_in_prayer",
        "image": "IMG_7650.jpeg",
        "ken_burns": "zoom_in",
        "text": "Pray for us sinners",
        "text_size": 90,
        "text_color": "white",
        "duration": 4.0,
    },
    {
        "id": "immaculate_heart",
        "image": "IMG_7651.jpeg",
        "ken_burns": "zoom_out",
        "text": "Immaculate Heart",
        "text_size": 90,
        "text_color": "white",
        "duration": 4.0,
    },
    {
        "id": "assumption",
        "image": "IMG_7652.jpeg",
        "ken_burns": "pan_down",
        "text": "Ave Maria\nGratia Plena",
        "text_subtitle": "The mother who intercedes for the West.",
        "text_size": 90,
        "text_color": "gold",
        "duration": 5.0,
    },
]

# ─── Ken Burns Effect ─────────────────────────────────────────────────────────

def load_and_prepare_image(image_path: Path) -> np.ndarray:
    """Load image, convert to RGB numpy array."""
    img = Image.open(image_path).convert("RGB")
    return np.array(img)


def crop_and_resize(img_array: np.ndarray, cx: float, cy: float,
                    crop_w: float, crop_h: float,
                    out_w: int, out_h: int) -> np.ndarray:
    """Crop a region from img_array and resize to output dimensions."""
    h, w = img_array.shape[:2]

    # Convert fractional coords to pixel coords
    x1 = int(cx * w - crop_w * w / 2)
    y1 = int(cy * h - crop_h * h / 2)
    x2 = int(cx * w + crop_w * w / 2)
    y2 = int(cy * h + crop_h * h / 2)

    # Clamp to image bounds
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w, x2)
    y2 = min(h, y2)

    cropped = img_array[y1:y2, x1:x2]
    pil_img = Image.fromarray(cropped)
    pil_img = pil_img.resize((out_w, out_h), Image.LANCZOS)
    return np.array(pil_img)


def make_ken_burns_clip(image_path: Path, duration: float,
                        direction: str) -> ImageClip:
    """Create a Ken Burns (pan/zoom) clip from a static image.

    The image is loaded once, then each frame crops a smoothly animated
    region and scales it to the output resolution.
    """
    img_array = load_and_prepare_image(image_path)
    img_h, img_w = img_array.shape[:2]

    # Target aspect ratio for the crop window (9:16)
    target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT

    # The image aspect ratio determines whether we're width- or height-limited
    img_ratio = img_w / img_h

    if img_ratio > target_ratio:
        # Image is wider than 9:16 — height-limited
        base_crop_h = 1.0
        base_crop_w = (target_ratio / img_ratio)
    else:
        # Image is taller than 9:16 — width-limited
        base_crop_w = 1.0
        base_crop_h = (img_ratio / target_ratio)

    # Ken Burns zoom factor (how much to zoom over the clip duration)
    zoom_amount = 0.10  # 10% zoom range

    # Define start and end states based on direction
    if direction == "zoom_in":
        start_scale = 1.0
        end_scale = 1.0 - zoom_amount
        start_cx, start_cy = 0.5, 0.5
        end_cx, end_cy = 0.5, 0.5
    elif direction == "zoom_out":
        start_scale = 1.0 - zoom_amount
        end_scale = 1.0
        start_cx, start_cy = 0.5, 0.5
        end_cx, end_cy = 0.5, 0.5
    elif direction == "pan_up":
        start_scale = 1.0 - zoom_amount * 0.5
        end_scale = start_scale
        start_cx, start_cy = 0.5, 0.55
        end_cx, end_cy = 0.5, 0.40
    elif direction == "pan_down":
        start_scale = 1.0 - zoom_amount * 0.5
        end_scale = start_scale
        start_cx, start_cy = 0.5, 0.40
        end_cx, end_cy = 0.5, 0.55
    elif direction == "pan_left":
        start_scale = 1.0 - zoom_amount * 0.5
        end_scale = start_scale
        start_cx, start_cy = 0.55, 0.5
        end_cx, end_cy = 0.40, 0.5
    elif direction == "pan_right":
        start_scale = 1.0 - zoom_amount * 0.5
        end_scale = start_scale
        start_cx, start_cy = 0.40, 0.5
        end_cx, end_cy = 0.55, 0.5
    else:
        start_scale = 1.0
        end_scale = 1.0
        start_cx, start_cy = 0.5, 0.5
        end_cx, end_cy = 0.5, 0.5

    def make_frame(t):
        progress = t / duration if duration > 0 else 0
        # Ease in-out for smoother motion
        progress = 0.5 - 0.5 * np.cos(progress * np.pi)

        scale = start_scale + (end_scale - start_scale) * progress
        cx = start_cx + (end_cx - start_cx) * progress
        cy = start_cy + (end_cy - start_cy) * progress

        crop_w = base_crop_w * scale
        crop_h = base_crop_h * scale

        return crop_and_resize(img_array, cx, cy, crop_w, crop_h,
                               VIDEO_WIDTH, VIDEO_HEIGHT)

    clip = VideoClip(make_frame, duration=duration).with_fps(FPS)
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
    hold = max(duration - 2 * fade, 0.2)

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
    print("\n Catholic TikTok Video Generator (Marian Artwork Edition)")
    print("=" * 55)

    # Step 1: Load images and create Ken Burns clips
    print("\n Step 1: Building Ken Burns clips from artwork...")
    video_clips = []
    text_clips = []

    for scene in SCENES:
        scene_id = scene["id"]
        image_path = IMAGES_DIR / scene["image"]

        if not image_path.exists():
            print(f"  Warning: Missing image {image_path} — using dark frame")
            clip = ColorClip(
                size=(VIDEO_WIDTH, VIDEO_HEIGHT),
                color=[10, 8, 5],
                duration=scene["duration"]
            ).with_fps(FPS)
        else:
            print(f"  Processing: {scene_id} ({scene['image']}, "
                  f"{scene['ken_burns']}, {scene['duration']}s)")
            clip = make_ken_burns_clip(
                image_path, scene["duration"], scene["ken_burns"]
            )
            # Apply color grade
            clip = clip.image_transform(apply_grade)

        video_clips.append(clip)

        text_clip = make_text_clip(
            scene, scene["duration"], VIDEO_WIDTH, VIDEO_HEIGHT
        )
        text_clips.append(text_clip)

        print(f"  Done: {scene_id}")

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

    # Step 5: Git commit
    print("\n Step 5: Committing to Git...")
    date_str = datetime.now().strftime("%Y-%m-%d")
    os.system('git add Videos/final_video.mp4')
    os.system(f'git commit -m "Add Marian TikTok video - {date_str}"')
    print("  Committed (run 'git push' manually to push to remote)")

    print("\n Done!\n")


if __name__ == "__main__":
    main()
