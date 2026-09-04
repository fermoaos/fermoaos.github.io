#!/usr/bin/env python3
"""Fermoa subpage generator. Content lives in site/content/pages.json; this file owns the format.
Usage: python3 build_pages.py   (idempotent; writes site/{agentos,cases}/<slug>/index.html and site/en/...)
"""
import json, html, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "site"
DATA = json.loads((ROOT / "content" / "pages.json").read_text(encoding="utf-8"))
DEMOS = json.loads((ROOT / "content" / "demos.json").read_text(encoding="utf-8"))

T = {
  "ko": dict(lang="ko", home="../../", skip="본문으로 건너뛰기", nav=["AgentOS","Agentic Ops","Use Cases","Insights","Company"],
             theme="칠판", theme_light="칠판", theme_dark="그래프지", contact="문의하기", other="ENG",
             kinds={"agentos":"AgentOS","cases":"Use Cases"}, facts="실측과 사실", impl="구현", status="지금 상태",
             related={"agentos":"다른 계층","cases":"다른 사례"}, cta_h="이 계층을 붙잡아 보시겠어요?", cta_p="실험에서 실행까지 같이 갑니다.",
             biz="(주)페르모아 | 대표 ○○○ | 사업자등록번호 000-00-00000 | 서울특별시 ○○구 ○○로 00", back="목록으로"),
  "en": dict(lang="en", home="../../../", skip="Skip to content", nav=["AgentOS","Agentic Ops","Use Cases","Insights","Company"],
             theme="Blackboard", theme_light="Blackboard", theme_dark="Graph paper", contact="Contact", other="KOR",
             kinds={"agentos":"AgentOS","cases":"Use Cases"}, facts="Measured and factual", impl="Implementation", status="Current state",
             related={"agentos":"Other layers","cases":"Other cases"}, cta_h="Want to hold this layer?", cta_p="From experiment to execution, together.",
             biz="Fermoa Inc. | CEO ○○○ | Business registration 000-00-00000 | Seoul, Korea", back="Back to the list"),
}
ANCH = {"AgentOS":"#agentos","Agentic Ops":"#ops","Use Cases":"#cases","Insights":"#insights","Company":"#company"}
MARK = '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="mark" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M4 12 L24 30 M4 30 L24 30 M4 44 L24 30 M24 30 L46 22"/><path d="M15 20 A9 9 0 0 1 33 20"/><circle cx="24" cy="30" r="4.2" fill="var(--hold)"/></symbol></svg>'

def e(s): return html.escape(s, quote=True)

def page(kind, item, lang):
    t = T[lang]; c = item[lang]; home = t["home"]
    assets = home + "assets/"
    site_home = home + ("index.html" if lang == "ko" else "en/index.html")
    other_home = home + ("en/index.html" if lang == "ko" else "index.html")
    # sibling page in the other language
    other_page = (home + f"en/{kind}/{item['slug']}/index.html") if lang == "ko" else (home + f"{kind}/{item['slug']}/index.html")
    title = c["title"]
    nav = "".join(f'<a href="{site_home}{ANCH[n]}">{n}</a>' for n in t["nav"])
    body = "".join(f"<p>{e(p)}</p>" for p in c["body"])
    facts = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in c["facts"])
    siblings = [x for x in DATA[kind] if x["slug"] != item["slug"]]
    rel = "".join(f'<li><a href="../{x["slug"]}/index.html">{e(x[lang]["title"])}</a></li>' for x in siblings)
    kind_label = t["kinds"][kind]
    return f"""<!doctype html>
<html lang="{lang}" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} — Fermoa</title>
<meta name="description" content="{e(c['lede'])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300..800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="{assets}style.css">
<link rel="icon" href="{assets}mark.svg" type="image/svg+xml">
<link rel="alternate" hreflang="{'en' if lang=='ko' else 'ko'}" href="{other_page}">
</head>
<body class="sub">
<a class="skip" href="#main">{t['skip']}</a>
<header class="top">
  <a class="brand" href="{site_home}" aria-label="Fermoa"><svg class="mark" viewBox="0 0 48 48" aria-hidden="true"><use href="#mark"/></svg><span class="wordmark">Fermoa</span></a>
  <nav class="nav" aria-label="Main">{nav}</nav>
  <div class="top-tools">
    <button class="theme" type="button" data-theme-toggle data-label-light="{t['theme_light']}" data-label-dark="{t['theme_dark']}">{t['theme']}</button>
    <span class="lang"><a href="{other_page}" hreflang="{'en' if lang=='ko' else 'ko'}">{t['other']}</a></span>
    <a class="btn btn-ink" href="{site_home}#contact">{t['contact']}</a>
  </div>
</header>
<main id="main">
<section class="page-hero">
  <p class="crumb"><a href="{site_home}{'#agentos' if kind=='agentos' else '#cases'}">{kind_label}</a></p>
  <div class="page-hero-grid">
    <div>
      <h1>{e(title)}</h1>
      <p class="lede">{e(c['lede'])}</p>
    </div>
    <div class="xbox" data-label="IMG 3:2" style="--ar:3/2"></div>
  </div>
</section>
<section class="page-body">
  <div class="prose">{body}</div>
  <aside class="facts" aria-label="{t['facts']}">
    <h2>{t['facts']}</h2>
    <dl>{facts}</dl>
    <p class="impl"><span>{t['impl']}</span> {e(item['impl'])}</p>
    <p class="impl"><span>{t['status']}</span> {e(item['status'][lang])}</p>
  </aside>
</section>
<section class="related">
  <h2>{t['related'][kind]}</h2>
  <ul>{rel}</ul>
  <p><a class="btn btn-line" href="{site_home}{'#agentos' if kind=='agentos' else '#cases'}">{t['back']}</a></p>
</section>
<section class="page-cta">
  <h2>{t['cta_h']}</h2>
  <p>{t['cta_p']}</p>
  <a class="btn btn-ink" href="{site_home}#contact">{t['contact']}</a>
</section>
</main>
<footer class="foot foot-sub">
  <div class="foot-base"><p class="biz">{t['biz']}</p><p class="copy">© <span data-year>2026</span> Fermoa. All rights reserved.</p></div>
</footer>
{MARK}
<script src="{assets}main.js" defer></script>
</body>
</html>
"""


