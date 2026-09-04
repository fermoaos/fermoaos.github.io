#!/usr/bin/env python3
"""Cut the conductor out of the generated PNGs so the page's own paper shows through.

Source (brand/character/*.png) -> site/assets/character/<id>-{ink,chalk}-{1536,768}.webp (alpha).
  ink   : dark marks for the graph-paper (light) theme
  chalk : light marks for the blackboard (dark) theme
The one yellow dot (페르) is kept and recolored to the theme's --hold token; the hero source gets a
`-nodot` variant so the page's SVG dot is the only lit dot. Baton-tip coordinates go to tips.json.
Format is code-owned; the model only drew the dots.
"""
import json, pathlib
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "brand" / "character"
DST = ROOT / "site" / "assets" / "character"
INK, CHALK = (0x17, 0x1A, 0x19), (0xEC, 0xE9, 0xDF)          # --ink light / --ink dark
HOLD_L, HOLD_D = (0xF2, 0xE6, 0x40), (0xF5, 0xEA, 0x6A)       # --hold light / dark
PAPER = [p.stem for p in SRC.glob("*-graphpaper.png")]
BOARD = [p.stem for p in SRC.glob("*-blackboard.png")]
HERO = "p2-hold-graphpaper"


def masks(im):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    yellow = (r > 150) & (g > 130) & (b < 120) & ((r + g) / 2 - b > 70)
    return lum, yellow


def alpha_from(lum, on_paper):
    # paper: marks are darker than the sheet; the printed ruling (~220-235) must vanish
    # board: marks are lighter than the board (~25-45)
    a = (232 - lum) / (232 - 95) if on_paper else (lum - 70) / (215 - 70)
    a = np.clip(a, 0, 1) ** 1.35
    return a


def export(stem, on_paper, drop_dot=False, suffix=""):
    im = Image.open(SRC / f"{stem}.png")
    lum, yellow = masks(im)
    a = alpha_from(lum, on_paper)
    tip = None
    if yellow.any():
        ys, xs = np.nonzero(yellow)
        tip = (float(xs.mean() / im.width), float(ys.mean() / im.height))
    for theme, ink, hold in (("ink", INK, HOLD_L), ("chalk", CHALK, HOLD_D)):
        rgba = np.zeros((im.height, im.width, 4), np.uint8)
        rgba[..., :3] = ink
        al = a.copy()
        if drop_dot:
            al[yellow] = 0
        else:
            rgba[yellow, :3] = hold
            al[yellow] = 1
        rgba[..., 3] = (al * 255).astype(np.uint8)
        out = Image.fromarray(rgba, "RGBA")
        for w in (1536, 768):
            o = out.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
            o.save(DST / f"{stem}{suffix}-{theme}-{w}.webp", "WEBP", quality=90, method=6)
    return tip


def main():
    DST.mkdir(parents=True, exist_ok=True)
    for old in DST.glob("*.webp"):
        old.unlink()
    tips = {}
    for stem in PAPER:
        tips[stem] = export(stem, True)
    for stem in BOARD:
        tips[stem] = export(stem, False)
    tips[HERO + "-nodot"] = export(HERO, True, drop_dot=True, suffix="-nodot")
    (DST / "tips.json").write_text(json.dumps(tips, indent=2))
    print("assets:", len(list(DST.glob("*.webp"))), "tips:", {k: v and tuple(round(x, 3) for x in v) for k, v in tips.items()})


if __name__ == "__main__":
    main()
