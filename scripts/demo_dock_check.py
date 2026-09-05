#!/usr/bin/env python3
"""Replay chat dock check (deterministic). exit 0 PASS · 1 FAIL.

Drives the real page with Chrome and asserts the dock replays the real recordings:
tool chips, generated cards, follow-ups, the approval interrupt (including the
segment that only exists after a human approves), delegation, dark theme, and
no horizontal overflow at 375.

Chrome needs --allow-file-access-from-files because the recordings are loaded
by XHR from file://; on http (GitHub Pages) no flag is involved.
"""
import sys, json, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright, Error as PWError

ROOT = Path(__file__).resolve().parents[1]
KO = (ROOT / "site" / "index.html").resolve().as_uri()
SHOTS = Path(tempfile.gettempdir()) / "fermoa-demo-shots"
FAILS, NOTES = [], {}


def need(cond, msg):
    if not cond:
        FAILS.append(msg)
    return bool(cond)


def play(page, slug, timeout=15000):
    """Select a scenario at instant speed and wait for the replay to settle."""
    page.click('[data-speed="0"]')
    page.click(f'.scn[data-scn="{slug}"]')
    page.wait_for_function(
        """s => {const st=document.querySelector('[data-status]');
                 return st && ['끝','승인 기다리는 중'].includes(st.textContent.trim());}""",
        arg=slug, timeout=timeout)
    return page.text_content("[data-status]").strip()


