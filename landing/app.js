(() => {
  "use strict";

  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const easeOut = (t) => 1 - Math.pow(1 - t, 4);
  const fontsReady = document.fonts ? document.fonts.ready : Promise.resolve();
  const canHover = matchMedia("(hover: hover) and (pointer: fine)").matches;

  // Call fn(true/false) as el enters and leaves the viewport.
  function whenVisible(el, fn, threshold = 0.2) {
    new IntersectionObserver((es) => es.forEach((e) => fn(e.isIntersecting)), { threshold }).observe(el);
  }

  // Clip a full-width indicator down to one child: animates without touching layout.
  function clipTo(indicator, container, el) {
    // measure content extent from the last child, not scrollWidth (which includes the indicator itself)
    const last = [...container.children].filter((c) => c !== indicator).pop();
    const total = last.offsetLeft + last.offsetWidth;
    indicator.style.width = total + "px";
    const right = total - (el.offsetLeft + el.offsetWidth);
    indicator.style.clipPath = `inset(0 ${right}px 0 ${el.offsetLeft}px round 999px)`;
  }

  /* ---------------- Nav: scrollspy pill ---------------- */
  (function nav() {
    const wrap = $(".nav__links");
    const links = $$("a", wrap);
    const pill = $(".nav__pill");

    const sections = links.map((a) => $(a.getAttribute("href")));
    let current = null;
    const move = (a) => {
      if (!a) { pill.style.opacity = 0; return; }
      pill.style.opacity = 1;
      clipTo(pill, wrap, a);
      // scroll the rail only if the active entry is cut off, and only by the amount needed
      const pad = 16, start = a.offsetLeft - pad, end = a.offsetLeft + a.offsetWidth + pad;
      const view = wrap.scrollLeft, viewEnd = view + wrap.clientWidth;
      let target = null;
      if (start < view) target = Math.max(0, start);
      else if (end > viewEnd) target = end - wrap.clientWidth;
      if (target !== null && Math.abs(target - view) > 1) {
        wrap.scrollTo({ left: target, behavior: reduced ? "auto" : "smooth" });
      }
    };
    const spy = () => {
      const mid = innerHeight * 0.35;
      let hit = null;
      // last section whose top has passed the marker; gaps between sections keep it
      sections.forEach((s, i) => { if (s.getBoundingClientRect().top <= mid) hit = links[i]; });
      if (hit === current) return;
      links.forEach((l) => l.removeAttribute("aria-current"));
      if (hit) hit.setAttribute("aria-current", "true");
      current = hit;
      move(hit);
    };
    let ticking = false;
    addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(() => { ticking = false; spy(); }); } }, { passive: true });
    addEventListener("resize", () => move(current));
    spy();
  })();

  /* ---------------- Hero: drag, guide, snap. Plays the three examples once, then rests ---------------- */
  (function demo() {
    const fig = $("[data-demo]");
    const scene = $(".demo__scene", fig);
    const title = $("[data-demo-title]", fig), text = $("[data-demo-text]", fig);
    const dots = $(".demo__dots", fig);
    const css = getComputedStyle(document.documentElement);
    const color = (v) => css.getPropertyValue(v).trim();
    const NS = "http://www.w3.org/2000/svg";

    // Each example: reference objects, the selection's path, and the guide it engages.
    const SCENES = [
      {
        title: "Alignment", text: "The selection lands on the same X coordinate as Cube.",
        refs: [{ x: 80, y: 50, w: 90, h: 90, name: "Cube" }],
        sel: { w: 70, h: 70, from: [260, 250], to: [90, 230] },
        guide: "M125 0V360", color: "--axis-x", tag: { x: 125, y: 190, t: "X" },
        dots: [[125, 140], [125, 230]],
      },
      {
        title: "Equal Spacing", text: "The selection repeats the gap between Cube and Cube.001.",
        refs: [{ x: 40, y: 140, w: 70, h: 70, name: "Cube" }, { x: 170, y: 140, w: 70, h: 70, name: "Cube.001" }],
        sel: { w: 70, h: 70, from: [400, 60], to: [300, 140] },
        guide: "M110 250H170M240 250H300M110 244v12M170 244v12M240 244v12M300 244v12",
        color: "--active", tag: { x: 270, y: 282, t: "⇔ 2 m" },
      },
      {
        title: "Midpoint", text: "The selection lands halfway between Cube and Cube.001.",
        refs: [{ x: 50, y: 150, w: 60, h: 60, name: "Cube" }, { x: 370, y: 150, w: 60, h: 60, name: "Cube.001" }],
        sel: { w: 40, h: 40, from: [290, 290], to: [220, 160] },
        guide: "M110 180H370", color: "--active", tag: { x: 240, y: 128, t: "◇" },
        dots: [[240, 180]],
      },
    ];
    const T = { drag: [400, 1900], release: 2400, snap: 200, fade: 3300, end: 3800 };
    const REST = T.release + 450; // snapped, guide still shown, pointer gone
    const NEAR = 10, ENGAGE = 14, RANGE = 90;

    const el = (tag, attrs, parent) => {
      const n = document.createElementNS(NS, tag);
      for (const k in attrs) n.setAttribute(k, attrs[k]);
      parent && parent.appendChild(n);
      return n;
    };

    let idx = 0, t0 = 0, raf = 0, running = false, parts = null, tour = true, done = false;
    const dotBtns = SCENES.map((s, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-label", s.title);
      b.innerHTML = '<span class="pip"><span class="pip__fill"></span></span>';
      b.addEventListener("click", () => {
        build(i); tour = false; done = false;
        if (reduced) { frame(0, REST); return; }
        t0 = performance.now(); start();
      });
      dots.appendChild(b);
      return b;
    });
    const fills = dotBtns.map((b) => $(".pip__fill", b));

    function build(i) {
      idx = i;
      const s = SCENES[i];
      scene.replaceChildren();
      scene.classList.remove("is-out");
      s.refs.forEach((r) => {
        el("rect", { class: "ref", x: r.x, y: r.y, width: r.w, height: r.h }, scene);
        el("text", { class: "name", x: r.x, y: r.y + r.h + 20 }, scene).textContent = r.name;
      });
      const c = color(s.color);
      const passive = el("path", { class: "passive", d: s.guide }, scene);
      const engaged = el("path", { class: "engaged", d: s.guide, stroke: c }, scene);
      const landing = el("rect", { class: "landing", x: s.sel.to[0], y: s.sel.to[1], width: s.sel.w, height: s.sel.h }, scene);
      const anchors = el("g", {}, scene);
      (s.dots || []).forEach(([x, y]) => el("circle", { class: "dot", cx: x, cy: y, r: 3.5 }, anchors));
      const sel = el("rect", { class: "sel", width: s.sel.w, height: s.sel.h }, scene);
      const tag = el("g", { class: "tag" }, scene);
      const tw = Math.max(26, s.tag.t.length * 8 + 16);
      el("rect", { x: s.tag.x - tw / 2, y: s.tag.y - 11, width: tw, height: 22, fill: c }, tag);
      el("text", { x: s.tag.x, y: s.tag.y + 1 }, tag).textContent = s.tag.t;
      const cursor = el("use", { href: "#cur", width: 28, height: 28 }, scene);
      parts = { passive, engaged, landing, anchors, sel, tag, cursor };
      title.textContent = s.title;
      text.textContent = s.text;
      // lay the pips out around the active capsule; the others slide to make room
      dotBtns.forEach((b, k) => {
        b.setAttribute("aria-current", String(k === i));
        b.style.transform = `translateX(${k * 16 + (k > i ? 20 : 0)}px)`;
        fills[k].style.transform = "scaleX(0)";
      });
    }

    const show = (n, o) => { n.style.opacity = o; };
    function frame(now, fixed) {
      let t = fixed ?? now - t0;
      const last = !tour || idx === SCENES.length - 1;
      if (last && t >= REST) { t = REST; done = true; }
      else if (t >= T.end) { build(idx + 1); t0 = now; t = 0; }
      const s = SCENES[idx], p = parts;
      // the active capsule fills over the time this example plays
      fills[idx].style.transform = `scaleX(${clamp(t / (last ? REST : T.end), 0, 1)})`;
      const [fx, fy] = s.sel.from, [tx, ty] = s.sel.to;
      const len = Math.hypot(tx - fx, ty - fy);
      const nx = tx + (fx - tx) / len * NEAR, ny = ty + (fy - ty) / len * NEAR;
      // drag toward the target, stopping just short of it
      const k = easeOut(clamp((t - T.drag[0]) / (T.drag[1] - T.drag[0]), 0, 1));
      let x = fx + (nx - fx) * k, y = fy + (ny - fy) * k;
      const released = t >= T.release;
      if (released) {
        const r = easeOut(clamp((t - T.release) / T.snap, 0, 1));
        x = nx + (tx - nx) * r; y = ny + (ty - ny) * r;
      }
      const dist = Math.hypot(x - tx, y - ty);
      const engaged = !released && dist <= ENGAGE;
      const guideOut = released ? 1 - clamp((t - T.release - 500) / 400, 0, 1) : 1;
      p.sel.setAttribute("x", x); p.sel.setAttribute("y", y);
      show(p.passive, engaged || released ? 0 : clamp(1 - (dist - ENGAGE) / RANGE, 0, 1));
      show(p.engaged, engaged ? 1 : released ? guideOut : 0);
      show(p.tag, engaged ? 1 : released ? guideOut : 0);
      show(p.anchors, engaged ? 1 : released ? guideOut : 0);
      show(p.landing, engaged ? 1 : 0);
      // the pointer holds the selection, then lets go
      const lift = released ? easeOut(clamp((t - T.release) / 600, 0, 1)) : 0;
      p.cursor.setAttribute("x", x + s.sel.w * .6 - 8 + lift * 14);
      p.cursor.setAttribute("y", y + s.sel.h * .6 - 5 + lift * 18);
      show(p.cursor, t < T.drag[0] ? clamp(t / 300, 0, 1) : 1 - lift);
      scene.classList.toggle("is-out", t > T.fade);
      if (done) { running = false; return; }
      if (running) raf = requestAnimationFrame(frame);
    }
    function start() { cancelAnimationFrame(raf); running = true; raf = requestAnimationFrame(frame); }

    build(0);
    if (reduced) { frame(0, REST); return; }
    let paused = 0;
    whenVisible(fig, (v) => {
      if (done) return;
      if (v && !running) { t0 = performance.now() - paused; start(); }
      else if (!v && running) { paused = performance.now() - t0; running = false; cancelAnimationFrame(raf); }
    }, 0.2);
  })();

  /* ---------------- How it works: user-driven stepper + legend ---------------- */
  (function how() {
    const root = $("[data-how]");
    const stage = $(".how__stage", root);
    const panel = $(".how__panel", root);
    const caption = $("[data-how-caption]", root);
    const tabs = $$("[data-step]", root);
    let i = 0;

    function show(n) {
      i = n;
      stage.dataset.stage = n;
      tabs.forEach((t, k) => { t.setAttribute("aria-selected", String(k === n)); t.tabIndex = k === n ? 0 : -1; });
      panel.setAttribute("aria-labelledby", tabs[n].id);
      caption.textContent = $(".steps__d", tabs[n]).textContent;
    }
    tabs.forEach((t, k) => t.addEventListener("click", () => show(k)));
    root.addEventListener("keydown", (e) => {
      if (!e.target.matches("[data-step]")) return;
      const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
      if (!d) return;
      e.preventDefault();
      const n = (i + d + tabs.length) % tabs.length; show(n); tabs[n].focus();
    });
    show(0);

    // Pointer hover on a legend item isolates its mark in the scene (fine pointers only).
    if (!canHover) return;
    $$("[data-legend]", root).forEach((li) => {
      let before = 0;
      li.addEventListener("mouseenter", () => {
        const part = li.dataset.legend;
        before = i;
        show({ passive: 0, landing: 2 }[part] ?? 2);
        stage.classList.add("is-focus");
        $$("[data-part]", stage).forEach((p) => p.classList.toggle("is-lit", p.dataset.part === part));
      });
      li.addEventListener("mouseleave", () => {
        stage.classList.remove("is-focus");
        $$(".is-lit", stage).forEach((p) => p.classList.remove("is-lit"));
        show(before);
      });
    });
  })();

  /* ---------------- Segmented controls (tabs use aria-selected, radios aria-checked) ---------------- */
  function segmented(seg, onChange) {
    const thumb = $(".seg__thumb", seg);
    const btns = $$("button", seg);
    const attr = btns[0].getAttribute("role") === "radio" ? "aria-checked" : "aria-selected";
    const active = () => btns.find((x) => x.getAttribute(attr) === "true");
    const place = () => clipTo(thumb, seg, active());
    const pick = (b) => {
      if (b === active()) return;
      btns.forEach((x) => { x.setAttribute(attr, String(x === b)); x.tabIndex = x === b ? 0 : -1; });
      place(); onChange(b);
    };
    btns.forEach((b) => b.addEventListener("click", () => pick(b)));
    seg.addEventListener("keydown", (e) => {
      const d = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
      if (!d) return;
      const n = btns[(btns.indexOf(active()) + d + btns.length) % btns.length];
      pick(n); n.focus();
    });
    btns.forEach((x) => { x.tabIndex = x === active() ? 0 : -1; });
    new ResizeObserver(place).observe(seg);
    fontsReady.then(place);
    place();
  }

  /* ---------------- Modes: plays once per change, then holds the result ---------------- */
  (function modes() {
    const root = $("[data-modes]");
    const path = $(".track__cursor-path", root);
    const block = $(".track__block", root), cur = $(".track__cursor", root), guide = $(".track__guide", root);
    const caption = $("[data-track-caption]", root);
    const yieldBtn = $("[data-yield]", root), yieldText = $("[data-yield-text]", root);
    let mode = "release", yielding = false, t0 = 0, raf = 0, lastCap = "", seen = false;
    const L = path.getTotalLength(), GY = 90, TOL = 22, DUR = 2600, END = .86;
    const captions = {
      release: ["Selection follows the pointer", "Guide engaged, selection still follows the pointer", "Released: snaps onto the guide"],
      precision: ["Selection follows the pointer", "Locked onto the guide while dragging", "Released: already on the guide"],
      yield: ["Blender snapping is active", "Magnets draws no guides", "Released: no Magnets snap"],
    };

    function draw(t) {
      const p = path.getPointAtLength(easeOut(clamp(t / .7, 0, 1)) * L);
      const near = Math.abs(p.y - GY) < TOL;
      let by = p.y, phase = 0;
      if (!yielding) {
        if (near) phase = 1;
        if (mode === "precision" && near) by = GY;
        if (t > .74) {
          phase = 2;
          const k = easeOut(clamp((t - .74) / .06, 0, 1));
          by = mode === "release" ? p.y + (GY - p.y) * k : GY;
        }
      } else if (t > .74) phase = 2;
      block.setAttribute("transform", `translate(${p.x} ${by})`);
      cur.setAttribute("transform", `translate(${p.x + 12} ${p.y + 14})`);
      cur.style.opacity = t >= END ? 0 : 1;
      guide.style.opacity = yielding ? 0 : near || phase === 2 ? 1 : .3;
      const cap = captions[yielding ? "yield" : mode][phase];
      if (cap !== lastCap) { caption.textContent = cap; lastCap = cap; }
    }
    function play() {
      cancelAnimationFrame(raf);
      if (reduced) { draw(END); return; }
      t0 = performance.now();
      const step = (now) => {
        const t = Math.min((now - t0) / DUR, END);
        draw(t);
        if (t < END) raf = requestAnimationFrame(step);
      };
      raf = requestAnimationFrame(step);
    }

    segmented($(".seg", root), (b) => {
      mode = b.dataset.mode;
      $$("[data-panel]", root).forEach((p) => (p.hidden = p.dataset.panel !== mode));
      play();
    });
    yieldBtn.addEventListener("click", () => {
      yielding = !yielding;
      yieldBtn.setAttribute("aria-checked", String(yielding));
      root.classList.toggle("is-yield", yielding);
      yieldText.textContent = yielding
        ? "On: Magnets stands aside, with no guides and no snap, unless Yield to Blender Snapping is off."
        : "Off: Magnets snaps as described above.";
      play();
    });
    draw(0);
    whenVisible(root, (v) => { if (v && !seen) { seen = true; play(); } }, .35);
  })();

  /* ---------------- Tolerance presets (values from ops/presets.py) ---------------- */
  (function tolerance() {
    const root = $("[data-tol]");
    const P = {
      precise: { snap: 8, brk: 24, reengage: 8, range: 48, spacing: 18, max: 4 },
      balanced: { snap: 16, brk: 40, reengage: 12, range: 72, spacing: 24, max: 5 },
      loose: { snap: 24, brk: 56, reengage: 16, range: 110, spacing: 32, max: 2 },
    };
    const S = 1.3, HALF = 150; // bands are drawn at ±150 and scaled around the guide
    const band = (n) => $(`.band-${n}`, root), label = (n) => $(`[data-band="${n}"]`, root);
    function apply(name) {
      const p = P[name];
      const h = { range: p.range * S, break: (p.snap + p.brk) * S, snap: p.snap * S };
      for (const k in h) band(k).style.transform = `scaleY(${h[k] / HALF})`;
      label("range").textContent = `Range ${p.range} px`;
      label("break").textContent = `Break ${p.snap} + ${p.brk} px`;
      label("snap").textContent = `Snap ${p.snap} px`;
      label("range").style.transform = `translateY(${-h.range + 16}px)`;
      label("break").style.transform = `translateY(${-h.break + 16}px)`;
      label("snap").style.transform = `translateY(${h.snap + 16}px)`;
      $("[data-tol-meta]", root).textContent = `Re-engage Gap ${p.reengage} px · Maximum Guides ${p.max} · Spacing ${p.spacing} px`;
    }
    segmented($(".seg", root), (b) => apply(b.dataset.preset));
    apply("balanced");
  })();

  /* ---------------- Guide type labels: click to look up in the reference ---------------- */
  function lookup(term) {
    const q = $("[data-q]");
    q.value = term;
    q.dispatchEvent(new Event("input"));
    $("#reference").scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
    q.focus({ preventScroll: true });
  }
  $$(".spec .lbl").forEach((span) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = span.className;
    btn.textContent = span.textContent;
    const first = span.textContent.split(/\s+/)[0];
    const term = { X: "alignment", "-": "collinear" }[first] || first;
    btn.setAttribute("aria-label", `Look up label ${span.textContent} in the reference`);
    btn.title = "Look up in the reference";
    btn.addEventListener("click", () => lookup(term));
    span.replaceWith(btn);
  });

  /* ---------------- Changelog: open it when linked to ---------------- */
  (function changelog() {
    const log = $("#changelog");
    const open = () => { if (location.hash === "#changelog") log.open = true; };
    $$("[data-open-log]").forEach((a) => a.addEventListener("click", () => { log.open = true; }));
    addEventListener("hashchange", open);
    open();
  })();

  /* ---------------- Reference: settings + viewport labels, with filter ---------------- */
  (function reference() {
    const where = {
      panel: "Sidebar ▸ Magnets",
      prefs: "Preferences ▸ Add-ons ▸ Magnets",
      labels: "Shown next to guides in the viewport",
    };
    // [name, description, default or type, extra search words]
    const D = [
      { g: "Viewport labels", w: "labels", glyph: true, items: [
        ["X  Y  Z", "Alignment on that axis. A length after it (X · 0.02 m) is the distance still to close.", "Alignment", "axis alignment"],
        ["⇔ 2 m", "Equal Spacing: the repeated gap between objects.", "Equal Spacing", "gap distribute distribution spacing"],
        ["= · 2 m", "Equal Spacing measured across one object's own span.", "Equal Spacing", "span spacing"],
        ["▭ X · 2 m", "Equal Size: the matched size along that axis.", "Equal Size", "size scale"],
        ["◇", "Midpoint between two points.", "Midpoint", "middle half"],
        ["◎", "Tangency (a contact point between curves) or Concentric (a shared center). The guide shape tells them apart.", "Tangency / Concentric", "circle tangent contact center concentric"],
        ["↔ surf", "Tangency at a surface offset.", "Tangency", "surface offset contact"],
        ["∥", "Parallel edges or directions.", "Parallel", "parallel"],
        ["⊥", "Perpendicular edges or directions.", "Perpendicular", "right angle 90 perpendicular"],
        ["-", "Collinear: the point lies on an edge's line.", "Collinear", "line collinear"],
        ["▭", "Coplanar: the point lies on a face's plane. With an axis and a length, it is Equal Size instead.", "Coplanar", "plane face coplanar"],
        ["⇔ YZ", "Symmetry across the XY, XZ or YZ plane.", "Symmetry", "mirror symmetry plane xy xz"],
        ["→ 45°", "Rotation preview: the angle the rotation snaps to on release.", "Rotate", "rotation angle snap degrees"],
        ["= Cube.002 · 2 m", "Scale preview: the object whose size is matched.", "Scale", "scale size match"],
      ]},
      { g: "General", w: "panel", items: [
        ["Enable Guides", "The checkbox in the panel header. Same as the header button and Shift Alt M.", "On"],
        ["Snap to Guides", "Off shows guides without snapping.", "On"],
        ["Precision Mode", "G, R and S run Magnets' operators, which lock onto guides while dragging. A line under it states what G/R/S will do.", "Off"],
        ["Presets", "Precise, Balanced or Loose tolerance profiles. The active one is highlighted. Reset restores every scene option.", "Balanced"],
      ]},
      { g: "Snapping", w: "panel", items: [
        ["Snap Tolerance", "Screen distance at which a guide engages.", "16 px"],
        ["Break Distance", "Distance added to Snap Tolerance before an engaged guide releases.", "40 px"],
        ["Re-engage Gap", "Distance the pointer must leave the snap zone before a guide can engage again.", "12 px"],
        ["Angle Snap", "Rotation snaps to this increment in degrees. 0 turns it off.", "15°"],
        ["Even Spacing", "Which gap equal-spacing guides equalize: Centers, Edges or Both.", "Both"],
        ["Yield to Blender Snapping", "Skip the Magnets snap whenever Blender's own snapping is active.", "On"],
      ]},
      { g: "Guides", w: "panel", items: [
        ["Range", "Screen distance within which guides appear.", "72 px"],
        ["Maximum Guides", "Largest number of guides shown at once.", "5"],
        ["Spacing", "Minimum screen distance between shown guides.", "24 px"],
        ["Passive Guides", "Show guides before they engage.", "On"],
        ["Feature Hints", "Show the reference feature next to each guide: origin, center, face, corner…", "On"],
        ["Ticks", "Tick marks at guide reference points.", "On"],
        ["Extend to Viewport", "Draw guide lines across the whole 3D viewport.", "On"],
      ]},
      { g: "Alignment", w: "panel", items: [
        ["Alignment Frame", "Axes to align in: World, Local, View, Parent, Collection or a Custom object.", "World"],
        ["Custom Frame Object", "Object whose axes define the frame, when the frame is Custom.", "None"],
        ["Axes X Y Z", "Which axes alignment may snap on.", "All"],
        ["Reference points", "Which points count: Origin, Pivot, Centroid, Face Centers, Bounding Box Corners.", "All"],
      ]},
      { g: "Guide Types", w: "panel", items: [
        ["Relationship types", "Turn each on or off: Alignment, Equal Spacing, Equal Size, Midpoint, Tangency, Parallel, Perpendicular, Collinear, Coplanar, Concentric, Symmetry.", "All on"],
      ]},
      { g: "Colors and lines", w: "prefs", items: [
        ["Passive Color", "Guide color while approaching the snap zone.", "Pale grey"],
        ["Active Color", "Color of engaged guides that have no axis color.", "Magenta"],
        ["Engaged Colors", "Axis Colors: alignment uses X red, Y green, Z blue, other types use the Active Color. Active Color: every engaged guide uses it.", "Axis Colors"],
        ["Line Width", "Guide line width in pixels.", "1.0 px"],
        ["Solid Lines", "Solid guide lines, otherwise dashed. Dashes follow the viewport zoom.", "On"],
      ]},
      { g: "Indicators", w: "prefs", items: [
        ["Proximity Fade", "Guides fade in as the pointer approaches the snap zone.", "On"],
        ["Snap Pulse", "Brief flash when a guide engages.", "On"],
        ["Intersection Dot", "Marker where two engaged guides cross.", "On"],
        ["Snap Anchor Dot", "Dot at the matched point when a guide is engaged.", "On"],
        ["Dot Radius", "Radius of the snap anchor dot.", "4 px"],
      ]},
      { g: "Other preferences", w: "prefs", items: [
        ["Header Toggle", "Show the Magnets on/off button and settings popover in the viewport header.", "On"],
        ["Shortcut", "Rebind the on/off toggle. You can also right-click the header button.", "Shift Alt M"],
        ["Debug Logging", "Print diagnostics to the system console (Window ▸ Toggle System Console). Useful when reporting a problem.", "Off"],
      ]},
    ];

    const list = $("[data-list]"), q = $("[data-q]"), count = $("[data-count]"), empty = $("[data-empty]");
    const rows = [];
    const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
    D.forEach((grp) => {
      const sec = document.createElement("section");
      sec.className = "group";
      sec.innerHTML = `<h3>${esc(grp.g)} <span>${esc(where[grp.w])}</span></h3>`;
      grp.items.forEach(([name, desc, def, extra = ""]) => {
        const row = document.createElement("div");
        row.className = "setting";
        row.innerHTML = `<div class="setting__name"></div><div class="setting__desc"></div><div class="setting__def"></div>`;
        if (grp.glyph) row.firstChild.classList.add("is-glyph");
        if (grp.glyph && def === "Alignment") row.firstChild.classList.add("is-axis");
        rows.push({ row, name, desc, def, hay: `${name} ${desc} ${def} ${grp.g} ${extra}`.toLowerCase(),
          n: row.children[0], d: row.children[1], v: row.children[2] });
        sec.appendChild(row);
      });
      list.appendChild(sec);
    });

    const hl = (text, term) => {
      if (!term) return esc(text);
      const i = text.toLowerCase().indexOf(term);
      if (i < 0) return esc(text);
      return esc(text.slice(0, i)) + "<mark>" + esc(text.slice(i, i + term.length)) + "</mark>" + esc(text.slice(i + term.length));
    };
    function filter() {
      const term = q.value.trim().toLowerCase();
      const words = term.split(/\s+/).filter(Boolean);
      let n = 0;
      rows.forEach((r) => {
        const ok = words.every((w) => r.hay.includes(w));
        r.row.hidden = !ok;
        if (ok) n++;
        r.n.innerHTML = hl(r.name, words[0]); r.d.innerHTML = hl(r.desc, words[0]); r.v.innerHTML = hl(r.def, words[0]);
      });
      $$(".group", list).forEach((s) => (s.hidden = !$$(".setting", s).some((r) => !r.hidden)));
      count.textContent = term ? `${n} of ${rows.length} entries` : `${rows.length} entries`;
      empty.hidden = n !== 0;
      $("[data-empty-q]").textContent = q.value.trim();
    }
    q.addEventListener("input", filter);
    q.addEventListener("keydown", (e) => { if (e.key === "Escape") { q.value = ""; filter(); q.blur(); } });
    $$("[data-try]").forEach((b) => b.addEventListener("click", () => { q.value = b.dataset.try; filter(); q.focus(); }));
    addEventListener("keydown", (e) => {
      if (e.key === "/" && !e.metaKey && !e.ctrlKey && !/input|textarea/i.test(document.activeElement.tagName)) {
        e.preventDefault(); q.focus({ preventScroll: true });
        $("#reference").scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
      }
    });
    filter();
  })();
})();
