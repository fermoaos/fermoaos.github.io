#!/usr/bin/env python3
"""Fermoa subpage generator. Content lives in site/content/pages.json; this file owns the format.
Usage: python3 build_pages.py   (idempotent; writes site/{agentos,cases}/<slug>/index.html and site/en/...)
"""
import json, html, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "site"
DATA = json.loads((ROOT / "content" / "pages.json").read_text(encoding="utf-8"))
DEMOS = json.loads((ROOT / "content" / "demos.json").read_text(encoding="utf-8"))
PROGRAM = json.loads((ROOT / "content" / "program.json").read_text(encoding="utf-8"))
LEGAL = json.loads((ROOT / "content" / "legal.json").read_text(encoding="utf-8"))
DOCK = json.loads((ROOT / "content" / "dock.json").read_text(encoding="utf-8"))
DEMO_IDX = json.loads((ROOT / "assets" / "demo" / "index.json").read_text(encoding="utf-8"))

T = {
  "ko": dict(lang="ko", home="../../", skip="본문으로 건너뛰기", nav=["AgentOS","Agentic Ops","Use Cases","AI Fabric","Insights","Company"],
             theme="칠판", theme_light="칠판", theme_dark="그래프지", contact="문의하기", other="ENG",
             kinds={"agentos":"AgentOS","cases":"Use Cases"}, facts="실측과 사실", impl="구현", status="지금 상태",
             related={"agentos":"다른 계층","cases":"다른 사례"}, cta_h="이 계층을 붙잡아 보시겠어요?", cta_p="실험에서 실행까지 같이 갑니다.",
             biz="페르모아 (Fermoa), 서울", back="목록으로"),
  "en": dict(lang="en", home="../../../", skip="Skip to content", nav=["AgentOS","Agentic Ops","Use Cases","AI Fabric","Insights","Company"],
             theme="Blackboard", theme_light="Blackboard", theme_dark="Graph paper", contact="Contact", other="KOR",
             kinds={"agentos":"AgentOS","cases":"Use Cases"}, facts="Measured and factual", impl="Implementation", status="Current state",
             related={"agentos":"Other layers","cases":"Other cases"}, cta_h="Want to hold this layer?", cta_p="From experiment to execution, together.",
             biz="Fermoa, Seoul, Korea", back="Back to the list"),
}
ANCH = {"AgentOS":"#agentos","Agentic Ops":"#ops","Use Cases":"#cases","AI Fabric":"#fabric","Insights":"#insights","Company":"#company"}
MARK = '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="mark" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M4 12 L24 30 M4 30 L24 30 M4 44 L24 30 M24 30 L46 22"/><path d="M15 20 A9 9 0 0 1 33 20"/><circle cx="24" cy="30" r="4.2" fill="var(--hold)"/></symbol></svg>'

def e(s): return html.escape(s, quote=True)

# ── 공유·검색 메타 (코드가 소유한다 — 손으로 head 를 고치지 마라) ─────────────
ORIGIN = "https://fermoaos.github.io"
OG_IMAGE = {"ko": ORIGIN + "/assets/og.png", "en": ORIGIN + "/assets/og-en.png"}
OG_ALT = {
  "ko": "페르모아 — 붙잡아, 모은다. 그래프지 위 지휘자가 지휘봉을 정점에서 멈춘 순간",
  "en": "Fermoa — Hold, and gather. A conductor on graph paper, baton stilled at its peak",
}
LOCALE = {"ko": "ko_KR", "en": "en_US"}

def _abs(rel):
    """site-root-relative dir path -> absolute URL (trailing slash; '' = home)."""
    return ORIGIN + "/" + rel

def head_meta(*, lang, rel_ko, rel_en, title, desc, jsonld=None):
    """canonical · Open Graph · Twitter · absolute hreflang(self/other/x-default) · JSON-LD."""
    rel = rel_ko if lang == "ko" else rel_en
    url, other = _abs(rel), LOCALE["en" if lang == "ko" else "ko"]
    ld = ""
    if jsonld:
        ld = ('\n<script type="application/ld+json">'
              + json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))
              + "</script>")
    return f"""<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="ko" href="{_abs(rel_ko)}">
<link rel="alternate" hreflang="en" href="{_abs(rel_en)}">
<link rel="alternate" hreflang="x-default" href="{_abs(rel_ko)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Fermoa">
<meta property="og:locale" content="{LOCALE[lang]}">
<meta property="og:locale:alternate" content="{other}">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{OG_IMAGE[lang]}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(OG_ALT[lang])}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{OG_IMAGE[lang]}">
<meta name="theme-color" content="#f7f6f1" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#14161a" media="(prefers-color-scheme: dark)">{ld}"""