HOME_T = {
  "ko": dict(atlas_h="역량 지도", atlas_p="직접 만들고 실측한 엔진 네 계열입니다. 전부 에이전트가 채팅에서 도구로 부릅니다.", papers="실험 기록 51편 보기"),
  "en": dict(atlas_h="Capability atlas", atlas_p="Four engine families we built and measured ourselves. Every one is a tool an agent calls from chat.", papers="See 51 experiment notes"),
}
def hold_svg():
    """Three worldlines converge on the lit dot of the hero; geometry comes from measured coordinates.
    Film hero (site/assets/film/hero.json present): the video fills a 16:9 stage, viewBox 600x338, and the
    dot is the raised hand in the film's opening frames. Character hero (fallback): .hero-fig sits at
    left 30% / top 20% / width 70% of a 3:2 stage whose viewBox is 600x400."""
    film = Path("site/assets/film/hero.json")
    if film.exists():
        tx, ty = json.load(open(film))["tip"]
        vh = 338
        cx, cy = round(tx * 600, 1), round(ty * vh, 1)
    else:
        tx, ty = json.load(open("site/assets/character/tips.json"))["p2-hold-graphpaper-nodot"]
        vh = 400
        cx, cy = round((0.30 + 0.70 * tx) * 600, 1), round((0.20 + 0.70 * ty) * 400, 1)
    return (f'<svg class="hold" viewBox="0 0 600 {vh}" preserveAspectRatio="xMidYMid meet">'
            f'<g class="hold-lines"><path d="M-20 {cy-140} L{cx} {cy}"/><path d="M-20 {cy} L{cx} {cy}"/>'
            f'<path d="M-20 {cy+140} L{cx} {cy}"/><path class="hold-out" d="M{cx} {cy} L620 {round(cy-70,1)}"/></g>'
            f'<path class="hold-arc" d="M{cx-40} {cy-40} A40 40 0 0 1 {cx+40} {cy-40}"/>'
            f'<circle class="hold-dot" cx="{cx}" cy="{cy}" r="7"/></svg>')


UT = {
  "ko": dict(h="Use Cases", p="말로 설명하는 대신 눌러 보시면 됩니다. 일곱 계열 {n}개 데모가 전부 브라우저에서 돌고, 에이전트는 이것들을 도구로 부릅니다.",
             more="데모 {n}개 전체 보기", field="현장에서 도는 것", field_p="데모가 제품이 된 사례입니다. 실측과 지금 상태를 적어 두었습니다.",
             page_h="눌러 보시면 됩니다", page_p="{n}개 데모 전부 브라우저에서 돕니다. 계열마다 문제와 접근을 먼저 적고, 그 아래에 실제로 눌러 볼 것을 두었습니다."),
  "en": dict(h="Use Cases", p="Instead of explaining, press. {n} demos across seven families run in the browser, and the agent calls them as tools.",
             more="See all {n} demos", field="Running in the field", field_p="Demos that became products, with measurements and current state.",
             page_h="Press, don't read", page_p="All {n} demos run in the browser. Each family states the problem and the approach first, then what to press."),
}

