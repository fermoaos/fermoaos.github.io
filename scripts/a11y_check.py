#!/usr/bin/env python3
"""접근성 게이트 — axe 전 페이지×양 테마 + 포커스 링 대비.

axe 는 포커스 표시자 대비를 보지 않는다. 2026-09-05 에 그 사각으로 라이트 테마의
포커스 링이 형광 노랑(#F2E640) on 종이(#F7F8F6) = 1.22:1 로 사실상 안 보이는 채
살아 있었다(WCAG 2.2 SC 1.4.11 은 3:1). 그래서 대비를 여기서 직접 계산한다.

Usage: .venv/bin/python scripts/a11y_check.py [--port 8899]   (exit 0 = PASS)
       서버는 이 스크립트가 띄웠다 내린다.
"""
import argparse, functools, http.server, json, socketserver, sys, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
AXE = "https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js"
PAGES = ["/", "/en/", "/usecases/", "/cases/mildo/", "/agentos/runtime/", "/404.html"]
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"]
MIN_FOCUS_CONTRAST = 3.0          # WCAG 2.2 SC 1.4.11 non-text contrast


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = (_lin(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):    # 요청 로그가 판정을 덮는다
        pass


def serve(port):
    h = functools.partial(_Quiet, directory=str(SITE))
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", port), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8899)
    args = ap.parse_args()
    from playwright.sync_api import sync_playwright

    fails, checked = [], 0
    srv = serve(args.port)
    base = f"http://127.0.0.1:{args.port}"
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(channel="chrome")
            for path in PAGES:
                for theme in ("light", "dark"):
                    pg = b.new_page(viewport={"width": 1280, "height": 900})
                    pg.goto(base + path)
                    pg.wait_for_timeout(550)
                    if theme == "dark":
                        pg.click("[data-theme-toggle]")
                        pg.wait_for_timeout(280)
                    # 포커스 링이 배경 위에서 실제로 보이는가 (axe 사각지대)
                    px = pg.evaluate("""() => {
                      const cs = getComputedStyle(document.documentElement);
                      const grab = n => cs.getPropertyValue(n).trim();
                      const el = document.createElement('span'); document.body.append(el);
                      const rgb = v => { el.style.color = v; const c = getComputedStyle(el).color;
                        return c.match(/\\d+/g).slice(0,3).map(Number); };
                      const out = {focus: rgb(grab('--focus')), paper: rgb(grab('--paper'))};
                      el.remove(); return out;
                    }""")
                    c = contrast(px["focus"], px["paper"])
                    if c < MIN_FOCUS_CONTRAST:
                        fails.append(f"{path}[{theme}] 포커스 링 대비 {c:.2f}:1 < {MIN_FOCUS_CONTRAST}")
                    pg.add_script_tag(url=AXE)
                    v = pg.evaluate("""async (tags) => {
                      const r = await axe.run(document, {resultTypes:['violations'],
                        runOnly:{type:'tag', values:tags}});
                      return r.violations.map(x => ({id:x.id, impact:x.impact, n:x.nodes.length,
                        sample:x.nodes[0]?.html.slice(0,110)}));
                    }""", TAGS)
                    for x in v:
                        fails.append(f"{path}[{theme}] {x['impact']} {x['id']} ×{x['n']} — {x['sample']}")
                    checked += 1
                    pg.close()

            # 데모 도크를 연 상태 — 사이트에서 상호작용이 가장 많은 표면
            pg = b.new_page(viewport={"width": 1280, "height": 900})
            pg.goto(base + "/")
            pg.wait_for_timeout(700)
            pg.evaluate("document.querySelector('#demo')?.scrollIntoView()")
            pg.wait_for_timeout(2500)
            pg.add_script_tag(url=AXE)
            v = pg.evaluate("""async (tags) => {
              const r = await axe.run(document, {resultTypes:['violations'],
                runOnly:{type:'tag', values:tags}});
              return r.violations.map(x => ({id:x.id, impact:x.impact, n:x.nodes.length}));
            }""", TAGS)
            for x in v:
                fails.append(f"/[dock] {x['impact']} {x['id']} ×{x['n']}")
            checked += 1
            pg.close()
            b.close()
    finally:
        srv.shutdown()

    print(json.dumps({"views": checked, "fails": fails}, ensure_ascii=False, indent=1))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
