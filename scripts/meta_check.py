#!/usr/bin/env python3
"""공유·검색 메타 게이트 — 모든 페이지가 canonical/OG/Twitter/hreflang/JSON-LD 를 갖췄나.

주장 말고 실행: build_pages.py 를 고친 뒤 이걸 통과해야 push 한다.
Usage: python3 scripts/meta_check.py   (exit 0 = PASS)
"""
import json, re, sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
ORIGIN = "https://fermoaos.github.io"
NEED = ('rel="canonical"', 'property="og:title"', 'property="og:image"', 'property="og:url"',
        'name="twitter:card"', 'hreflang="x-default"', 'application/ld+json')


def main() -> int:
    bad, pages = [], sorted(SITE.rglob("index.html"))
    for f in pages:
        rel = f.relative_to(SITE)
        s = f.read_text(encoding="utf-8")
        for tag in NEED:
            if tag not in s:
                bad.append(f"{rel}: {tag} 없음")
        for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                json.loads(m)
            except Exception as err:
                bad.append(f"{rel}: JSON-LD 파싱 실패 — {err}")
        for href in re.findall(r'<link rel="alternate" hreflang="[^"]+" href="([^"]+)"', s):
            if not href.startswith(ORIGIN):
                bad.append(f"{rel}: hreflang 이 절대 URL 이 아니다 — {href}")
        # canonical 은 이 페이지의 실제 경로여야 한다 (복붙으로 홈 URL 이 남는 사고 방지)
        can = re.search(r'<link rel="canonical" href="([^"]+)"', s)
        if can:
            want = "/" + str(rel.parent).replace(".", "").strip("/")
            want = (want.rstrip("/") + "/") if want != "/" else "/"
            if urlparse(can.group(1)).path != want:
                bad.append(f"{rel}: canonical 경로 불일치 — {can.group(1)} (기대 {want})")
        for img in re.findall(r'content="(https://[^"]+/assets/og[^"]*\.png)"', s):
            if not (SITE / "assets" / Path(img).name).exists():
                bad.append(f"{rel}: og 이미지 파일 없음 — {Path(img).name}")

    for extra in ("sitemap.xml", "robots.txt"):
        if not (SITE / extra).exists():
            bad.append(f"{extra} 없음")
    if (SITE / "sitemap.xml").exists():
        locs = re.findall(r"<loc>(.*?)</loc>", (SITE / "sitemap.xml").read_text(encoding="utf-8"))
        if len(locs) != len(pages):
            bad.append(f"sitemap {len(locs)}건 vs 페이지 {len(pages)}건")
        for loc in locs:
            p = urlparse(loc).path.strip("/")
            if not (SITE / p / "index.html").exists():
                bad.append(f"sitemap 이 없는 페이지를 가리킨다 — {loc}")

    print(json.dumps({"pages": len(pages), "fails": bad}, ensure_ascii=False, indent=1))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
