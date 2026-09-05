(() => {
  const root = document.documentElement;
  const KEY = "fermoa-theme";

  // theme: graph paper (light) <-> blackboard (dark)
  const toggle = document.querySelector("[data-theme-toggle]");
  const applyTheme = (t) => {
    root.setAttribute("data-theme", t);
    if (toggle) {
      const light = toggle.dataset.labelLight || "칠판";   // label shown while light (what you switch TO)
      const dark = toggle.dataset.labelDark || "그래프지";
      toggle.textContent = t === "dark" ? dark : light;
      toggle.setAttribute("aria-label", t === "dark" ? `Switch to ${dark}` : `Switch to ${light}`);
    }
  };
  let saved = null;
  try { saved = localStorage.getItem(KEY); } catch (_) {}
  applyTheme(saved || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  toggle?.addEventListener("click", () => {
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    applyTheme(next);
    try { localStorage.setItem(KEY, next); } catch (_) {}
  });

  // the one motion: hold. lines converge, arc draws, dot lands.
  const stage = document.querySelector(".hero-stage");
  const hold = () => {
    if (!stage) return;
    stage.classList.remove("is-held", "is-released");
    void stage.offsetWidth;                      // restart the stroke animations
    requestAnimationFrame(() => requestAnimationFrame(() => stage.classList.add("is-held")));
  };
  hold();

  // hero film: the lines draw over S1's stillness and let go when the person dissolves (data-release seconds);
  // every loop re-holds. Reduced motion = poster only. The button is the WCAG pause for autoplay > 5s.
  const film = stage?.querySelector(".hero-film");
  const filmBtn = stage?.querySelector("[data-film-toggle]");
  if (film && filmBtn) {
    const release = parseFloat(film.dataset.release || "6");
    // 4.5MB 를 아껴 쓰라는 신호가 오면 자동재생하지 않는다 — 포스터로 두고 버튼은 살려 둔다.
    const net = navigator.connection || {};
    const thrifty = net.saveData === true || /(^|-)2g$/.test(net.effectiveType || "");
    const still = matchMedia("(prefers-reduced-motion: reduce)").matches || thrifty;
    const label = () => {
      const playing = !film.paused;
      filmBtn.textContent = playing ? filmBtn.dataset.labelPause : filmBtn.dataset.labelPlay;
      filmBtn.setAttribute("aria-pressed", playing ? "true" : "false");
    };
    film.addEventListener("timeupdate", () => {
      const t = film.currentTime;
      if (t >= release && !stage.classList.contains("is-released")) stage.classList.add("is-released");
      else if (t < 0.5 && stage.classList.contains("is-released")) hold();
    });
    film.addEventListener("play", label);
    film.addEventListener("pause", label);
    film.addEventListener("error", () => { filmBtn.disabled = true; }, true);
    filmBtn.addEventListener("click", () => { film.paused ? film.play().catch(() => {}) : film.pause(); });
    if (!still) film.play().catch(() => { label(); });   // autoplay blocked -> the button still works
    label();
  }

  // 3-step contact form -> mailto
  const CONTACT_EMAIL = "hyojunguy@gmail.com";
  const form = document.querySelector("[data-steps]");
  if (form) {
    const steps = [...form.querySelectorAll("[data-step]")];
    const prev = form.querySelector("[data-prev]");
    const next = form.querySelector("[data-next]");
    const send = form.querySelector("[data-send]");
    const count = form.querySelector(".step-count");
    let i = 0;
    const show = () => {
      steps.forEach((s, k) => { s.hidden = k !== i; });
      prev.hidden = i === 0;
      next.hidden = i === steps.length - 1;
      send.hidden = i !== steps.length - 1;
      count.textContent = `${i + 1} / ${steps.length}`;
      steps[i].querySelector("input,textarea")?.focus({ preventScroll: true });
    };
    const valid = () => {
      let ok = true;
      steps[i].querySelectorAll("[required]").forEach((el) => {
        const bad = !el.value.trim() || (el.type === "email" && !el.validity.valid);
        el.setAttribute("aria-invalid", bad ? "true" : "false");
        if (bad) ok = false;
      });
      return ok;
    };
    next.addEventListener("click", () => { if (valid()) { i++; show(); } });
    prev.addEventListener("click", () => { i--; show(); });
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      if (!valid()) return;
      const d = Object.fromEntries(new FormData(form).entries());
      const body = `이름: ${d.name}\n이메일: ${d.email}\n소속: ${d.org} (${d.role || "-"})\n\n${d.msg}`;
      location.href = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent("[Fermoa] 문의")}&body=${encodeURIComponent(body)}`;
    });
    show();
  }

  const y = document.querySelector("[data-year]");
  if (y) y.textContent = String(new Date().getFullYear());
})();
