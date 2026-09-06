#!/usr/bin/env python3
"""growth-commerce-os 의 실제 SSE 실행 기록을 재생용 JSON 으로 남긴다 (site/assets/demo/<slug>.json).

기록은 **실제 실행**이다 — 모델이 쓴 텍스트·툴 호출·카드·승인·후속 질문을 이벤트 단위로 시각 오프셋(ms)과 함께
담고, 재생기는 그 타이밍대로 다시 흘린다. 승인 대기(paused) 턴은 사람이 승인한 뒤의 continue 스트림을 같은
파일의 다음 `segment` 로 붙인다. PII 는 API 의 READ 마스킹 + 아래 정규식 이중 스크럽.
    GCOS=http://127.0.0.1:8787 python3 scripts/record_demo.py
"""
import json, os, re, sys, time, urllib.request, pathlib, uuid

BASE = os.environ.get("GCOS", "http://127.0.0.1:8787")
OUT = pathlib.Path(__file__).resolve().parents[1] / "site" / "assets" / "demo"
# PII 와 **가상 회사의 브랜드명**을 같은 자리에서 가린다. 브랜드는 소스(gcos)의 시드 회사 이름이라
# 모델 출력·툴 인자·카드 어디에나 나타난다 — 손으로 지우면 다음 녹화에서 되돌아온다.
SCRUB = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "***@***"),
    (re.compile(r"01[016789]-?\d{3,4}-?\d{4}"), "010-****-****"),
    (re.compile(r"밀도\s*베이커리\s*\(\s*MILDO\s*Bakery\s*\)"), "우리 베이커리"),
    (re.compile(r"밀도\s*베이커리\s*\(\s*가상 회사[^)]*\)"), "가상 D2C 베이커리(합성 데이터)"),
    (re.compile(r"MILDO\s*Bakery", re.I), "our bakery"),
    (re.compile(r"\bMILDO\b", re.I), "Our Bakery"),
    (re.compile(r"밀도\s*베이커리"), "우리 베이커리"),
    (re.compile(r"밀도\s*공구"), "공구"),
    (re.compile(r"밀도"), "우리"),
]
KEEP = {"turn_start", "thinking_delta", "thinking_end", "content_delta", "tool_use", "tool_result", "gen_ui",
        "approval_request", "approval_auto", "agent_spawned", "agent_progress", "agent_done", "model_fallback", "error", "done"}
SCENARIOS = [
    {"slug": "dormant", "title": "휴면 고객을 찾아 복귀 캠페인까지", "turns": ["최근 90일간 구매가 없는 휴면 고객을 뽑고 이탈 원인을 정리해줘"]},
    {"slug": "diagnose", "title": "매출 진단과 3개월 계획 (위임)", "turns": ["매출이 안 나오는 이유를 진단하고 앞으로 3개월 계획을 제안해줘."]},
    {"slug": "groupbuy", "title": "인플루언서 공구 시작 → 제안 DM 발송 (승인)", "turns": ["적합도 1위 인플루언서로 공구를 시작하고 제안 DM 초안을 만들어서 보내줘"], "approve": True},
    {"slug": "subscription", "title": "구독 전환 후보와 오퍼 설계", "turns": ["구독 전환 후보를 뽑고 첫 오퍼를 설계해줘"]},
    {"slug": "groupbuy-result", "title": "끝난 공구 성과 분석 → 후속 전환", "turns": ["최근에 끝난 공구의 성과를 분석하고 구매자를 재구매로 잇는 후속 캠페인을 설계해줘"]},
    {"slug": "b2b", "title": "재주문 임박 거래처와 견적 초안", "turns": ["재주문 시점이 다가온 B2B 거래처를 뽑고 상위 한 곳의 견적 초안을 만들어줘"]},
    {"slug": "curation", "title": "객단가를 올리는 세트 구성", "turns": ["객단가를 분석하고 함께 잘 팔리는 조합으로 세트를 제안해줘"]},
]

def scrub(s):
    if not isinstance(s, str): return s
    for rx, rep in SCRUB: s = rx.sub(rep, s)
    return s

def deep(o):
    if isinstance(o, dict): return {k: deep(v) for k, v in o.items()}
    if isinstance(o, list): return [deep(v) for v in o]
    return scrub(o)

def stream(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers={"content-type": "application/json"})
    ev, t0, out = None, time.time(), []
    with urllib.request.urlopen(req, timeout=600) as r:
        for line in r:
            s = line.decode().rstrip("\n")
            if s.startswith("event: "): ev = s[7:]
            elif s.startswith("data: ") and ev in KEEP:
                out.append({"t": int((time.time() - t0) * 1000), "event": ev, "data": deep(json.loads(s[6:]))})
    return out

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    only = {a for a in sys.argv[1:] if not a.startswith("-")}
    prev = {}
    idx_path = OUT / "index.json"
    if idx_path.exists():
        prev = {x["slug"]: x for x in json.loads(idx_path.read_text(encoding="utf-8"))["scenarios"]}
    index = []
    for sc in SCENARIOS:
        if only and sc["slug"] not in only:
            if sc["slug"] in prev: index.append(prev[sc["slug"]])
            continue
        sid = f"demo-{sc['slug']}-{uuid.uuid4().hex[:6]}"
        segments = []
        for msg in sc["turns"]:
            evs = stream("/v1/chat", {"session_id": sid, "message": msg})
            segments.append({"user": msg, "events": evs})
            done = next((e for e in evs if e["event"] == "done"), None)
            if done and done["data"].get("paused") and sc.get("approve"):
                ap = next(e for e in evs if e["event"] == "approval_request")["data"]
                req = urllib.request.Request(f"{BASE}/v1/approvals/{ap['approval_id']}", data=json.dumps({"decision": "approve", "scope": "once"}).encode(),
                                             headers={"content-type": "application/json", "x-gcos-authority": "4"})
                dec = json.loads(urllib.request.urlopen(req, timeout=60).read() or b"{}")
                segments.append({"user": None, "approval": {"approval_id": ap["approval_id"], "decision": "approve", "decided_by": dec.get("decided_by", "대표")},
                                 "events": stream("/v1/chat", {"session_id": sid, "message": ""})})
        rec = {"slug": sc["slug"], "title": sc["title"], "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "source": "growth-commerce-os · 가상 D2C 베이커리(합성 데이터)",
               "model": next((e["data"].get("run", {}).get("model") for s in segments for e in s["events"] if e["event"] == "done" and e["data"].get("run")), None),
               "segments": segments}
        (OUT / f"{sc['slug']}.json").write_text(json.dumps(rec, ensure_ascii=False))
        n = sum(len(s["events"]) for s in segments)
        index.append({"slug": sc["slug"], "title": sc["title"], "events": n, "segments": len(segments)})
        print(sc["slug"], "segments", len(segments), "events", n, "model", rec["model"])
    (OUT / "index.json").write_text(json.dumps({"recorded_at": time.strftime("%Y-%m-%d"), "scenarios": index}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