def org_jsonld(lang, desc):
    name = "페르모아" if lang == "ko" else "Fermoa"
    return {"@context": "https://schema.org", "@type": "Organization", "name": name,
            "alternateName": "Fermoa" if lang == "ko" else "페르모아",
            "url": _abs("" if lang == "ko" else "en/"),
            "logo": ORIGIN + "/assets/mark.svg", "image": OG_IMAGE[lang],
            "slogan": "붙잡아, 모은다." if lang == "ko" else "Hold, and gather.",
            "description": desc,
            "address": {"@type": "PostalAddress", "addressLocality": "Seoul", "addressCountry": "KR"},
            "email": "hyojunguy@gmail.com", "telephone": "+821094820309",
            "contactPoint": {"@type": "ContactPoint", "contactType": "sales",
                             "name": "Hyojung Han", "email": "hyojunguy@gmail.com", "telephone": "+821094820309",
                             "availableLanguage": ["ko", "en"]}}

def crumb_jsonld(lang, trail):
    """trail: [(name, site-root-relative dir), ...] — home 부터 현재 페이지까지."""
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": _abs(r)}
                                for i, (n, r) in enumerate(trail)]}


POSE_ALT = {
  "p1-ready": {"ko": "양손을 들어 올린 준비 자세의 지휘자 — 계획", "en": "Both hands raised in the preparatory position — plan"},
  "p2-hold": {"ko": "지휘봉을 정점에서 멈춘 지휘자, 왼손은 멈춤 신호 — 승인 대기", "en": "The baton held still at its peak, left hand raised in a stop — waiting for approval"},
  "p3-downbeat": {"ko": "점으로 그린 지휘자가 다운비트를 내리는 순간, 오케스트라 한 구역이 켜진다 — 실행", "en": "A conductor drawn in dots on the downbeat; one section of the orchestra lights up — run"},
  "p4-lower": {"ko": "왼손 손바닥을 아래로 내리는 지휘자 — 롤백과 감속", "en": "Left palm slowly pressing downward — rollback and slowing"},
  "p5-cutoff": {"ko": "손을 안쪽으로 닫는 컷오프, 점이 흩어지기 시작한다 — 종료", "en": "Hands closing inward in a cutoff as the dots begin to scatter — done"},
}
AGENTOS_POSE = {"runtime": "p3-downbeat", "contract": "p2-hold", "pipeline": "p1-ready", "gateway": "p4-lower", "edge": "p5-cutoff"}

