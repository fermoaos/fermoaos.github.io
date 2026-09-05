#!/usr/bin/env python3
"""Fermoa OG card (1200x630) — brand tokens and real webfonts, shot with Playwright.

The card is not hand-drawn: it reuses site/assets/style.css so the palette, grid and
type come from the same tokens the site does. Regenerate after a brand change.

Usage: .venv/bin/python scripts/build_og_image.py [--open]
Out:   site/assets/og.png · site/assets/og-en.png  (referenced by build_pages.py head_meta)
"""
import sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
POSE = "character/p2-hold-graphpaper-ink-1536.webp"   # 승인 대기 — 붙잡은 순간
W, H = 1200, 630

CARD = """<!doctype html>
<html lang="__LANG__" data-theme="light"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&display=block" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="assets/style.css">
<style>
  html,body{margin:0;padding:0;overflow:hidden}
  body{width:__W__px;height:__H__px;background-size:40px 40px;word-break:keep-all}
  .card{width:__W__px;height:__H__px;display:grid;grid-template-columns:1fr 460px;
        align-items:center;gap:32px;padding:56px 72px 64px;box-sizing:border-box}
  .brandline{display:flex;align-items:center;gap:14px;margin-bottom:40px}
  .brandline svg{width:40px;height:40px;color:var(--ink)}
  .brandline b{font-family:var(--font-display);font-weight:700;font-size:30px;letter-spacing:-.03em}
  .tag{font-family:var(--font-display);font-weight:700;font-size:76px;line-height:1.02;
       letter-spacing:-.045em;margin:0 0 26px;font-variation-settings:"opsz" 96}
  .tag em{font-style:normal;background:linear-gradient(transparent 62%,var(--hold) 62%);padding:0 .06em}
  .sub{font-size:24px;line-height:1.5;color:var(--muted);max-width:22ch;margin:0;text-wrap:balance}
  html[lang="en"] .sub{max-width:32ch}
  .rule{height:1px;background:var(--rule);margin:34px 0 22px;width:120px}
  .url{font-size:20px;color:var(--muted);letter-spacing:.01em}
  figure{margin:0;display:flex;justify-content:center}
  figure img{width:112%;height:auto;max-height:540px;object-fit:contain}
</style></head><body>
<div class="card">
  <div>
    <div class="brandline">
      <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
        <path d="M4 12 L24 30 M4 30 L24 30 M4 44 L24 30 M24 30 L46 22"/>
        <path d="M15 20 A9 9 0 0 1 33 20"/><circle cx="24" cy="30" r="4.2" fill="var(--hold)"/>
      </svg><b>Fermoa</b>
    </div>
    <p class="tag">__TAG__</p>
    <p class="sub">__SUB__</p>
    <div class="rule"></div>
    <p class="url">fermoaos.github.io</p>
  </div>
  <figure><img src="assets/__POSE__" alt=""></figure>
</div></body></html>"""


COPY = {
    "ko": dict(out="og.png", lang="ko",
               tag="붙잡아,<br><em>모은다.</em>",
               sub="기업의 실제 업무를 에이전트가 사고하고 실행하는 운영체계, AgentOS."),
    "en": dict(out="og-en.png", lang="en",
               tag="Hold,<br><em>and gather.</em>",
               sub="AgentOS — an operating layer where agents reason through and run your real work."),
}


def render(pg, lang) -> Path:
    c = COPY[lang]
    out = SITE / "assets" / c["out"]
    tmp = SITE / f"_og-card-{lang}.html"
    tmp.write_text(CARD.replace("__W__", str(W)).replace("__H__", str(H))
                   .replace("__POSE__", POSE).replace("__LANG__", c["lang"])
                   .replace("__TAG__", c["tag"]).replace("__SUB__", c["sub"]), encoding="utf-8")
    try:
        pg.goto(tmp.as_uri())
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        # 폰트가 실제로 붙었는지 확인한다 — 폴백으로 찍힌 카드는 브랜드가 아니다.
        if not pg.evaluate('document.fonts.check("700 76px Bricolage Grotesque")'):
            raise RuntimeError("Bricolage Grotesque 미로딩 — 네트워크 확인 후 다시")
        pg.screenshot(path=str(out))
    finally:
        tmp.unlink(missing_ok=True)
    return out


def main() -> int:
    from playwright.sync_api import sync_playwright
    made = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        try:
            for lang in COPY:
                made.append(render(pg, lang))
        except RuntimeError as err:
            print(f"FAIL: {err}", file=sys.stderr)
            return 2
        finally:
            b.close()
    for out in made:
        kb = out.stat().st_size / 1024
        print(f"wrote {out.relative_to(ROOT)}  {W}x{H}  {kb:.0f} KB")
        if kb > 800:
            print("WARN: 800KB 초과 — 공유 미리보기가 느려진다", file=sys.stderr)
    if "--open" in sys.argv:
        subprocess.run(["open", *map(str, made)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
