#!/usr/bin/env python3
"""링크 게이트 — 내부 경로·앵커는 항상, 외부는 --external 일 때.

내부는 파일이 실제로 있는지 + `#fragment` 가 그 문서에 id 로 존재하는지까지 본다
(경로만 보는 검사는 죽은 앵커를 통째로 놓친다). 외부는 데모 76개가 개인 레포에
얹혀 있어 조용히 썩는다 — 배포 전이나 주기적으로 --external 로 돈다.

Usage: python3 scripts/link_check.py [--external] [--timeout 12]
"""
import argparse, json, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
HREF = re.compile(r'href="([^"]+)"')
ID = re.compile(r'\sid="([^"]+)"')
SKIP_SCHEME = re.compile(r"^(mailto:|tel:|javascript:|data:)")
# 폰트 CDN 은 우리 자산이 아니다 — 죽으면 폰트만 폴백된다
VENDOR = ("fonts.googleapis.com", "fonts.gstatic.com", "cdn.jsdelivr.net")
UA = "Mozilla/5.0 (compatible; fermoa-link-check)"


def resolve(src: Path, href: str) -> Path:
    p = href.split("#", 1)[0]
    if p == "":
        return src
    t = (SITE / p.lstrip("/")) if p.startswith("/") else (src.parent / p).resolve()
    if t.is_dir():
        return t / "index.html"
    if not t.exists() and Path(str(t) + "/index.html").exists():
        return Path(str(t) + "/index.html")
    return t


def probe(url: str, timeout: int):
    try:
        with urlopen(Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
            return r.status, url
    except Exception as err:
        return f"ERR {type(err).__name__}: {str(err)[:60]}", url


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--external", action="store_true")
    ap.add_argument("--timeout", type=int, default=12)
    args = ap.parse_args()

    files = sorted(SITE.rglob("*.html"))
    ids, fails, n_int, external = {}, [], 0, {}

    def id_set(p: Path):
        if p not in ids:
            ids[p] = set(ID.findall(p.read_text(encoding="utf-8"))) if p.exists() else None
        return ids[p]

    for f in files:
        rel = f.relative_to(SITE)
        for href in HREF.findall(f.read_text(encoding="utf-8")):
            if SKIP_SCHEME.match(href):
                continue
            if href.startswith(("http://", "https://")):
                if not any(v in href for v in VENDOR):
                    external.setdefault(href, []).append(str(rel))
                continue
            n_int += 1
            t = resolve(f, href)
            if not t.exists():
                fails.append(f"{rel} -> {href} (파일 없음)")
                continue
            frag = href.split("#", 1)[1] if "#" in href else ""
            if frag and t.suffix == ".html":      # 앵커는 문서에만 있다 (자산은 존재만 본다)
                ids_ = id_set(t)
                if ids_ is not None and frag not in ids_:
                    fails.append(f"{rel} -> {href} (앵커 없음)")

    ext_checked = 0
    if args.external and external:
        with ThreadPoolExecutor(max_workers=12) as ex:
            for status, url in ex.map(lambda u: probe(u, args.timeout), list(external)):
                ext_checked += 1
                if status != 200:
                    fails.append(f"{status} {url} <- {', '.join(external[url][:2])}")

    print(json.dumps({"files": len(files), "internal": n_int,
                      "external_found": len(external), "external_checked": ext_checked,
                      "fails": fails}, ensure_ascii=False, indent=1))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
