# Fermoa (페르모아) — AgentOS 브랜드 · 마케팅 사이트

재개 절차 (어느 머신에서든):

```bash
python3 marketing/fermoa/build_pages.py            # content/pages.json → 서브페이지 22장 재생성 (멱등)
python3 scripts/skills/static_site_gate.py marketing/fermoa/site   # 넘침·토큰·hidden·크롬 게이트
open marketing/fermoa/site/index.html              # KO 홈 · en/index.html = EN
```

| 무엇 | 어디 |
|---|---|
| 브랜드 결정 원장 · 스펙 | `docs/2026-09-03-brand-ideation.md` · `docs/2026-09-03-fermoa-brand-and-site-spec.md` |
| 캐릭터 시트 · 이미지 | `docs/2026-09-03-fermoa-character-sheet.md` · `brand/character/` (prompts.jsonl 정본, chosen.json 채택) · 사이트용 투명 webp(ink/chalk 쌍)는 `site/assets/character/` — `build_character_assets.py` 산출 |
| 홈 (손으로 쓴 정본) | `site/index.html` · `site/en/index.html` |
| 서브페이지 콘텐츠 (KO/EN 데이터) | `site/content/pages.json` — 문장은 여기서만 고친다 |
| 서브페이지 포맷 | `build_pages.py` — 생성물(`site/agentos/*`, `site/cases/*`, `site/en/...`)은 손대지 않는다 |
| 토큰·스타일 | `site/assets/style.css` (`:root` / `[data-theme=dark]` 밖 hex 금지) |

⛔ 제외: Paxis · Metis · Maxis · praxis 문구 전부. 미디어는 X 박스 유지(사용자 지시).
보드 프로젝트 `agentos-brand`. 미완: KIPRIS 상표 조회 · 도메인 등록(사용자 수동) · 실제 미디어.

- 캐릭터 자산 재생성: `python3 marketing/fermoa/build_character_assets.py` → `build_pages.py`
- 히어로 필름 재생성: `python3 marketing/fermoa/build_film_assets.py` (brand/film/draft-v1-36s.mp4 → `site/assets/film/hero.mp4` 무음·faststart + 포스터 + `hero.json` 점 좌표/풀림 시각) → `build_pages.py` (SVG 세계선이 `hero.json` 의 점으로 수렴). 새 초안이 나오면 `SRC` 만 바꾼다.
- 히어로 = 필름(2026-09-03). 지휘자 스틸은 계층 5칸·Operations 에 남아 있다. 시나리오 원장 `docs/2026-09-03-hero-film-scenario.md` §12.