def char_fig(pose, css_class, lang, assets):
    alt = e(POSE_ALT[pose][lang])
    base = f"{assets}character/{pose}-graphpaper"
    def img(variant, cls):
        return (f'<img class="mod-img {cls}" src="{base}-{variant}-768.webp" '
                f'srcset="{base}-{variant}-768.webp 768w, {base}-{variant}-1536.webp 1536w" '
                f'sizes="(max-width:768px) 100vw, 34rem" width="1536" height="1024" '
                f'loading="lazy" decoding="async" alt="{alt}">')
    return f'<figure class="mod-fig {css_class}">{img("ink", "img-light")}{img("chalk", "img-dark")}</figure>'


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
    rel_ko, rel_en = f"{kind}/{item['slug']}/", f"en/{kind}/{item['slug']}/"
    anchor = "#agentos" if kind == "agentos" else "#cases"
    base = "" if lang == "ko" else "en/"
    meta = head_meta(lang=lang, rel_ko=rel_ko, rel_en=rel_en, title=f"{title} — Fermoa", desc=c["lede"],
                     jsonld=crumb_jsonld(lang, [("Fermoa", base), (kind_label, base + anchor),
                                                (title, rel_ko if lang == "ko" else rel_en)]))
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
{meta}
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
    {char_fig(AGENTOS_POSE.get(item["slug"], "p2-hold") if kind == "agentos" else "p3-downbeat", "mod-fig--hero", lang, assets)}
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
    inner = f'<h3>{e(ti)}</h3><p>{e(bl)}</p><span class="chips">{chips}</span>'
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
    base = "" if lang == "ko" else "en/"
    meta = head_meta(lang=lang, rel_ko="usecases/", rel_en="en/usecases/",
                     title=f'{u["h"]} — Fermoa', desc=u["page_p"].format(n=n),
                     jsonld=crumb_jsonld(lang, [("Fermoa", base), (u["h"], base + "usecases/")]))
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
{meta}
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
    title = html.unescape(re.search(r"<title>(.*?)</title>", s, re.S).group(1).strip())
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)">', s, re.S).group(1).strip())
    meta = head_meta(lang=lang, rel_ko="", rel_en="en/", title=title, desc=desc,
                     jsonld=org_jsonld(lang, desc))
    s = re.sub(r"<!-- meta:start -->.*?<!-- meta:end -->", "<!-- meta:start -->\n" + meta + "\n<!-- meta:end -->", s, flags=re.S)
    s = re.sub(r"<!-- hold:start -->.*?<!-- hold:end -->", "<!-- hold:start -->" + hold_svg() + "<!-- hold:end -->", s, flags=re.S)
    s = re.sub(r"<!-- usecases:start -->.*?<!-- usecases:end -->", "<!-- usecases:start -->" + render_usecases_home(lang, "" if lang == "ko" else "../") + "<!-- usecases:end -->", s, flags=re.S)
    s = re.sub(r"<!-- scn:start -->.*?<!-- scn:end -->", "<!-- scn:start -->" + dock_buttons(lang) + "<!-- scn:end -->", s, flags=re.S)
    s = re.sub(r"<!-- scnN:start -->.*?<!-- scnN:end -->", "<!-- scnN:start -->" + dock_count(lang) + "<!-- scnN:end -->", s, flags=re.S)
    s = re.sub(r"<!-- fabric:start -->.*?<!-- fabric:end -->", "<!-- fabric:start -->" + render_program_home(lang, "" if lang == "ko" else "../") + "<!-- fabric:end -->", s, flags=re.S)
    s = re.sub(r"<!-- atlas:start -->.*?<!-- atlas:end -->", "<!-- atlas:start -->" + atlas + "<!-- atlas:end -->", s, flags=re.S)
    cards = "".join(f'<article>{char_fig("p1-ready", "mod-fig--card", lang, "" if lang == "ko" else "../")}<h3><a href="{"" if lang=="ko" else ""}cases/{c["slug"]}/index.html">{e(c[lang]["title"])}</a></h3><p>{e(c[lang]["lede"])}</p></article>' for c in DATA["cases"])
    s = re.sub(r"<!-- cases:start -->.*?<!-- cases:end -->", "<!-- cases:start -->" + cards + "<!-- cases:end -->", s, flags=re.S)
    s = re.sub(r"<!-- papers:start -->.*?<!-- papers:end -->", f'<!-- papers:start --><p class="atlas-more"><a class="btn btn-line" href="{L["company_papers"]}">{t["papers"]}</a></p><!-- papers:end -->', s, flags=re.S)
    path.write_text(s, encoding="utf-8")

def write_sitemap():
    """모든 페이지를 ko/en 쌍으로 — 링크는 canonical 과 같은 절대 경로다."""
    pairs = [("", "en/"), ("usecases/", "en/usecases/"), ("program/", "en/program/")]
    pairs += [(f"{d['slug']}/", f"en/{d['slug']}/") for d in LEGAL.values()]
    for kind in ("agentos", "cases"):
        for item in DATA[kind]:
            pairs.append((f"{kind}/{item['slug']}/", f"en/{kind}/{item['slug']}/"))
    rows = []
    for ko, en in pairs:
        for rel in (ko, en):
            alts = "".join(
                f'\n    <xhtml:link rel="alternate" hreflang="{lg}" href="{_abs(r)}"/>'
                for lg, r in (("ko", ko), ("en", en), ("x-default", ko)))
            rows.append(f"  <url>\n    <loc>{_abs(rel)}</loc>{alts}\n  </url>")
    body = "\n".join(rows)
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
        ' xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + body + "\n</urlset>\n",
        encoding="utf-8")