def plain(s):
    """status strings use " · " and "→" as facts shorthand; the home renders them as prose."""
    return re.sub(r"\s·\s", ", ", s.replace("→", " to " if s.isascii() else " 에서 "))

def demo_card(d, lang):
    ti = d["title"] if lang == "ko" else d.get("title_en", d["title"]); bl = d["blurb"] if lang == "ko" else d.get("blurb_en", d["blurb"])
    tech = d.get("tech", []) if lang == "ko" else d.get("tech_en", d.get("tech", []))
    chips = "".join(f"<span>{e(x)}</span>" for x in tech[:3])
    inner = f'<h4>{e(ti)}</h4><p>{e(bl)}</p><span class="chips">{chips}</span>'
    if d.get("url"):
        return f'<li class="demo"><a href="{e(d["url"])}" target="_blank" rel="noopener">{inner}</a></li>'
    note = d.get("note" if lang == "ko" else "note_en", "")
    return f'<li class="demo demo--closed"><div>{inner}<span class="note">{e(note)}</span></div></li>'

def render_usecases_home(lang, prefix):
    t = UT[lang]; n = len(DEMOS["demos"])
    fams = ""
    for f in DEMOS["families"]:
        ds = [d for d in DEMOS["demos"] if d["group"] == f["id"] and d.get("url")][:3]
        mini = "".join(f'<li><a href="{e(d["url"])}" target="_blank" rel="noopener">{e(d["title"] if lang=="ko" else d.get("title_en", d["title"]))}</a></li>' for d in ds)
        fams += (f'<li class="demo-fam"><h3><a href="{prefix}usecases/index.html#{f["id"]}">{e(f[lang]["name"])}</a></h3>'
                 f'<p>{e(f[lang]["blurb"])}</p><ul class="demo-mini">{mini}</ul></li>')
    field = "".join(f'<li><a href="{prefix}cases/{c["slug"]}/index.html"><h4>{e(c[lang]["title"])}</h4><p>{e(plain(c["status"][lang]))}</p></a></li>' for c in DATA["cases"])
    return (f'<section id="cases" class="cases" aria-labelledby="cases-h"><div class="section-head"><h2 id="cases-h">{t["h"]}</h2><p>{t["p"].format(n=n)}</p></div>'
            f'<ul class="demo-fams">{fams}</ul><p class="atlas-more"><a class="btn btn-line" href="{prefix}usecases/index.html">{t["more"].format(n=n)}</a></p>'
            f'<div class="field"><h3>{t["field"]}</h3><p>{t["field_p"]}</p><ul class="field-list">{field}</ul></div></section>')

def usecases_page(lang):
    t = T[lang]; u = UT[lang]; n = len(DEMOS["demos"])
    home = "../" if lang == "ko" else "../../"; assets = home + "assets/"
    site_home = home + ("index.html" if lang == "ko" else "en/index.html")
    other_page = (home + "en/usecases/index.html") if lang == "ko" else (home + "usecases/index.html")
    nav = "".join(f'<a href="{site_home}{ANCH[x]}">{x}</a>' for x in t["nav"])
    secs = ""
    for f in DEMOS["families"]:
        ds = [d for d in DEMOS["demos"] if d["group"] == f["id"]]
        secs += (f'<section class="demo-sec" id="{f["id"]}"><div class="section-head"><h2>{e(f[lang]["name"])} <span class="count">{len(ds)}</span></h2><p>{e(f[lang]["blurb"])}</p></div>'
                 f'<ul class="demo-grid">' + "".join(demo_card(d, lang) for d in ds) + '</ul></section>')
    jump = "".join(f'<a href="#{f["id"]}">{e(f[lang]["name"])}</a>' for f in DEMOS["families"])
    ol = 'en' if lang == 'ko' else 'ko'
    return f"""<!doctype html>
<html lang="{lang}" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{u["h"]} — Fermoa</title>
<meta name="description" content="{e(u['page_p'].format(n=n))}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300..800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="{assets}style.css">
<link rel="icon" href="{assets}mark.svg" type="image/svg+xml">
<link rel="alternate" hreflang="{ol}" href="{other_page}">
</head>
<body class="sub">
<a class="skip" href="#main">{t['skip']}</a>
<header class="top">
  <a class="brand" href="{site_home}" aria-label="Fermoa"><svg class="mark" viewBox="0 0 48 48" aria-hidden="true"><use href="#mark"/></svg><span class="wordmark">Fermoa</span></a>
  <nav class="nav" aria-label="Main">{nav}</nav>
  <div class="top-tools">
    <button class="theme" type="button" data-theme-toggle data-label-light="{t['theme_light']}" data-label-dark="{t['theme_dark']}">{t['theme']}</button>
    <span class="lang"><a href="{other_page}" hreflang="{ol}">{t['other']}</a></span>
    <a class="btn btn-ink" href="{site_home}#contact">{t['contact']}</a>
  </div>
</header>
<main id="main">
<section class="page-hero">
  <p class="crumb"><a href="{site_home}#cases">{u['h']}</a></p>
  <div class="page-hero-grid"><div><h1>{u['page_h']}</h1><p class="lede">{e(u['page_p'].format(n=n))}</p></div>
  <nav class="jump" aria-label="families">{jump}</nav></div>
</section>
{secs}
<section class="page-cta">
  <h2>{t['cta_h']}</h2>
  <p>{t['cta_p']}</p>
  <a class="btn btn-ink" href="{site_home}#contact">{t['contact']}</a>
</section>
</main>
<footer class="foot foot-sub">
  <div class="foot-base"><p class="biz">{t['biz']}</p><p class="copy">© <span data-year>2026</span> Fermoa. All rights reserved.</p></div>
</footer>
{MARK}
<script src="{assets}main.js" defer></script>
</body>
</html>
"""


