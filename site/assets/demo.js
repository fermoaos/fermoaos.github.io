/* Fermoa — replay chat dock. Plays back real recorded agent executions
   (site/assets/demo/*.json) event by event: thinking, tool calls, generated
   cards, delegation, and the approval interrupt. Nothing here is invented;
   every line on screen comes out of the recording. Vanilla, no dependencies. */
(function () {
  'use strict';
  var root = document.getElementById('demo');
  if (!root) return;
  var EN = (document.documentElement.lang || 'ko').slice(0, 2) === 'en';
  var BASE = root.getAttribute('data-base') || 'assets/demo/';

  var T = EN ? {
    idle: 'idle', loading: 'loading', playing: 'playing', paused: 'paused',
    waiting: 'waiting for approval', ended: 'finished',
    play: 'Play', pause: 'Pause', thinking: 'Thinking', chars: 'characters',
    running: 'running', ok: 'done', failed: 'failed', input: 'Input', output: 'Output',
    delegate: 'Delegated', subDone: 'Sub-agent finished', subFail: 'Sub-agent failed',
    needApproval: 'Approval required', preview: 'If you approve',
    before: 'Before', after: 'After', raw: 'Raw request', expires: 'expires in',
    approve: 'Approve', reject: 'Reject',
    approved: 'Approved, owner, just now, 1 time', whatApproved: 'What was approved',
    rejected: 'Rejected. In the real product the run stops here and you can approve again.',
    next: 'You could ask next', tools: 'tools', delegations: 'delegations',
    sec: 's', inTok: 'in', outTok: 'out', tokens: 'tokens',
    noRecord: 'No recording for this question yet. In the real product the agent answers it right away.',
    loadErr: 'Recordings could not be loaded here. Open the site over http (or GitHub Pages) and the player runs.',
    latest: 'Jump to latest', live: 'Assistant is answering.', y: 'yes', n: 'no',
    more: 'Show {n} more rows', less: 'Collapse'
  } : {
    idle: '대기', loading: '기록 여는 중', playing: '재생 중', paused: '멈춤',
    waiting: '승인 기다리는 중', ended: '끝',
    play: '재생', pause: '일시정지', thinking: '생각', chars: '자',
    running: '실행 중', ok: '완료', failed: '실패', input: '입력', output: '출력',
    delegate: '작업을 맡김', subDone: '맡긴 작업 끝', subFail: '맡긴 작업 실패',
    needApproval: '승인이 필요합니다', preview: '실행하면',
    before: '지금', after: '바뀐 뒤', raw: '원본 요청', expires: '남은 시간',
    approve: '승인', reject: '반려',
    approved: '승인함, 대표, 방금, 1회', whatApproved: '무엇을 승인했나',
    rejected: '반려했습니다. 실제 제품에서도 여기서 멈추고, 다시 승인할 수 있습니다.',
    next: '다음에 물어볼 수 있어요', tools: '도구', delegations: '위임',
    sec: '초', inTok: '입력', outTok: '출력', tokens: '토큰',
    noRecord: '이 질문의 기록은 아직 없습니다. 실제 제품에서는 바로 이어서 답합니다.',
    loadErr: '이 환경에서는 기록을 열 수 없습니다. http 로 열면(깃허브 페이지 포함) 재생됩니다.',
    latest: '최신으로 내리기', live: '에이전트가 답하는 중입니다.', y: '예', n: '아니오',
    more: '외 {n}행 펼치기', less: '접기'
  };

  var log = root.querySelector('[data-log]');
  var player = root.querySelector('[data-player]');
  var statusEl = root.querySelector('[data-status]');
  var liveEl = root.querySelector('[data-live]');
  var playBtn = root.querySelector('[data-play]');
  var latestBtn = root.querySelector('[data-latest]');
  var scnBtns = [].slice.call(root.querySelectorAll('.scn'));
  var REDUCED = window.matchMedia && window.matchMedia('(prefers-reduced-motion:reduce)').matches;

  /* ── helpers ─────────────────────────────────────────────────────────────── */
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function num(v) { return typeof v === 'number' ? v.toLocaleString(EN ? 'en-US' : 'ko-KR') : String(v); }
  function pretty(v) { try { return JSON.stringify(v, null, 2); } catch (e) { return String(v); } }
  function loadJSON(url) {                       /* XHR, not fetch: works on file:// too */
    return new Promise(function (res, rej) {
      var x = new XMLHttpRequest();
      x.open('GET', url, true);
      x.onload = function () {
        var body = x.responseText;
        if ((x.status >= 200 && x.status < 300) || (x.status === 0 && body)) {
          try { res(JSON.parse(body)); } catch (e) { rej(e); }
        } else rej(new Error('HTTP ' + x.status));
      };
      x.onerror = function () { rej(new Error('network')); };
      try { x.send(); } catch (e) { rej(e); }
    });
  }

  /* minimal, safe markdown: headings, bold, inline code, lists, paragraphs */
  function inline(s) {
    s = esc(s);
    s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
    s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    return s;
  }
  function md(src) {
    var out = [], list = null, para = [];
    function flushP() { if (para.length) { out.push('<p>' + inline(para.join(' ')) + '</p>'); para = []; } }
    function flushL() { if (list) { out.push('<' + list.tag + '>' + list.items.join('') + '</' + list.tag + '>'); list = null; } }
    String(src).split(/\n/).forEach(function (raw) {
      var line = raw.replace(/\s+$/, '');
      var h = /^(#{1,6})\s+(.*)$/.exec(line);
      var ul = /^\s*[-*]\s+(.*)$/.exec(line);
      var ol = /^\s*(\d+)[.)]\s+(.*)$/.exec(line);
      if (!line.trim()) { flushP(); flushL(); return; }
      if (h) { flushP(); flushL(); out.push('<h3>' + inline(h[2]) + '</h3>'); return; }
      if (ul) { flushP(); if (!list || list.tag !== 'ul') { flushL(); list = { tag: 'ul', items: [] }; } list.items.push('<li>' + inline(ul[1]) + '</li>'); return; }
      if (ol) { flushP(); if (!list || list.tag !== 'ol') { flushL(); list = { tag: 'ol', items: [] }; } list.items.push('<li>' + inline(ol[2]) + '</li>'); return; }
      flushL(); para.push(line.trim());
    });
    flushP(); flushL();
    return out.join('');
  }

  /* ── generated UI cards ───────────────────────────────────────────────────── */
  var ROWCAP = 8;
  function cell(v) {
    if (v === null || v === undefined) return { t: '', n: false };
    if (typeof v === 'boolean') return { t: v ? T.y : T.n, n: false };
    if (typeof v === 'number') return { t: Number.isInteger(v) ? num(v) : String(v), n: true };
    return { t: String(v), n: false };
  }
  function cardTable(p) {
    var w = el('div', 'tbl-wrap'), tb = document.createElement('table');
    var cols = p.columns || [], rows = p.rows || [];
    var h = '<thead><tr>' + cols.map(function (c) { return '<th scope="col">' + esc(c) + '</th>'; }).join('') + '</tr></thead>';
    var b = rows.map(function (r, i) {
      return '<tr' + (i >= ROWCAP ? ' class="is-extra" hidden' : '') + '>' + (r || []).map(function (v) { var c = cell(v); return '<td' + (c.n ? ' class="num"' : '') + '>' + esc(c.t) + '</td>'; }).join('') + '</tr>';
    }).join('');
    tb.innerHTML = h + '<tbody>' + b + '</tbody>';
    w.appendChild(tb);
    var box = document.createDocumentFragment();
    box.appendChild(w);
    if (rows.length > ROWCAP) {
      var extra = rows.length - ROWCAP;
      var more = el('button', 'more', T.more.replace('{n}', num(extra)));
      more.type = 'button'; more.setAttribute('aria-expanded', 'false'); more.setAttribute('data-rows', String(rows.length));
      more.addEventListener('click', function () {
        var open = more.getAttribute('aria-expanded') !== 'true';
        more.setAttribute('aria-expanded', open ? 'true' : 'false');
        more.textContent = open ? T.less : T.more.replace('{n}', num(extra));
        w.classList.toggle('is-open', open);
        Array.prototype.forEach.call(tb.querySelectorAll('tr.is-extra'), function (tr) { tr.hidden = !open; });
        if (!open) w.scrollTop = 0;
      });
      box.appendChild(more);
    }
    return box;
  }
  function cardPlan(p) {
    var f = document.createDocumentFragment();
    var secs = p.sections || (p.items ? [{ heading: '', bullets: p.items }] : []);
    secs.forEach(function (s) {
      var d = el('div', 'plan-sec');
      if (s.heading) d.appendChild(el('h5', null, s.heading));
      var ul = el('ul');
      (s.bullets || s.items || []).forEach(function (b) { ul.appendChild(el('li', null, typeof b === 'string' ? b : pretty(b))); });
      d.appendChild(ul); f.appendChild(d);
    });
    return f;
  }
  function cardKV(p, skip) {
    var dl = el('dl', 'kv');
    Object.keys(p).forEach(function (k) {
      if (skip.indexOf(k) >= 0) return;
      var v = p[k];
      if (v === null || v === '' || (Array.isArray(v) && !v.length)) return;
      var row = document.createElement('div');
      row.appendChild(el('dt', null, k));
      row.appendChild(el('dd', null, typeof v === 'object' ? pretty(v) : String(v)));
      dl.appendChild(row);
    });
    return dl;
  }
  function cardMetric(p) {
    var d = el('div', 'metric');
    d.appendChild(el('b', null, typeof p.value === 'number' ? num(p.value) : String(p.value)));
    if (p.unit) d.appendChild(el('span', null, p.unit));
    if (p.delta != null) d.appendChild(el('span', null, String(p.delta)));
    return d;
  }
  function svgEl(n, attrs) {
    var e = document.createElementNS('http://www.w3.org/2000/svg', n);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    return e;
  }
  function cardChart(p) {
    var W = 640, H = 190, PL = 44, PR = 8, PT = 10, PB = 26;
    var labels = p.labels || [], series = (p.series || []).filter(function (s) { return s && s.values; });
    var svg = svgEl('svg', { viewBox: '0 0 ' + W + ' ' + H, class: 'chart', role: 'img', 'aria-label': p.title || 'chart' });
    var all = [];
    series.forEach(function (s) { s.values.forEach(function (v) { if (typeof v === 'number') all.push(v); }); });
    if (!all.length || !labels.length) return svg;
    var mx = Math.max.apply(null, all), mn = Math.min(0, Math.min.apply(null, all));
    if (mx === mn) mx = mn + 1;
    var iw = W - PL - PR, ih = H - PT - PB;
    var X = function (i) { return PL + (labels.length === 1 ? iw / 2 : iw * i / (labels.length - 1)); };
    var Y = function (v) { return PT + ih - ih * (v - mn) / (mx - mn); };
    svg.appendChild(svgEl('line', { class: 'axis', x1: PL, y1: PT + ih, x2: W - PR, y2: PT + ih }));
    svg.appendChild(svgEl('line', { class: 'axis', x1: PL, y1: PT, x2: PL, y2: PT + ih }));
    [mx, mn].forEach(function (v, k) {
      var t = svgEl('text', { x: PL - 6, y: k ? PT + ih : PT + 8, 'text-anchor': 'end' });
      t.textContent = Number.isInteger(v) ? num(v) : String(Math.round(v * 1e4) / 1e4);
      svg.appendChild(t);
    });
    var bar = (p.type === 'bar' || p.type === 'column');
    series.forEach(function (s) {
      if (bar) {
        var bw = Math.max(3, iw / labels.length * 0.6 / series.length);
        s.values.forEach(function (v, i) {
          if (typeof v !== 'number') return;
          var y = Y(v);
          svg.appendChild(svgEl('rect', { class: 'bar', x: X(i) - bw / 2, y: y, width: bw, height: Math.max(1, PT + ih - y) }));
        });
      } else {
        var pts = [];
        s.values.forEach(function (v, i) { if (typeof v === 'number') pts.push(X(i) + ',' + Y(v)); });
        svg.appendChild(svgEl('polyline', { class: 'lin', points: pts.join(' ') }));
        s.values.forEach(function (v, i) {
          if (typeof v !== 'number') return;
          svg.appendChild(svgEl('circle', { class: 'pt', cx: X(i), cy: Y(v), r: 2.6 }));
        });
      }
    });
    var step = Math.ceil(labels.length / 7);
    labels.forEach(function (lb, i) {
      if (i % step) return;
      var t = svgEl('text', { x: X(i), y: H - 8, 'text-anchor': 'middle' });
      t.textContent = lb;
      svg.appendChild(t);
    });
    return svg;
  }
  function genCard(kind, p) {
    p = p || {};
    var card = el('div', 'ui-card ui-card--' + kind);
    var h = el('h4');
    h.appendChild(document.createTextNode(p.title || kind));
    h.appendChild(el('span', 'kind', kind));
    card.appendChild(h);
    if (kind === 'table') card.appendChild(cardTable(p));
    else if (kind === 'plan') card.appendChild(cardPlan(p));
    else if (kind === 'chart') card.appendChild(cardChart(p));
    else if (kind === 'metric') card.appendChild(cardMetric(p));
    else if (kind === 'brief') card.appendChild(cardKV(p, ['kind', 'title']));
    else card.appendChild(cardKV(p, ['kind', 'title']));
    return card;
  }

  /* ── state ───────────────────────────────────────────────────────────────── */
  var S = {
    rec: null, slug: null, seg: 0, i: 0, timer: null, speed: 1, instant: REDUCED,
    playing: false, waiting: false, ended: false, elapsed: 0,
    turn: null, text: null, textBuf: '', think: null, thinkBuf: '',
    tools: {}, agents: {}, host: null, mdPending: false, liveAt: 0, load: 0
  };
  var CACHE = {}, USERMSG = {}, seen = false, autoPaused = false;

  function setStatus(s) { if (statusEl) statusEl.textContent = s; }
  function say(msg, force) {
    if (!liveEl) return;
    var now = Date.now();
    if (!force && now - S.liveAt < 1200) return;
    S.liveAt = now; liveEl.textContent = msg;
  }
  function nearBottom() { return log.scrollHeight - log.scrollTop - log.clientHeight < 90; }
  function stick() { if (nearBottom()) log.scrollTop = log.scrollHeight; }
  function host() { return S.host || S.turn || log; }

  /* ── event application ───────────────────────────────────────────────────── */
  function breakText() { S.text = null; S.textBuf = ''; }

  function apply(e) {
    var d = e.data || {};
    switch (e.event) {
      case 'turn_start':
        S.turn = el('article', 'turn');
        S.turn.setAttribute('data-turn', d.turn_id || '');
        log.appendChild(S.turn);
        S.host = null; breakText(); S.think = null;
        say(T.live, true);
        break;

      case 'thinking_delta':
        breakText();
        if (!S.think) {
          S.think = document.createElement('details');
          S.think.className = 'think';
          var sm = el('summary'); sm.textContent = T.thinking;
          var pre = el('pre');
          S.think.appendChild(sm); S.think.appendChild(pre);
          host().appendChild(S.think);
          S.thinkBuf = '';
        }
        S.thinkBuf += (d.text || '');
        S.think.querySelector('pre').textContent = S.thinkBuf;
        S.think.querySelector('summary').textContent = T.thinking + ' ' + num(S.thinkBuf.length) + T.chars;
        stick();
        break;

      case 'thinking_end':
        S.think = null;
        break;

      case 'content_delta':
        S.think = null;
        if (!S.text) {
          S.text = el('div', 'md');
          host().appendChild(S.text);
          S.textBuf = '';
        }
        S.textBuf += (d.text || '');
        renderText();
        stick();
        break;

      case 'tool_use': {
        breakText(); S.think = null;
        var chip = document.createElement('details');
        chip.className = 'tool-chip';
        chip.setAttribute('data-state', 'run');
        chip.setAttribute('data-name', d.name || '');
        chip.setAttribute('data-call', d.call_id || '');
        var s = el('summary');
        s.appendChild(el('span', 'dot'));
        s.appendChild(el('span', 'nm', d.name || 'tool'));
        s.appendChild(el('span', 'st', T.running));
        chip.appendChild(s);
        var body = el('div', 'tool-body');
        var tabs = el('div', 'tabs');
        var bIn = el('button', 'tab', T.input), bOut = el('button', 'tab', T.output);
        bIn.type = 'button'; bOut.type = 'button';
        bIn.setAttribute('aria-selected', 'true'); bOut.setAttribute('aria-selected', 'false');
        var preIn = el('pre', null, pretty(d.input === undefined ? {} : d.input));
        var preOut = el('pre'); preOut.hidden = true; preOut.textContent = '';
        function pick(which) {
          bIn.setAttribute('aria-selected', String(which === 'in'));
          bOut.setAttribute('aria-selected', String(which === 'out'));
          preIn.hidden = which !== 'in'; preOut.hidden = which !== 'out';
        }
        bIn.addEventListener('click', function () { pick('in'); });
        bOut.addEventListener('click', function () { pick('out'); });
        tabs.appendChild(bIn); tabs.appendChild(bOut);
        body.appendChild(tabs); body.appendChild(preIn); body.appendChild(preOut);
        chip.appendChild(body);
        host().appendChild(chip);
        S.tools[d.call_id] = chip;
        stick();
        break;
      }

      case 'tool_result': {
        var c = S.tools[d.call_id];
        if (c) {
          c.setAttribute('data-state', d.ok ? 'ok' : 'error');
          c.querySelector('.st').textContent = d.ok ? T.ok : T.failed;
          var po = c.querySelectorAll('.tool-body pre')[1];
          if (po) po.textContent = pretty(d.error ? { error: d.error, output: d.output } : d.output);
        }
        break;
      }

      case 'gen_ui':
        breakText();
        host().appendChild(genCard(d.kind || 'card', d.payload));
        stick();
        break;

      case 'agent_spawned': {
        breakText(); S.think = null;
        var box = el('div', 'subagent');
        box.setAttribute('data-task', d.task_id || '');
        var hd = el('div', 'sa-head');
        hd.appendChild(el('span', 'p-dot'));
        hd.appendChild(document.createTextNode(d.name || d.agent_id || 'agent'));
        hd.appendChild(el('span', 'chip', T.delegate));
        box.appendChild(hd);
        if (d.task) box.appendChild(el('p', 'sa-task', d.task));
        box.appendChild(el('ol', 'sa-steps'));
        (S.turn || log).appendChild(box);
        S.agents[d.task_id] = box;
        S.host = box;                       /* the sub-agent's own tools and cards land inside it */
        stick();
        break;
      }

      case 'agent_progress': {
        var b = S.agents[d.task_id];
        if (b) {
          var ol = b.querySelector('.sa-steps');
          [].forEach.call(ol.children, function (li) { li.removeAttribute('data-live'); });
          var step = d.step === 'thinking' ? T.thinking : (d.step || '');
          var li = el('li', null, step + (d.note ? ', ' + String(d.note).slice(0, 110) : ''));
          li.setAttribute('data-live', '1');
          ol.appendChild(li);
          stick();
        }
        break;
      }

      case 'agent_done': {
        var ab = S.agents[d.task_id];
        if (ab) {
          [].forEach.call(ab.querySelectorAll('.sa-steps li'), function (li) { li.removeAttribute('data-live'); });
          var done = el('div', 'sa-done');
          done.appendChild(el('b', null, d.ok ? T.subDone : T.subFail));
          if (d.summary) {
            var sm2 = el('div', 'md');
            sm2.innerHTML = md(String(d.summary));
            done.appendChild(sm2);
          }
          ab.appendChild(done);
        }
        S.host = null; breakText();
        stick();
        break;
      }

      case 'approval_auto': {
        breakText();
        var au = el('div', 'ap-note', (EN ? 'Auto-approved by policy: ' : '정책이 자동 승인했습니다: ') +
          [d.op, d.policy_name, d.scope].filter(Boolean).join(', '));
        host().appendChild(au);
        break;
      }

      case 'approval_request':
        breakText(); S.think = null;
        (S.turn || log).appendChild(approvalCard(d));
        say(T.needApproval, true);
        stick();
        break;

      case 'done':
        S.elapsed += (e.t || 0);
        if (!d.paused) finishTurn(d);
        break;
    }
  }

  function renderText() {
    if (S.mdPending) return;
    S.mdPending = true;
    var run = function () {
      S.mdPending = false;
      if (S.text) S.text.innerHTML = md(S.textBuf);
      say(S.textBuf.slice(-160));
    };
    if (S.instant) run(); else setTimeout(run, 60);
  }

  function finishTurn(d) {
    if (!S.turn) return;
    if (S.text) S.text.innerHTML = md(S.textBuf);
    var foot = el('div', 'turn-foot');
    var run = d.run || {}, u = d.usage || {};
    var parts = [];
    if (run.tool_calls != null) parts.push(T.tools + ' ' + num(run.tool_calls) + (EN ? '' : '개'));
    if (run.delegations) parts.push(T.delegations + ' ' + num(run.delegations) + (EN ? '' : '건'));
    parts.push((S.elapsed / 1000).toFixed(1) + T.sec);
    if (u.prompt_tokens != null) parts.push(T.inTok + ' ' + num(u.prompt_tokens) + ' ' + T.tokens);
    if (u.completion_tokens != null) parts.push(T.outTok + ' ' + num(u.completion_tokens) + ' ' + T.tokens);
    foot.appendChild(el('p', 'turn-sum', parts.join(', ')));
    var sg = (d.suggestions || []).slice(0, 3);
    if (sg.length) {
      foot.appendChild(el('p', 'sugg-h', T.next));
      var wrap = el('div', 'sugg');
      sg.forEach(function (s) {
        var b = el('button', 'sugg-chip', s.text);
        b.type = 'button';
        var target = matchScenario(s.text);
        if (target) b.setAttribute('data-plays', '1');
        b.addEventListener('click', function () {
          var t = matchScenario(s.text);
          if (t) { select(t, true); return; }
          var n = wrap.parentNode.querySelector('.sugg-note');
          if (!n) { n = el('p', 'sugg-note'); wrap.parentNode.appendChild(n); }
          n.textContent = T.noRecord;
        });
        wrap.appendChild(b);
      });
      foot.appendChild(wrap);
    }
    S.turn.appendChild(foot);
    stick();
  }

  function matchScenario(text) {
    var t = String(text || '').trim();
    var hit = null;
    Object.keys(USERMSG).forEach(function (slug) {
      if (slug !== S.slug && USERMSG[slug] && USERMSG[slug].trim() === t) hit = slug;
    });
    return hit;
  }

  /* ── approval ────────────────────────────────────────────────────────────── */
  function approvalCard(d) {
    var card = el('div', 'approval');
    var hd = el('div', 'ap-head');
    hd.appendChild(el('h4', null, T.needApproval));
    var risk = d.risk || 'write';
    var rl = EN ? { external_send: 'external send', irreversible: 'irreversible', write: 'write' }
                : { external_send: '외부 발신', irreversible: '비가역', write: '쓰기' };
    var badge = el('span', 'risk-badge', rl[risk] || risk);
    badge.setAttribute('data-risk', risk);
    hd.appendChild(badge);
    hd.appendChild(el('span', 'ap-op', d.op || ''));
    card.appendChild(hd);
    if (d.summary) card.appendChild(el('p', 'ap-sum', d.summary));

    var pv = d.preview || {};
    if ((pv.lines && pv.lines.length) || pv.diff) {
      var box = el('div', 'approval-preview');
      box.appendChild(el('h5', null, T.preview));
      if (pv.lines && pv.lines.length) {
        var ul = el('ul');
        pv.lines.forEach(function (l) { ul.appendChild(el('li', null, l)); });
        box.appendChild(ul);
      }
      if (pv.diff) {
        var df = el('div', 'ap-diff');
        [['before', T.before], ['after', T.after]].forEach(function (k) {
          var col = document.createElement('div');
          col.appendChild(el('h6', null, k[1]));
          col.appendChild(el('pre', null, typeof pv.diff[k[0]] === 'object' ? pretty(pv.diff[k[0]]) : String(pv.diff[k[0]] == null ? '' : pv.diff[k[0]])));
          df.appendChild(col);
        });
        box.appendChild(df);
      }
      card.appendChild(box);
    }

    var rawD = document.createElement('details');
    rawD.className = 'think';
    rawD.appendChild(el('summary', null, T.raw));
    rawD.appendChild(el('pre', null, pretty({ approval_id: d.approval_id, op: d.op, input: d.input })));
    card.appendChild(rawD);

    var total = 1800, left = total;
    var fromRec = (typeof d.expires_at === 'number') ? Math.round(d.expires_at * 1000 - Date.now()) / 1000 : 0;
    if (fromRec > 0 && fromRec < 86400) { left = Math.round(fromRec); total = left; }
    var tm = el('div', 'ap-timer');
    var lbl = el('span', null, T.expires);
    var val = el('b');
    var bar = el('div', 'ap-bar'); var fill = el('i'); bar.appendChild(fill);
    tm.appendChild(lbl); tm.appendChild(val); tm.appendChild(bar);
    card.appendChild(tm);
    function paint() {
      var m = Math.floor(left / 60), s = left % 60;
      val.textContent = m + ':' + (s < 10 ? '0' : '') + s;
      fill.style.width = Math.max(0, (left / total) * 100) + '%';
    }
    paint();
    var iv = setInterval(function () { if (left > 0) { left--; paint(); } }, 1000);

    var acts = el('div', 'ap-actions');
    var no = el('button', 'p-btn', T.reject), yes = el('button', 'p-btn is-go', T.approve);
    no.type = 'button'; yes.type = 'button';
    no.addEventListener('click', function () {
      var n = card.querySelector('.ap-note');
      if (!n) { n = el('p', 'ap-note'); card.appendChild(n); }
      n.textContent = T.rejected;
      say(T.rejected, true);
    });
    yes.addEventListener('click', function () {
      clearInterval(iv);
      var frozen = el('div', 'approval-done');
      frozen.appendChild(el('b', null, T.approved));
      var det = document.createElement('details');
      det.appendChild(el('summary', null, T.whatApproved));
      var keep = card.querySelector('.approval-preview');
      det.appendChild(keep ? keep.cloneNode(true) : el('p', null, d.op || ''));
      frozen.appendChild(det);
      card.parentNode.replaceChild(frozen, card);
      S.waiting = false;
      nextSegment();
    });
    acts.appendChild(no); acts.appendChild(yes);
    card.appendChild(acts);
    return card;
  }

  /* ── driver ──────────────────────────────────────────────────────────────── */
  function events() { return (S.rec && S.rec.segments[S.seg] && S.rec.segments[S.seg].events) || []; }

  function tick() {
    if (!S.playing) return;
    var ev = events();
    while (S.i < ev.length) {
      var e = ev[S.i];
      var prev = S.i > 0 ? ev[S.i - 1].t : e.t;
      var gap = S.instant || !S.speed ? 0 : Math.min(1500, Math.max(0, e.t - prev)) / S.speed;
      if (gap > 14) {
        S.timer = setTimeout(function () { S.timer = null; if (!S.playing) return; apply(ev[S.i]); S.i++; tick(); }, gap);
        return;
      }
      apply(e); S.i++;
      if (S.waiting) return;
    }
    endSegment();
  }

  function endSegment() {
    var segs = (S.rec && S.rec.segments) || [];
    var lastEv = events()[events().length - 1];
    var paused = lastEv && lastEv.event === 'done' && lastEv.data && lastEv.data.paused;
    if (paused && S.seg + 1 < segs.length) { S.waiting = true; S.playing = false; setStatus(T.waiting); setPlayLabel(); return; }
    if (S.seg + 1 < segs.length && !paused) { S.seg++; S.i = 0; tick(); return; }
    S.playing = false; S.ended = true; setStatus(T.ended); setPlayLabel();
  }

  function nextSegment() {
    var segs = (S.rec && S.rec.segments) || [];
    if (S.seg + 1 >= segs.length) { S.ended = true; setStatus(T.ended); return; }
    S.seg++; S.i = 0;
    var seg = segs[S.seg];
    if (seg.user) log.appendChild(el('div', 'msg-user', seg.user));
    S.playing = true; setStatus(T.playing); setPlayLabel();
    tick();
  }

  function setPlayLabel() {
    if (!playBtn) return;
    playBtn.textContent = S.playing ? T.pause : T.play;
    playBtn.setAttribute('aria-pressed', String(S.playing));
  }

  function stop() {
    S.playing = false;
    if (S.timer) { clearTimeout(S.timer); S.timer = null; }
    setPlayLabel();
  }

  function resetLog() {
    stop();
    log.innerHTML = '';
    S.seg = 0; S.i = 0; S.elapsed = 0; S.waiting = false; S.ended = false;
    S.turn = null; S.host = null; S.text = null; S.textBuf = ''; S.think = null; S.thinkBuf = '';
    S.tools = {}; S.agents = {};
  }

  function start() {
    if (!S.rec) return;
    resetLog();
    var seg = S.rec.segments[0];
    if (seg && seg.user) log.appendChild(el('div', 'msg-user', seg.user));
    S.playing = true; setStatus(T.playing); setPlayLabel();
    tick();
  }

  function select(slug, autoplay) {
    S.slug = slug;
    seen = true;                       /* a deliberate pick outranks the scroll autoplay */
    var token = ++S.load;
    scnBtns.forEach(function (b) { b.setAttribute('aria-current', String(b.getAttribute('data-scn') === slug)); });
    stop(); log.innerHTML = ''; setStatus(T.loading);
    log.appendChild(el('p', 'log-note', T.loading));
    var got = function (rec) {
      CACHE[slug] = rec;
      if (token !== S.load) return;    /* a later pick already took over */
      S.rec = rec;
      if (rec.segments && rec.segments[0] && rec.segments[0].user) USERMSG[slug] = rec.segments[0].user;
      log.innerHTML = '';
      setStatus(T.idle);
      if (autoplay !== false) start();
      prefetch();
    };
    if (CACHE[slug]) { got(CACHE[slug]); return; }
    loadJSON(BASE + slug + '.json').then(got).catch(function () {
      if (token !== S.load) return;
      log.innerHTML = '';
      setStatus(T.idle);
      log.appendChild(el('p', 'log-note', T.loadErr));
    });
  }

  var prefetched = false;
  function prefetch() {
    if (prefetched) return; prefetched = true;
    var go = function () {
      scnBtns.forEach(function (b) {
        var s = b.getAttribute('data-scn');
        if (CACHE[s]) return;
        loadJSON(BASE + s + '.json').then(function (r) {
          CACHE[s] = r;
          if (r.segments && r.segments[0] && r.segments[0].user) USERMSG[s] = r.segments[0].user;
        }).catch(function () {});
      });
    };
    if (window.requestIdleCallback) requestIdleCallback(go, { timeout: 4000 }); else setTimeout(go, 1500);
  }

  /* ── wiring ──────────────────────────────────────────────────────────────── */
  scnBtns.forEach(function (b) {
    b.addEventListener('click', function () { select(b.getAttribute('data-scn'), true); });
  });
  if (playBtn) playBtn.addEventListener('click', function () {
    if (S.waiting) return;
    if (S.playing) { stop(); setStatus(T.paused); return; }
    if (S.ended || !S.rec) { start(); return; }
    S.playing = true; setStatus(T.playing); setPlayLabel(); tick();
  });
  root.querySelectorAll('[data-speed]').forEach(function (b) {
    b.addEventListener('click', function () {
      var v = Number(b.getAttribute('data-speed'));
      S.speed = v; S.instant = (v === 0) || REDUCED;
      root.querySelectorAll('[data-speed]').forEach(function (o) { o.setAttribute('aria-pressed', String(o === b)); });
      if (S.playing) { if (S.timer) { clearTimeout(S.timer); S.timer = null; } tick(); }
    });
  });
  var restart = root.querySelector('[data-restart]');
  if (restart) restart.addEventListener('click', function () { start(); });
  if (latestBtn) latestBtn.addEventListener('click', function () { log.scrollTop = log.scrollHeight; });
  log.addEventListener('scroll', function () { if (latestBtn) latestBtn.hidden = nearBottom(); });

  player.addEventListener('keydown', function (e) {
    var tag = (e.target.tagName || '').toLowerCase();
    if (e.key === 'Escape') {
      [].forEach.call(log.querySelectorAll('details[open]'), function (d) { d.open = false; });
      return;
    }
    if ((e.key === ' ' || e.key === 'Spacebar') && tag !== 'button' && tag !== 'input' && tag !== 'summary') {
      e.preventDefault();
      if (playBtn) playBtn.click();
    }
  });

  var launcher = document.querySelector('[data-launcher]');
  if (launcher) launcher.addEventListener('click', function () {
    root.scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'start' });
    if (!S.rec) select(S.slug || scnBtns[0].getAttribute('data-scn'), true);
    else start();
  });

  /* autoplay once when the dock scrolls into view; pause when it leaves */
  if (window.IntersectionObserver) {
    new IntersectionObserver(function (ents) {
      ents.forEach(function (en) {
        if (launcher) launcher.hidden = en.isIntersecting;
        if (en.isIntersecting) {
          if (!seen) { seen = true; select(scnBtns[0].getAttribute('data-scn'), true); }
          else if (autoPaused && !S.waiting && !S.ended) { autoPaused = false; S.playing = true; setStatus(T.playing); setPlayLabel(); tick(); }
        } else if (S.playing) { autoPaused = true; stop(); setStatus(T.paused); }
      });
    }, { threshold: 0.25 }).observe(player);
  } else {
    select(scnBtns[0].getAttribute('data-scn'), true);
  }
})();