def four_oh_four():
    """GitHub Pages 는 없는 경로마다 /404.html 을 준다 — 어느 깊이에서 떠도 되게 절대 경로를 쓴다.
    지휘자의 컷오프(p5) 를 쓴다: 흩어진 것. 브랜드가 사과하지 않고 길만 내준다."""
    img = "/assets/character/p5-cutoff-graphpaper"
    alt = e(POSE_ALT["p5-cutoff"]["ko"])
    return f"""<!doctype html>
<html lang="ko" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>없는 페이지 — Fermoa</title>
<meta name="description" content="찾으시는 페이지가 없습니다.">
<meta name="robots" content="noindex">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300..800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="/assets/style.css">
<link rel="icon" href="/assets/mark.svg" type="image/svg+xml">
</head>
<body class="sub">
<a class="skip" href="#main">본문으로 건너뛰기</a>
<header class="top">
  <a class="brand" href="/" aria-label="Fermoa"><svg class="mark" viewBox="0 0 48 48" aria-hidden="true"><use href="#mark"/></svg><span class="wordmark">Fermoa</span></a>
  <nav class="nav" aria-label="Main">{"".join(f'<a href="/{ANCH[n]}">{n}</a>' for n in T["ko"]["nav"])}</nav>
  <div class="top-tools">
    <button class="theme" type="button" data-theme-toggle data-label-light="칠판" data-label-dark="그래프지">칠판</button>
    <span class="lang"><a href="/en/" hreflang="en">ENG</a></span>
    <a class="btn btn-ink" href="/#contact">문의하기</a>
  </div>
</header>
<main id="main">
<section class="page-hero">
  <p class="crumb">404</p>
  <div class="page-hero-grid">
    <div>
      <h1>흩어졌습니다</h1>
      <p class="lede">이 주소에는 아무것도 없습니다. 링크가 옮겨졌거나, 처음부터 없던 경로입니다. <span lang="en">This page does not exist.</span></p>
      <nav class="related" aria-label="다른 경로" style="margin-top:2.5rem">
        <h2>여기로 가시면 됩니다</h2>
        <ul><li><a href="/">홈</a></li><li><a href="/#agentos">AgentOS 다섯 계층</a></li><li><a href="/usecases/">Use Cases</a></li><li><a href="/#company">Company</a></li><li><a href="/en/" hreflang="en">English</a></li></ul>
      </nav>
    </div>
    <figure class="mod-fig mod-fig--hero"><img class="mod-img img-light" src="{img}-ink-768.webp" srcset="{img}-ink-768.webp 768w, {img}-ink-1536.webp 1536w" sizes="(max-width:768px) 100vw, 34rem" width="1536" height="1024" decoding="async" alt="{alt}"><img class="mod-img img-dark" src="{img}-chalk-768.webp" srcset="{img}-chalk-768.webp 768w, {img}-chalk-1536.webp 1536w" sizes="(max-width:768px) 100vw, 34rem" width="1536" height="1024" decoding="async" alt="{alt}"></figure>
  </div>
</section>
</main>
<footer class="foot foot-sub">
  <div class="foot-base"><p class="biz">{T["ko"]["biz"]}</p><p class="copy">© <span data-year>2026</span> Fermoa. All rights reserved.</p></div>
</footer>
{MARK}
<script src="/assets/main.js" defer></script>
</body>
</html>
"""


# ── AI Fabric 프로그램 (25개 항목) ────────────────────────────────────────────
PT = {
  "ko": dict(back="프로그램 전체 보기", crumb="AI Fabric", jump="번들로 이동",
             home_more="25개 항목 전부 보기",
             cta_h="어느 항목부터 보시겠어요?", cta_p="여섯 개는 이미 게이트가 돌고 있습니다. 나머지도 같은 방식으로 짓습니다."),
  "en": dict(back="See the whole program", crumb="AI Fabric", jump="Jump to a bundle",
             home_more="See all twenty-five",
             cta_h="Which piece should we start with?", cta_p="Six already run behind a gate. The rest get built the same way."),
}

def program_counts():
    n = len(PROGRAM["items"])
    built = sum(1 for i in PROGRAM["items"] if i["state"] == "built")
    return n, built, n - built


def program_item(it, lang):
    """한 항목. 상태는 코드가 붙인다 — 근거 문장이 있는 항목만 built 로 렌더된다."""
    c, m = it[lang], PROGRAM["meta"][lang]
    label = m["built_label"] if it["state"] == "built" else m["scaffold_label"]
    ev = f'<p class="fab-ev">{e(c["evidence"])}</p>' if it["state"] == "built" and c.get("evidence") else ""
    return (f'<li class="fab-item fab-{it["state"]}">'
            f'<p class="fab-no"><span class="fab-num">{it["no"]:02d}</span>'
            f'<span class="fab-state">{e(label)}</span></p>'
            f'<h3>{e(c["title"])}</h3><p class="fab-lede">{e(c["lede"])}</p>'
            f'<p class="fab-note">{e(c["note"])}</p>{ev}</li>')