def render_home(lang):
    path = ROOT / ("index.html" if lang == "ko" else "en/index.html")
    s = path.read_text(encoding="utf-8"); t = HOME_T[lang]; L = DATA["links"]
    def atlas_item(a):
        inner = f'<h3>{e(a[lang]["name"])}</h3><p>{e(a[lang]["blurb"])}</p>'
        return f'<li><a href="{a["href"]}">{inner}</a></li>' if a.get("href") else f'<li><div class="atlas-card">{inner}</div></li>'
    items = "".join(atlas_item(a) for a in DATA["atlas"])
    atlas = f'<section id="atlas" class="atlas" aria-labelledby="atlas-h"><div class="section-head"><h2 id="atlas-h">{t["atlas_h"]}</h2><p>{t["atlas_p"]}</p></div><ul class="atlas-grid">{items}</ul></section>'
    s = re.sub(r"<!-- hold:start -->.*?<!-- hold:end -->", "<!-- hold:start -->" + hold_svg() + "<!-- hold:end -->", s, flags=re.S)
    s = re.sub(r"<!-- usecases:start -->.*?<!-- usecases:end -->", "<!-- usecases:start -->" + render_usecases_home(lang, "" if lang == "ko" else "../") + "<!-- usecases:end -->", s, flags=re.S)
    s = re.sub(r"<!-- atlas:start -->.*?<!-- atlas:end -->", "<!-- atlas:start -->" + atlas + "<!-- atlas:end -->", s, flags=re.S)
    cards = "".join(f'<article><div class="xbox" data-label="IMG 3:2" style="--ar:3/2"></div><h3><a href="{"" if lang=="ko" else ""}cases/{c["slug"]}/index.html">{e(c[lang]["title"])}</a></h3><p>{e(c[lang]["lede"])}</p></article>' for c in DATA["cases"])
    s = re.sub(r"<!-- cases:start -->.*?<!-- cases:end -->", "<!-- cases:start -->" + cards + "<!-- cases:end -->", s, flags=re.S)
    s = re.sub(r"<!-- papers:start -->.*?<!-- papers:end -->", f'<!-- papers:start --><p class="atlas-more"><a class="btn btn-line" href="{L["company_papers"]}">{t["papers"]}</a></p><!-- papers:end -->', s, flags=re.S)
    path.write_text(s, encoding="utf-8")

def main():
    n = 0
    for kind in ("agentos", "cases"):
        for item in DATA[kind]:
            for lang in ("ko", "en"):
                out = ROOT / (f"{kind}/{item['slug']}" if lang == "ko" else f"en/{kind}/{item['slug']}") / "index.html"
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(page(kind, item, lang), encoding="utf-8"); n += 1
    for lang in ("ko","en"): render_home(lang)
    for lang in ("ko", "en"):
        p = ROOT / ("usecases" if lang == "ko" else "en/usecases") / "index.html"; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(usecases_page(lang), encoding="utf-8")
    print(f"wrote {n} pages + 2 homes")

if __name__ == "__main__":
    main()
