# CLAUDE.md — Catholic TikTok Video Generator

## What This Project Does

This project generates short cinematic vertical videos (9:16, 20–25 seconds) for TikTok and Instagram Reels. The videos highlight the Catholic Church and Traditional Latin Mass in shaping Western civilization. They are reverent, solemn, and historically styled — Gregorian chant background, cathedral footage, minimal Latin text overlays.

## Your Job When Asked to Generate a Video

1. Read `prompts/video_prompt.md` for the full visual/audio/text specification
2. Run `python generate_video.py` (or create it if it doesn't exist yet — see below)
3. The output video is saved to `output/final_video.mp4`
4. Commit and push the output to GitHub

---

## Stack & Tools

| Layer | Tool | Purpose |
|---|---|---|
| Video composition | `moviepy` | Assemble clips, transitions, overlays |
| Footage sourcing | Pexels API | Free stock footage matching scene descriptions |
| Audio | Local `.mp3` files in `assets/audio/` | Gregorian chant background |
| Text overlays | `moviepy` + PIL/Pillow | Cinzel/Trajan-style white/gold text |
| Color grading | `moviepy` + numpy | Warm golden tones, dark shadows, vignette, grain |
| Output | `output/final_video.mp4` | 1080×1920, H.264, ~20–25s |

---

## Environment Setup (run once)

```bash
# Install Python dependencies
pip install moviepy pillow requests numpy

# FFmpeg must be installed
# macOS:   brew install ffmpeg
# Ubuntu:  sudo apt install ffmpeg
# Windows: https://ffmpeg.org/download.html

# Set your Pexels API key (free at pexels.com/api)
export PEXELS_API_KEY="your_key_here"
```

If the user has provided a `.env` file, load variables from it automatically.

---

## Audio Instructions

Gregorian chant files should be placed in `assets/audio/`. Acceptable filenames:
- `kyrie_eleison.mp3`
- `dies_irae.mp3`
- `salve_regina.mp3`
- `adoro_te_devote.mp3`

If no audio files exist, attempt to download a royalty-free Gregorian chant from the Internet Archive or instruct the user to add one. The audio must:
- Start quietly (fade in for first 3 seconds)
- Build slightly toward the middle
- Fade out over the final 3 seconds
- Be looped or trimmed to match the video length

---

## Footage Sourcing via Pexels

Use the Pexels Video API (`https://api.pexels.com/videos/search`) to search for clips matching each scene description. 

Scene search terms to use (in order):
1. `"gothic cathedral interior candlelight"`
2. `"catholic priest mass altar"`
3. `"incense smoke church"`
4. `"medieval monastery monks"`
5. `"stained glass window sunlight cathedral"`
6. `"stone abbey cloister"`
7. `"illuminated manuscript medieval"`
8. `"saints statues church"`
9. `"cathedral altar candles"`
10. `"roman ruins ancient architecture"` (optional)

For each scene:
- Download the SD or HD version (prefer 1080p)
- Crop/scale to 9:16 (1080×1920) using center crop
- Trim to 2.5–3 seconds
- Cache downloaded files in `assets/footage/` to avoid re-downloading

If Pexels returns no results for a query, try a simplified version of the search term.

---

## Color Grade Specification

Apply this grade to every clip using numpy array manipulation on the MoviePy frame:

```python
def apply_grade(frame):
    # Warm: boost red, slightly reduce blue
    frame = frame.astype(float)
    frame[:,:,0] = np.clip(frame[:,:,0] * 1.12, 0, 255)  # Red up
    frame[:,:,2] = np.clip(frame[:,:,2] * 0.88, 0, 255)  # Blue down

    # Crush shadows
    frame = np.clip((frame / 255.0) ** 1.15 * 255, 0, 255)

    # Film grain
    grain = np.random.normal(0, 6, frame.shape)
    frame = np.clip(frame + grain, 0, 255)

    return frame.astype(np.uint8)
```

After grading, apply a **vignette**: darken edges with a radial gradient mask.

---

## Text Overlay Sequence

Render text using PIL. Use the **Cinzel** font if available in `assets/fonts/`. Fall back to Times New Roman, then a serif system font.

| Scene # | Text | Duration |
|---|---|---|
| 1 | "For over 1,500 years…" | 2.5s |
| 2 | "This was the Mass of the West." | 3s |
| 3 | "Monks prayed it." | 2s |
| 4 | "Saints worshiped this way." | 2s |
| 5 | "Augustine" then "Thomas Aquinas" then "Joan of Arc" then "Padre Pio" | 0.7s each |
| Final | "Lex Orandi\nLex Credendi" (large) + "The Mass that built the West." (small, below) | 3.5s |

Text style:
- Color: white (`#FFFFFF`) or gold (`#D4AF37`) for the final card
- Centered horizontally and vertically
- Font size: ~90px for main text, ~50px for subtitle
- Fade in over 0.3s, hold, fade out over 0.3s
- Drop shadow: offset (2,2), black, 60% opacity

---

## Transition Specification

Between every clip: **crossfade dissolve** of **0.4 seconds**.
Do NOT use wipes, zooms, or hard cuts.
Use `moviepy`'s `CompositeVideoClip` with clip opacity transitions.

---

## Final Assembly Order

1. Source and cache all footage clips
2. Apply color grade to each clip
3. Trim all clips to target duration
4. Add text overlays per scene
5. Concatenate with crossfade transitions
6. Mix in audio (chant, faded in/out)
7. Export to `output/final_video.mp4` at 1080×1920, 30fps, H.264

---

## GitHub Workflow

After generating the video:

```bash
git add output/final_video.mp4
git commit -m "Add generated Catholic TikTok video - $(date +%Y-%m-%d)"
git push origin main
```

If the repo uses Git LFS for large files, ensure LFS is tracking `*.mp4` before committing:
```bash
git lfs track "*.mp4"
git add .gitattributes
```

---

## Error Handling

- If Pexels API is unavailable or quota is exceeded: log the error, use any locally cached footage, and note missing scenes in the commit message
- If no audio file is found: generate the video without audio and warn the user
- If font file is missing: fall back gracefully, log which font was used
- Never crash silently — always print a clear error with the fix

---

## Re-running / Updating

To regenerate with a different prompt or new footage:
1. Edit `prompts/video_prompt.md`
2. Delete `assets/footage/` cache if you want fresh clips
3. Run `python generate_video.py`

To change only the text or music without re-downloading footage, set `USE_CACHED_FOOTAGE=true` in your `.env`.