def program_page(lang):
    t, m, pt = T[lang], PROGRAM["meta"][lang], PT[lang]
    n, built, scaffold = program_counts()
    home = "../" if lang == "ko" else "../../"
    assets = home + "assets/"
    site_home = home + ("index.html" if lang == "ko" else "en/index.html")
    other_page = (home + "en/program/index.html") if lang == "ko" else (home + "program/index.html")
    nav = "".join(f'<a href="{site_home}{ANCH[x]}">{x}</a>' for x in t["nav"])
    secs = ""
    for b in PROGRAM["bundles"]:
        items = [i for i in PROGRAM["items"] if i["bundle"] == b["id"]]
        secs += (f'<section class="fab-sec" id="{b["id"]}"><div class="section-head">'
                 f'<h2><span class="fab-letter">{b["letter"]}</span> {e(b[lang]["name"])} '
                 f'<span class="count">{len(items)}</span></h2><p>{e(b[lang]["blurb"])}</p></div>'
                 f'<ul class="fab-grid">' + "".join(program_item(i, lang) for i in items) + "</ul></section>")
    jump = "".join(f'<a href="#{b["id"]}">{b["letter"]}. {e(b[lang]["name"])}</a>' for b in PROGRAM["bundles"])
    meta = head_meta(lang=lang, rel_ko="program/", rel_en="en/program/",
                     title=f'{m["name"]} — {m["h"]} — Fermoa', desc=m["lede"],
                     jsonld=crumb_jsonld(lang, [("Fermoa", "" if lang == "ko" else "en/"),
                                                (m["name"], ("" if lang == "ko" else "en/") + "program/")]))
    return f"""<!doctype html>
<html lang="{lang}" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(m["name"])} — {e(m["h"])} — Fermoa</title>
<meta name="description" content="{e(m["lede"])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300..800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="{assets}style.css">
<link rel="icon" href="{assets}mark.svg" type="image/svg+xml">
{meta}
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
  <p class="crumb">{e(pt["crumb"])}</p>
  <div class="page-hero-grid">
    <div>
      <h1>{e(m["h"])}</h1>
      <p class="lede">{e(m["lede"])}</p>
      <p class="fab-honest">{e(m["honest"])}</p>
    </div>
    {char_fig("p1-ready", "mod-fig--hero", lang, assets)}
  </div>
</section>
<nav class="jump" aria-label="{e(pt['jump'])}">{jump}</nav>
{secs}
<section class="page-cta">
  <h2>{e(pt['cta_h'])}</h2>
  <p>{e(pt['cta_p'])}</p>
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


def render_program_home(lang, prefix):
    """홈 섹션 — 번들 7개와 정직한 집계만. 25개 전체는 서브페이지가 소유한다."""
    m, pt = PROGRAM["meta"][lang], PT[lang]
    n, built, scaffold = program_counts()
    cards = ""
    for b in PROGRAM["bundles"]:
        items = [i for i in PROGRAM["items"] if i["bundle"] == b["id"]]
        nb = sum(1 for i in items if i["state"] == "built")
        tally = (f'<span class="fab-chip">{nb} {e(m["built_label"])}</span>' if nb else "")
        cards += (f'<li><a href="{prefix}program/index.html#{b["id"]}">'
                  f'<h3><span class="fab-letter">{b["letter"]}</span> {e(b[lang]["name"])}'
                  f'<span class="count">{len(items)}</span></h3>'
                  f'<p>{e(b[lang]["blurb"])}</p>{tally}</a></li>')
    return (f'<section id="fabric" class="fabric" aria-labelledby="fabric-h">'
            f'<div class="section-head"><h2 id="fabric-h">{e(m["name"])}</h2>'
            f'<p>{e(m["lede"])}</p></div>'
            f'<p class="fab-tally"><b>{built}</b>{e(m["built_tally"])}, <b>{scaffold}</b>{e(m["scaffold_tally"])}</p>'
            f'<ul class="fab-fams">{cards}</ul>'
            f'<p class="atlas-more"><a class="btn btn-line" href="{prefix}program/index.html">{e(pt["home_more"])}</a></p>'
            f'</section>')


# ── 법적 고지 (개인정보 처리방침) ────────────────────────────────────────────
CODE = re.compile(r"`([^`]+)`")
CODE_SPAN = r"<code>\g<1></code>"

def legal_page(key, lang):
    """산문 한 장. 문장은 콘텐츠가, 마크업은 여기가 소유한다."""
    d = LEGAL[key]; c = d[lang]; t = T[lang]
    home = "../" if lang == "ko" else "../../"
    assets = home + "assets/"
    site_home = home + ("index.html" if lang == "ko" else "en/index.html")
    other_page = (home + f"en/{d['slug']}/index.html") if lang == "ko" else (home + f"{d['slug']}/index.html")
    nav = "".join(f'<a href="{site_home}{ANCH[x]}">{x}</a>' for x in t["nav"])
    body = ""
    for sec in c["sections"]:
        paras = "".join("<p>" + CODE.sub(CODE_SPAN, e(x)) + "</p>" for x in sec["p"])
        body += f"<h2>{e(sec['h'])}</h2>{paras}"
    rel_ko, rel_en = f"{d['slug']}/", f"en/{d['slug']}/"
    meta = head_meta(lang=lang, rel_ko=rel_ko, rel_en=rel_en,
                     title=f"{c['title']} — Fermoa", desc=c["lede"],
                     jsonld=crumb_jsonld(lang, [("Fermoa", "" if lang == "ko" else "en/"),
                                                (c["title"], rel_ko if lang == "ko" else rel_en)]))
    return f"""<!doctype html>
