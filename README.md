# 🕊️ Catholic TikTok Video Generator

A Claude Code-powered tool that generates short cinematic vertical videos (9:16) for TikTok and Instagram Reels — highlighting the Catholic Church and Traditional Latin Mass in shaping Western civilization.

**Output:** A 20–25 second vertical video with Gregorian chant, cathedral footage, cinematic color grade, and Latin text overlays.

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/your-username/catholic-video-generator
cd catholic-video-generator

pip install moviepy pillow requests numpy python-dotenv
```

Install FFmpeg:
- **macOS:** `brew install ffmpeg`
- **Ubuntu:** `sudo apt install ffmpeg`
- **Windows:** [ffmpeg.org/download](https://ffmpeg.org/download.html)

### 2. Set Up API Key

Get a free Pexels API key at [pexels.com/api](https://www.pexels.com/api/) (free, no credit card needed).

```bash
cp .env.example .env
# Edit .env and add your key
```

### 3. Add Gregorian Chant Audio

Place an `.mp3` file in `assets/audio/`. Recommended filenames:
- `kyrie_eleison.mp3`
- `dies_irae.mp3`
- `salve_regina.mp3`

Free sources:
- [archive.org](https://archive.org/search?query=gregorian+chant) — search "Gregorian chant"
- [musopen.org](https://musopen.org) — public domain choral music

### 4. (Optional) Add Cinzel Font

Download [Cinzel](https://fonts.google.com/specimen/Cinzel) and place `Cinzel-Regular.ttf` in `assets/fonts/` for best-looking text. The script will fall back to system serif fonts if not present.

### 5. Generate the Video

```bash
python generate_video.py
```

The output video will be at `output/final_video.mp4` and automatically committed to your repo.

---

## Using with Claude Code

Simply open this project in Claude Code and say:

> "Generate the Catholic TikTok video"

Claude Code will read `CLAUDE.md` and `prompts/video_prompt.md`, run the generation script, and push the result to GitHub.

To customize the video, edit `prompts/video_prompt.md` and tell Claude Code:

> "Regenerate the video with the updated prompt"

---

## Project Structure

```
catholic-video-generator/
├── CLAUDE.md                  ← Claude Code instructions (brain file)
├── README.md
├── generate_video.py          ← Main generation script
├── .env.example               ← Environment variable template
├── requirements.txt
├── prompts/
│   └── video_prompt.md        ← Full visual/audio/text specification
├── assets/
│   ├── audio/                 ← Add Gregorian chant .mp3 files here
│   ├── fonts/                 ← Add Cinzel-Regular.ttf here (optional)
│   └── footage/               ← Auto-downloaded and cached video clips
└── output/
    └── final_video.mp4        ← Generated video (committed to repo)
```

---

## Video Spec

| Property | Value |
|---|---|
| Format | MP4, H.264 |
| Resolution | 1080 × 1920 (9:16 vertical) |
| Frame rate | 30fps |
| Duration | 20–25 seconds |
| Transitions | Crossfade dissolve (0.4s) |
| Color grade | Warm golden tones, crushed shadows, vignette, film grain |
| Text font | Cinzel (falls back to Times New Roman) |

---

## Customization

Edit `prompts/video_prompt.md` to change:
- Text displayed in each scene
- Footage search terms
- Music preferences
- Pacing and clip duration

Edit `generate_video.py` → `SCENES` list to reorder, add, or remove scenes.

---

## Large File Handling

For repos with Git LFS enabled:

```bash
git lfs track "*.mp4"
git add .gitattributes
git commit -m "Track mp4 files with LFS"
```

---

## License

Video generation code: MIT License  
Generated videos: Your own content, subject to Pexels license for sourced footage.
