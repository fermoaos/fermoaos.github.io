# Fermoa (페르모아) — 브랜드 · 홈페이지 스펙 v1 (2026-09-03)

상태: 설계 제시. 사용자 승인 대기. 승인 후 `marketing/fermoa/site/` 구현.

## 1. 브랜드 코어

| 항목 | 정본 |
|---|---|
| 이름 | **Fermoa** · 국문 **페르모아** (애칭 "페르") |
| 어원 | it. *ferma*(머문다·붙잡는다) + ko. 모아(모으다) |
| 한 줄 명제 | **일은 완료 상태가 아니라 사고하는 순간에 있다.** |
| 태그라인 KR | **붙잡아, 모은다.** |
| 태그라인 EN | **Hold the thought. Gather the work.** |
| 카테고리 문장 | 기업의 실제 업무를 에이전트가 사고하고 실행하는 운영체계, AgentOS |
| 뿌리 | 파인만 — "자기 자신을 속이지 않는 것이 첫 원칙" / "만들 수 없는 것은 이해하지 못한 것" |

매니페스토(3문장, 홈 2번 섹션에 그대로):
1. 에이전트가 "완료했다"고 말하는 것을 믿지 않는다. 지금 사고하고 검증하는 상태만 진짜다.
2. 일은 끝나는 것이 아니라 흘러간다. 우리는 그 흐름이 한 점에 모이는 순간을 붙잡는다.
3. 그 점에서 사람이 이해하고, 에이전트가 실행한다. 그것이 페르모아다.

## 2. 아이덴티티 시스템 (마스코트 없음 — 기호가 캐릭터)

- **마크**: 늘임표 𝄐 재해석 — 점(punctum temporis) + 위의 호(붙잡음). 점으로 얇은 선 셋이
  수렴한다(파인만 꼭짓점). 단색. 최소 크기 16px 에서는 점+호만.
- **워드마크**: `Fermoa` 소문자 시작 아님 — 대문자 F, 나머지 소문자. 'o' 위에 마크의 호를 얹는
  변형(로고타입 전용). 국문 `페르모아`는 Pretendard Bold 단독.
- **모션은 하나(“hold”)**: 선 3개 수렴 → 호가 왼→오로 그려짐(0.6s) → 점이 강조색으로 밝아짐 →
  선이 계속 흘러 나감. 히어로 1회 + 로딩 인디케이터. 그 외 모션 금지.
- **색** (토큰, hex 하드코딩 금지 — CSS 변수만):
  - `--paper #F5F2EA` 바탕 / `--ink #15130F` 글 / `--hold #D9481F`(붙잡는 순간 — 유일한 강조)
  - `--line #8B8578` 다이어그램 선 / `--grid rgba(21,19,15,.07)` 모눈 / `--muted #6B665C`
  - 다크: `--paper #0F0E0C` `--ink #F1EDE4` `--grid rgba(241,237,228,.06)`, `--hold` 동일
- **서체**: 표시 = Fraunces(Google Fonts, 옵티컬 사이즈) · 본문 KR/EN = Pretendard(jsdelivr) ·
  숫자·다이어그램 라벨 = JetBrains Mono. 최대 3패밀리, 그 이상 금지.
- **레이아웃 원칙**: 편집·과학 노트 톤. 12컬럼, 큰 스케일 대비(히어로 clamp 3–8rem), 배경에
  아주 옅은 모눈. 카드 그리드 균일 배치 금지 — 섹션마다 리듬을 바꾼다(anti-template).
- **금지**: 로봇·헬멧·얼굴·의인화, 그라디언트 블롭, 스톡 3D, "완료/자동화/혁신" 류 상투어.
- **보이스**: 현재형·단정. "~하고 있다" 허용, "~했다/완료" 는 검증 문맥에서만.

## 3. 홈페이지 IA (enhans.ai/kr 골격 1:1 + 우리 배선)

파일: `marketing/fermoa/site/index.html`(KR) — EN 은 v2.
이미지·영상은 전부 **X 박스**(점선 사각 + 대각선 X + `IMG 16:9` 같은 라벨).

