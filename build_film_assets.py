#!/usr/bin/env python3
"""Turn the adopted hero film into the site's hero video.

brand/film/draft-v1-36s.mp4 -> site/assets/film/hero.mp4 (muted, faststart) + hero-poster.webp + hero.json
  - the source opens with a ~1s fade from black; the web cut starts where the frame is fully lit so the
    poster (= first frame, what reduced-motion viewers see) reads and the loop seam is S4 -> lit S1.
  - audio is dropped: it is model-generated and nobody has listened to it (generated-audio rule), and a
    hero autoplays muted anyway.
  - hero.json carries what build_pages.py needs: the yellow dot's position in the first frames (the
    page's SVG worldlines converge there) and the second at which S1's stillness ends (the lines let go).
Format is code-owned; the model only made the frames.
"""
import json, pathlib, shutil, subprocess, tempfile
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "brand" / "film" / "draft-v1-36s.mp4"
DST = ROOT / "site" / "assets" / "film"
TRIM_S = 0.9          # fade-from-black ends here (luma plateau measured 2026-09-03)
S2_AT_SRC = 6.0       # scenario §2: S1 정지 0–6s, S2 풀림 starts here (source time)
TIP_SAMPLES = (0.0, 0.2, 0.4, 0.6)   # seconds into the web cut where the film's dot is still lit


def run(*cmd):
    subprocess.run(cmd, check=True)


def frame(path, t, out):
    run("ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(path), "-frames:v", "1", str(out))
    return np.asarray(Image.open(out).convert("RGB")).astype(np.float32)


def yellow_centroid(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    y = (r > 140) & (g > 120) & (b < 110) & ((r + g) / 2 - b > 55)
    if y.sum() < 20:
        return None
    ys, xs = np.nonzero(y)
    return float(xs.mean() / a.shape[1]), float(ys.mean() / a.shape[0])


def main():
    DST.mkdir(parents=True, exist_ok=True)
    mp4 = DST / "hero.mp4"
    run("ffmpeg", "-v", "error", "-y", "-ss", str(TRIM_S), "-i", str(SRC), "-an",
        "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p",
        "-vf", "scale=1280:720", "-r", "24", "-movflags", "+faststart", str(mp4))
    tmp = pathlib.Path(tempfile.mkdtemp())
    first = frame(mp4, 0, tmp / "f0.png")
    Image.fromarray(first.astype(np.uint8)).save(DST / "hero-poster.webp", "WEBP", quality=82, method=6)
    tips = [c for c in (yellow_centroid(frame(mp4, t, tmp / "t.png")) for t in TIP_SAMPLES) if c]
    if not tips:
        raise SystemExit("no lit dot found in the opening frames — check TRIM_S / thresholds")
    tip = [round(float(np.mean([t[0] for t in tips])), 4), round(float(np.mean([t[1] for t in tips])), 4)]
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", str(mp4)]).strip())
    meta = {"src": SRC.name, "trim_s": TRIM_S, "duration_s": round(dur, 2),
            "release_s": round(S2_AT_SRC - TRIM_S, 2), "tip": tip, "width": 1280, "height": 720}
    (DST / "hero.json").write_text(json.dumps(meta, indent=2))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"hero.mp4 {mp4.stat().st_size/1e6:.1f} MB · {dur:.1f}s · tip {tip} · release {meta['release_s']}s")


if __name__ == "__main__":
    main()