<html lang="{lang}" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(c['title'])} — Fermoa</title>
<meta name="description" content="{e(c['lede'])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,300..800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="{assets}style.css">
<link rel="icon" href="{assets}mark.svg" type="image/svg+xml">
{meta}
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
<section class="page-hero legal-hero">
  <p class="crumb">{e(c['updated_label'])} {d['updated']}</p>
  <h1>{e(c['title'])}</h1>
  <p class="lede">{e(c['lede'])}</p>
</section>
<section class="page-body legal-body">
  <div class="prose">{body}</div>
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


# ── 재생 도크 시나리오 버튼 ──────────────────────────────────────────────────
# 부제(위임·카드·승인 수)는 손으로 쓰지 않고 **기록 자체에서 센다** — 녹화를 다시 하면 따라 움직인다.
DOCK_T = {"ko": dict(delegation="위임 {n}건", card="카드 {n}장", approval="승인 {n}건",
                     count=["", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉"]),
          "en": dict(delegation="{n} delegation", card="{n} cards", approval="{n} approval",
                     count=["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"])}

def _demo_counts(slug):
    f = ROOT / "assets" / "demo" / f"{slug}.json"
    d = json.loads(f.read_text(encoding="utf-8"))
    evs = [e for seg in d["segments"] for e in seg.get("events", [])]
    c = {}
    for e in evs:
        c[e["event"]] = c.get(e["event"], 0) + 1
    return c

def dock_buttons(lang):
    t = DOCK_T[lang]
    out = ""
    for i, sc in enumerate(DEMO_IDX["scenarios"]):
        slug = sc["slug"]
        c = _demo_counts(slug)
        bits = []
        if c.get("agent_spawned"):
            bits.append(t["delegation"].format(n=c["agent_spawned"]))
        if c.get("approval_request"):
            bits.append(t["approval"].format(n=c["approval_request"]))
        if c.get("gen_ui"):
            bits.append(t["card"].format(n=c["gen_ui"]))
        title = DOCK[slug][lang]
        out += (f'<li><button class="scn" type="button" data-scn="{slug}" '
                f'aria-current="{"true" if i == 0 else "false"}">'
                f'<b>{e(title)}</b><span>{e(", ".join(bits))}</span></button></li>')
    return out

def dock_count(lang):
    n = len(DEMO_IDX["scenarios"])
    words = DOCK_T[lang]["count"]
    if not words or n >= len(words):
        return str(n)
    return f"{words[n]} 가지" if lang == "ko" else words[n]


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
        q = ROOT / ("program" if lang == "ko" else "en/program") / "index.html"; q.parent.mkdir(parents=True, exist_ok=True); q.write_text(program_page(lang), encoding="utf-8")
        for key, d in LEGAL.items():
            r = ROOT / (d["slug"] if lang == "ko" else f"en/{d['slug']}") / "index.html"
            r.parent.mkdir(parents=True, exist_ok=True); r.write_text(legal_page(key, lang), encoding="utf-8")
    (ROOT / "404.html").write_text(four_oh_four(), encoding="utf-8")
    write_sitemap()
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {ORIGIN}/sitemap.xml\n", encoding="utf-8")
    print(f"wrote {n} pages + 2 homes + 404.html + sitemap.xml + robots.txt")

if __name__ == "__main__":
    main()