def main() -> int:
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", args=["--allow-file-access-from-files"])
        page = browser.new_page(viewport={"width": 1440, "height": 950})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(KO)
        page.wait_for_selector("#demo .player", timeout=10000)

        scns = page.query_selector_all("#demo .scn")
        need(len(scns) == 4, f"scenario buttons: {len(scns)} (want 4)")
        NOTES["scenarios"] = len(scns)

        # 1) dormant: tools, cards, exactly three follow-ups
        st = play(page, "dormant")
        need(st == "끝", f"dormant did not finish (status {st!r})")
        tools = len(page.query_selector_all("#demo .tool-chip"))
        tables = len(page.query_selector_all("#demo .ui-card--table"))
        sugg = len(page.query_selector_all("#demo .sugg-chip"))
        ok_tools = len(page.query_selector_all('#demo .tool-chip[data-state="ok"]'))
        subs = len(page.query_selector_all("#demo .subagent"))
        need(tools >= 1, "dormant: no tool chip")
        need(tables >= 1, "dormant: no table card")
        need(sugg == 3, f"dormant: {sugg} follow-up chips (want exactly 3)")
        # 1b) chart card from the real recording: line + one point per label
        charts = page.query_selector_all("#demo .ui-card--chart")
        need(len(charts) >= 1, "dormant: no chart card (the recording has one)")
        pts = len(page.query_selector_all("#demo .ui-card--chart .chart .pt"))
        lines = len(page.query_selector_all("#demo .ui-card--chart .chart .lin"))
        need(lines >= 1 and pts >= 12, f"dormant: chart drew {lines} lines / {pts} points (want >=1 / >=12)")
        # 1c) tables past ROWCAP collapse to 8 rows and expand on click to every row
        more = page.query_selector('#demo .ui-card--table .more[aria-expanded="false"]')
        need(more is not None, "dormant: no expand button on a >8-row table")
        if more:
            card = more.evaluate_handle("b => b.closest('.ui-card')")
            vis = lambda: card.evaluate("c => Array.from(c.querySelectorAll('tbody tr')).filter(t => !t.hidden).length")
            total = int(more.get_attribute("data-rows"))
            before = vis(); more.click(); page.wait_for_timeout(100); after = vis()
            need(before == 8 and after == total, f"dormant: table expand {before} -> {after} (want 8 -> {total})")
            need(more.get_attribute("aria-expanded") == "true", "dormant: aria-expanded did not flip")
            more.click(); page.wait_for_timeout(100)
            need(vis() == 8, "dormant: collapse did not hide the extra rows")
            NOTES["table_expand"] = {"before": before, "after": after, "total": total}
        NOTES["chart"] = {"cards": len(charts), "points": pts, "lines": lines}
        NOTES["dormant"] = {"tool_chips": tools, "resolved": ok_tools, "tables": tables,
                            "cards": len(page.query_selector_all("#demo .ui-card")),
                            "subagents": subs, "followups": sugg,
                            "summary": (page.text_content("#demo .turn-sum") or "").strip()}

        # 2) groupbuy: the approval interrupt, then the post-approval segment
        st = play(page, "groupbuy")
        need(st == "승인 기다리는 중", f"groupbuy did not pause for approval (status {st!r})")
        need(page.query_selector("#demo .approval") is not None, "groupbuy: no approval card")
        badge = page.query_selector("#demo .approval .risk-badge")
        need(badge is not None, "groupbuy: no risk badge")
        risk = badge.get_attribute("data-risk") if badge else None
        need(risk == "external_send", f"groupbuy: risk badge is {risk!r}")
        prev = page.query_selector_all("#demo .approval-preview li")
        need(len(prev) >= 1, "groupbuy: approval preview empty")
        pending = page.query_selector('#demo .tool-chip[data-name="message.send"][data-state="run"]')
        need(pending is not None, "groupbuy: message.send should still be pending before approval")
        NOTES["groupbuy"] = {"risk": risk, "preview_lines": len(prev),
                             "badge": (badge.text_content() or "").strip() if badge else None}

        page.click("#demo .approval .is-go")
        page.wait_for_selector("#demo .approval-done", timeout=8000)
        page.wait_for_function(
            """() => document.querySelector('[data-status]').textContent.trim() === '끝'""",
            timeout=10000)
        sent = page.query_selector('#demo .tool-chip[data-name="message.send"][data-state="ok"]')
        need(sent is not None, "groupbuy: segment 2 did not render (message.send never resolved)")
        turns = len(page.query_selector_all("#demo .turn"))
        need(turns >= 2, f"groupbuy: {turns} turns after approval (want 2)")
        NOTES["groupbuy"].update({
            "frozen_badge": (page.text_content("#demo .approval-done b") or "").strip(),
            "turns_after_approve": turns,
            "message_send_resolved": sent is not None,
            "followups": len(page.query_selector_all("#demo .sugg-chip"))})

        # 3) diagnose: delegation renders a sub-agent card with steps
        st = play(page, "diagnose")
        need(st == "끝", f"diagnose did not finish (status {st!r})")
        sa = page.query_selector("#demo .subagent")
        need(sa is not None, "diagnose: no sub-agent card")
        steps = len(page.query_selector_all("#demo .subagent .sa-steps li"))
        need(steps >= 1, "diagnose: sub-agent card has no steps")
        NOTES["diagnose"] = {"subagents": len(page.query_selector_all("#demo .subagent")),
                             "steps": steps,
                             "plan_cards": len(page.query_selector_all("#demo .ui-card--plan")),
                             "sub_done": page.query_selector("#demo .sa-done") is not None}

        # 3b) a follow-up chip whose text is another recording plays it; the rest say so
        chips = page.query_selector_all("#demo .sugg-chip")
        playable = [c for c in chips if c.get_attribute("data-plays") == "1"]
        NOTES["diagnose"]["followups"] = len(chips)
        NOTES["diagnose"]["playable_followups"] = len(playable)
        if chips:
            dead = [c for c in chips if c.get_attribute("data-plays") != "1"]
            if need(dead, "diagnose: every follow-up claims a recording"):
                dead[0].click()
                page.wait_for_selector("#demo .sugg-note", timeout=4000)
                NOTES["diagnose"]["no_record_note"] = (page.text_content("#demo .sugg-note") or "").strip()[:40]

        st = play(page, "groupbuy")
        page.click("#demo .approval .is-go")
        page.wait_for_function(
            """() => document.querySelector('[data-status]').textContent.trim() === '\ub05d'""", timeout=10000)
        jump = [c for c in page.query_selector_all("#demo .sugg-chip") if c.get_attribute("data-plays") == "1"]
        need(len(jump) == 1, f"groupbuy: {len(jump)} follow-ups map to a recording (want 1)")
        if jump:
            want = (jump[0].text_content() or "").strip()
            jump[0].click()
            page.wait_for_function(
                """() => document.querySelector('[data-status]').textContent.trim() === '\ub05d'""", timeout=15000)
            got = (page.text_content("#demo .msg-user") or "").strip()
            need(got == want, f"follow-up jump: played {got[:24]!r}, chip said {want[:24]!r}")
            need(page.query_selector('.scn[data-scn="diagnose"][aria-current="true"]') is not None,
                 "follow-up jump: picker did not follow")
            NOTES["followup_jump"] = {"chip": want, "played": got}

        # 4) dark theme
        page.click("[data-theme-toggle]")
        page.wait_for_timeout(250)
        theme = page.get_attribute("html", "data-theme")
        need(theme == "dark", f"theme toggle did not reach dark ({theme!r})")
        page.locator("#demo").screenshot(path=str(SHOTS / "dock-dark.png"))
        page.click("[data-theme-toggle]")
        page.wait_for_timeout(250)
        page.locator("#demo").screenshot(path=str(SHOTS / "dock-light.png"))

        # 5) 375 wide, no horizontal overflow
        page.set_viewport_size({"width": 375, "height": 800})
        page.wait_for_timeout(400)
        play(page, "subscription")
        m375 = page.query_selector('#demo .ui-card--table .more[aria-expanded="false"]')
        if m375: m375.click(); page.wait_for_timeout(150)
        sw, iw = page.evaluate("() => [document.documentElement.scrollWidth, innerWidth]")
        need(sw <= iw, f"horizontal overflow at 375: {sw}/{iw}")
        page.locator("#demo").screenshot(path=str(SHOTS / "dock-375.png"))
        NOTES["mobile375"] = {"scrollWidth": sw, "innerWidth": iw,
                              "cards": len(page.query_selector_all("#demo .ui-card"))}

        # 6) English home: English chrome, Korean transcript
        en = browser.new_page(viewport={"width": 1440, "height": 950})
        en_errors = []
        en.on("pageerror", lambda e: en_errors.append(str(e)))
        en.goto((ROOT / "site" / "en" / "index.html").resolve().as_uri())
        en.wait_for_selector("#demo .player", timeout=10000)
        en.click('[data-speed="0"]')
        en.click('.scn[data-scn="dormant"]')
        en.wait_for_function(
            """() => document.querySelector('[data-status]').textContent.trim() === 'finished'""", timeout=15000)
        need(en.query_selector("#demo .ui-card--table") is not None, "EN: no table card")
        need("휴면" in (en.text_content("#demo .msg-user") or ""), "EN: transcript is not the Korean recording")
        need(not en_errors, f"EN page errors: {en_errors[:3]}")
        NOTES["en"] = {"status": en.text_content("[data-status]").strip(),
                       "play_label": en.text_content("[data-play]").strip(),
                       "cards": len(en.query_selector_all("#demo .ui-card")),
                       "followups": len(en.query_selector_all("#demo .sugg-chip"))}
        en.close()

        # 7) reduced motion: the replay still completes, without typing animation
        rm = browser.new_context(reduced_motion="reduce")
        rp = rm.new_page()
        rp.goto(KO)
        rp.wait_for_selector("#demo .player", timeout=10000)
        rp.click('.scn[data-scn="subscription"]')        # 1x speed on purpose
        rp.wait_for_function(
            """() => document.querySelector('[data-status]').textContent.trim() === '\ub05d'""", timeout=8000)
        rm_cards = len(rp.query_selector_all("#demo .ui-card"))
        rm_user = (rp.text_content("#demo .msg-user") or "").strip()
        need(rm_cards >= 1, "reduced motion: replay finished with no cards (autoplay raced the click)")
        need("\uad6c\ub3c5" in rm_user, f"reduced motion: played the wrong scenario ({rm_user[:20]!r})")
        NOTES["reduced_motion"] = {"finished_at_1x": True, "cards": rm_cards, "user": rm_user}
        rm.close()

        need(not errors, f"page errors: {errors[:3]}")
        NOTES["page_errors"] = errors
        NOTES["shots"] = str(SHOTS)
        browser.close()

    print(json.dumps({"fails": FAILS, "notes": NOTES}, ensure_ascii=False, indent=1))
    return 1 if FAILS else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except PWError as e:
        print(json.dumps({"fails": [f"playwright: {e}"]}, ensure_ascii=False))
        sys.exit(1)