| # | 섹션 | 내용 | 배선 |
|---|---|---|---|
| 0 | Nav | AgentOS · Agentic Ops · Use Cases · Insights · Company · [Contact] · KOR/ENG | — |
| 1 | Hero | 헤드 "붙잡아, 모은다." / 서브 = 카테고리 문장 / CTA Contact / **X 박스(VIDEO 16:9)** + 뒤에 hold 모션 | — |
| 2 | Manifesto | 매니페스토 3문장, 큰 타이포, 모눈 위 | — |
| 3 | AgentOS 모듈 5 | Agent Runtime · Contract Layer · Pipeline · Model Gateway · Edge Agent — 각 X 박스(IMG 4:3) + 2문장 | companyos · media-ops(IR/Metric Contract) · companyos rulepack+media-ops 증분검증 · token-factory-gateway · ondevice-slm |
| 4 | Agentic Operations | Company Ops · Media · Commerce · Growth · Discovery — 5열, 각 1문장 | companyos · media-ops · commerce-brain · growth-commerce-os · ai-discovery-os |
| 5 | Use Cases 6 | 밀도 베이커리 D2C · 카페24 머천트 · 퍼포먼스 대행사 · 급여마감/4대보험 · AI 가시성 · 프라이버시 광고(DIPS) — 각 X 박스(IMG 3:2) + 결과 문장 1 | 각 README 사례 |
| 6 | Insights 3 | X 박스(IMG 16:9) 카드 3 + 제목 플레이스홀더 | 추후 블로그 |
| 7 | CTA + 문의 3단계 | "이제 에이전트에게 실제 업무를" / 3-step 폼(이름·소속·용건, 전송은 mailto) | — |
| 8 | Footer | 4열 링크 + 사업자정보 플레이스홀더 + 저작권 | — |

제외: Paxis · Metis · Maxis · praxis (문구·로고·링크 전부). token-factory-gateway 설명에서 Metis/Signum 문구 제거.

## 4. 기술

- 정적 3파일: `site/index.html` · `site/assets/style.css` · `site/assets/main.js` + `site/assets/mark.svg`. 빌드 없음.
- 시맨틱 HTML(header/nav/main/section/footer), 토큰은 `:root` CSS 변수 + `[data-theme=dark]`.
- 모션은 transform/opacity/stroke-dashoffset 만, `prefers-reduced-motion` 존중.
- 반응형 320/768/1024/1440. 가로 스크롤 0.
- 게이트(배포 전): `anti-slop-ui-guard` · `design-agent` audit · 렌더 스크린샷 3 브레이크포인트 육안 ·
  `verify_contract check`.
- 배포는 이번 범위 밖(로컬 `file://` 또는 `python -m http.server`).

## 5. 범위 밖 (v2+)

EN 페이지 · 서브 페이지(모듈/유즈케이스 상세) · 실제 이미지/영상 · KIPRIS 조회 결과 반영 · 도메인 연결.

## 6. 정정 (구현 직전, frontend-design 리뷰)

§2 의 팔레트(크림 종이 + 세리프 표시체 + 주홍 강조)는 생성형 디자인의 최빈 상투로 판정 → 주제에서 다시 끌어옴.
- **라이트 = 그래프지**: `--paper #F7F8F6` · `--grid #D3DAD6`(초록빛 모눈) · `--ink #171A19` · **`--hold #F2E640`(형광펜 — 사람이 종이 위 생각을 "붙잡는" 도구)** · `--muted #5F6663`
- **다크 = 칠판**: `--paper #1B2321` · `--ink #ECE9DF`(분필) · `--grid rgba(236,233,223,.08)` · `--hold #F5EA6A`
- 서체 2패밀리: **Bricolage Grotesque**(EN 표시·라벨, opsz) + **Pretendard**(KR). 모노 제거.
- 히어로: 헤드라인 좌 + 우측 VIDEO X 박스로 선 셋이 **수렴**(X 박스 자체가 꼭짓점). 모션 "hold" 는 이 SVG 1회.
- 금지 추가: 대문자 아이브로우 라벨 · 링크 뒤 화살표 · 가운뎃점 메타 · 시퀀스 아닌 곳의 번호(01/02) — 3단계 폼만 예외.

## 7. 마케팅 캐릭터 (2026-09-03 추가)

캐릭터는 마스코트가 아니라 **지휘자 + 지휘봉 끝의 점 "페르"** 다. 정본은
`2026-09-03-fermoa-character-sheet.md` — 포즈 5(제어 동사 5)·상태 3·배경 2·금지 목록·히어로
장면 지시문을 소유한다. 이미지는 `marketing/fermoa/brand/character/` 에 있고 시트가 바뀌면
다시 뽑는다. 로봇·얼굴·네온은 브랜드 밖이다.
