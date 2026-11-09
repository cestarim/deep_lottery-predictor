(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const SVG = "http://www.w3.org/2000/svg";
  const FORMATS = {
    euromillions: "Columnas: fecha, n_1..n_5, star_1, star_2",
    bonoloto: "Columnas: fecha, n_1..n_6, complementario, reintegro",
  };
  let games = [];

  const el = (tag, props = {}, ...kids) => {
    const e = document.createElement(tag);
    Object.assign(e, props);
    kids.forEach((k) => e.append(k));
    return e;
  };
  const clear = (n) => { while (n.firstChild) n.removeChild(n.firstChild); };
  const key = () => $("game").value;

  async function api(path, opts) {
    let res;
    try { res = await fetch(path, opts); }
    catch (e) { throw new Error("No se pudo conectar con el backend."); }
    const body = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(body.detail || `Error ${res.status}`);
    return body;
  }

  function setStatus(node, cls, text, items = []) {
    clear(node);
    node.className = "status " + cls;
    node.append(text);
    if (items.length) {
      const ul = el("ul");
      items.forEach(([c, t]) => ul.append(el("li", { className: c, textContent: t })));
      node.append(ul);
    }
  }

  function enable(on) {
    ["dataset", "stats", "backtest", "train-btn", "wf-btn"].forEach((id) => { $(id).disabled = !on; });
  }

  function barChart(freqs, group) {
    const entries = Object.entries(freqs).map(([k, v]) => [Number(k), v]);
    const W = 640, H = 170, padL = 26, padB = 18, padT = 8;
    const max = Math.max(...entries.map((e) => e[1]), 1);
    const avg = entries.reduce((s, e) => s + e[1], 0) / entries.length;
    const bw = (W - padL) / entries.length;
    const sorted = [...entries].sort((a, b) => b[1] - a[1]);
    const topSet = new Set(sorted.slice(0, group.count).map((e) => e[0]));
    const lowSet = new Set(sorted.slice(-group.count).map((e) => e[0]));

    const svg = document.createElementNS(SVG, "svg");
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("class", "bars");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", `Frecuencia de ${group.name}`);

    const y = (v) => padT + (H - padT - padB) * (1 - v / max);
    entries.forEach(([n, v], i) => {
      const r = document.createElementNS(SVG, "rect");
      r.setAttribute("x", padL + i * bw + 1);
      r.setAttribute("width", Math.max(bw - 2, 1));
      r.setAttribute("y", y(v));
      r.setAttribute("height", H - padB - y(v));
      r.setAttribute("class", "bar" + (topSet.has(n) ? " top" : lowSet.has(n) ? " low" : ""));
      const t = document.createElementNS(SVG, "title");
      t.textContent = `${n}: ${v} apariciones`;
      r.append(t);
      svg.append(r);
      const step = entries.length > 30 ? 5 : 1;
      if ((n - entries[0][0]) % step === 0) {
        const tx = document.createElementNS(SVG, "text");
        tx.setAttribute("x", padL + i * bw + bw / 2);
        tx.setAttribute("y", H - 4);
        tx.setAttribute("text-anchor", "middle");
        tx.textContent = n;
        svg.append(tx);
      }
    });
    const ln = document.createElementNS(SVG, "line");
    ln.setAttribute("class", "avg");
    ln.setAttribute("x1", padL); ln.setAttribute("x2", W);
    ln.setAttribute("y1", y(avg)); ln.setAttribute("y2", y(avg));
    svg.append(ln);
    [0, max].forEach((v) => {
      const tx = document.createElementNS(SVG, "text");
      tx.setAttribute("x", padL - 4); tx.setAttribute("y", y(v) + 3);
      tx.setAttribute("text-anchor", "end");
      tx.textContent = v;
      svg.append(tx);
    });
    return svg;
  }

  async function loadGames() {
    games = await api("/games");
    const sel = $("game");
    clear(sel);
    games.forEach((g) => sel.append(el("option", { value: g.key, textContent: g.label })));
    onGameChange();
  }

  function onGameChange() {
    $("format-hint").textContent = FORMATS[key()] || "";
    const g = games.find((x) => x.key === key());
    enable(!!(g && g.loaded));
    clear($("upload-status")); clear($("dataset-out")); clear($("stats-out")); clear($("bt-out")); clear($("train-out")); clear($("wf-out"));
    if (g && g.loaded) {
      setStatus($("upload-status"), "ok", `Datos ya cargados: ${g.rows} sorteos.`);
      refreshStats();
    }
  }

  async function upload() {
    const f = $("file").files[0];
    if (!f) return setStatus($("upload-status"), "err", "Elige un archivo CSV.");
    const fd = new FormData();
    fd.append("file", f);
    $("upload").disabled = true;
    try {
      const r = await api(`/games/${key()}/upload`, { method: "POST", body: fd });
      const items = [
        ...r.errors.map((t) => ["err", t]),
        ...r.warnings.map((t) => ["warn", t]),
      ];
      setStatus($("upload-status"), r.ok ? "ok" : "err",
        r.ok ? `Válido: ${r.rows_ok} de ${r.rows_in} filas.` : "El CSV no es válido:", items);
      const g = games.find((x) => x.key === key());
      if (g) { g.loaded = r.ok; g.rows = r.rows_ok; }
      enable(r.ok);
      if (r.ok) refreshStats();
    } catch (e) {
      setStatus($("upload-status"), "err", e.message);
    } finally { $("upload").disabled = false; }
  }

  async function refreshStats() {
    const out = $("stats-out");
    const last = $("last").value;
    try {
      const s = await api(`/games/${key()}/stats` + (last ? `?last=${encodeURIComponent(last)}` : ""));
      const game = games.find((x) => x.key === key());
      clear(out);
      const kp = el("div", { className: "kpis" });
      [[s.rows, "sorteos"], [s.from, "desde"], [s.to, "hasta"]].forEach(([v, l]) =>
        kp.append(el("div", { className: "kpi" }, el("div", { className: "v", textContent: v }), el("div", { className: "l", textContent: l }))));
      out.append(kp);
      const { groups } = game;
      groups.forEach((g) => {
        const title = el("div", { className: "chart-title", textContent: `${g.name} ` },
          el("small", { textContent: `(${g.range[0]}–${g.range[1]}) · naranja: más frecuentes · gris: menos · línea: media` }));
        out.append(title, barChart(s.frequencies[g.name], { name: g.name, count: g.count }));
      });
      out.append(el("p", { className: "hint", textContent: "En un sorteo aleatorio las diferencias entre bolas son ruido estadístico, no una señal." }));
    } catch (e) { setStatus(out, "err", e.message); }
  }

  async function dataset() {
    const q = new URLSearchParams({
      window: $("window").value,
      train: $("train").value / 100,
      val: $("val").value / 100,
    });
    try {
      const d = await api(`/games/${key()}/dataset?${q}`);
      setStatus($("dataset-out"), "ok",
        `X ${JSON.stringify(d.X_shape)} · y ${JSON.stringify(d.y_shape)} — entrenamiento ${d.split.train}, validación ${d.split.val}, test ${d.split.test} (orden cronológico).`);
    } catch (e) { setStatus($("dataset-out"), "err", e.message); }
  }

  async function backtest() {
    const out = $("bt-out");
    const q = new URLSearchParams({
      lookback: $("lookback").value,
      hot: $("mode").value,
      test_fraction: $("testfrac").value / 100,
    });
    $("backtest").disabled = true;
    setStatus(out, "", "Calculando…");
    try {
      const r = await api(`/games/${key()}/backtest?${q}`, { method: "POST" });
      clear(out);
      const t = el("table");
      t.append(el("thead", {}, el("tr", {},
        ...["Grupo", "Modelo", "Azar (media)", "Azar (σ)", "z"].map((h, i) => el("th", { className: i ? "num" : "", textContent: h })))));
      const tb = el("tbody");
      Object.keys(r.model).forEach((g) => {
        const z = r.z_vs_random[g];
        tb.append(el("tr", {},
          el("td", { textContent: g }),
          el("td", { className: "num", textContent: r.model[g].toFixed(3) }),
          el("td", { className: "num", textContent: r.random_mean[g].toFixed(3) }),
          el("td", { className: "num", textContent: r.random_std[g].toFixed(3) }),
          el("td", { className: "num", textContent: z === null ? "—" : z.toFixed(2) })));
      });
      t.append(tb);
      out.append(el("p", { className: "hint", textContent: `${r.n_draws} sorteos de test · aciertos medios por sorteo.` }),
        el("div", { className: "table-wrap" }, t),
        el("p", { className: "hint", textContent: "|z| < 2 es indistinguible del azar. Con varios grupos y pruebas, algún z alto aparece por casualidad." }),
        el("p", { className: "hint", textContent: r.disclaimer }));
    } catch (e) { setStatus(out, "err", e.message); }
    finally { $("backtest").disabled = false; }
  }


  function resultTable(rows, headers) {
    const t = el("table");
    t.append(el("thead", {}, el("tr", {}, ...headers.map((h, i) => el("th", { className: i ? "num" : "", textContent: h })))));
    const tb = el("tbody");
    rows.forEach((r) => tb.append(el("tr", {}, ...r.map((c, i) => el("td", { className: i ? "num" : "", textContent: c })))));
    t.append(tb);
    return el("div", { className: "table-wrap" }, t);
  }

  function lossChart(hist) {
    const W = 640, H = 140, pad = 30;
    const vals = hist.flatMap((h) => [h.train_loss, h.val_loss]);
    const lo = Math.min(...vals), hi = Math.max(...vals), span = hi - lo || 1;
    const x = (i) => pad + (W - pad - 8) * (hist.length === 1 ? 0.5 : i / (hist.length - 1));
    const y = (v) => 8 + (H - 26) * (1 - (v - lo) / span);
    const svg = document.createElementNS(SVG, "svg");
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("class", "bars");
    svg.setAttribute("role", "img"); svg.setAttribute("aria-label", "Pérdida por época");
    [["train_loss", "#38bdf8"], ["val_loss", "#f97316"]].forEach(([k, c]) => {
      const p = document.createElementNS(SVG, "polyline");
      p.setAttribute("points", hist.map((h, i) => `${x(i)},${y(h[k])}`).join(" "));
      p.setAttribute("fill", "none"); p.setAttribute("stroke", c); p.setAttribute("stroke-width", "2");
      svg.append(p);
    });
    [[lo, H - 12], [hi, 14]].forEach(([v, yy]) => {
      const tx = document.createElementNS(SVG, "text");
      tx.setAttribute("x", pad - 4); tx.setAttribute("y", yy); tx.setAttribute("text-anchor", "end");
      tx.textContent = v.toFixed(3); svg.append(tx);
    });
    return svg;
  }

  async function trainModel() {
    const out = $("train-out");
    const q = new URLSearchParams({
      kind: $("kind").value, window: $("window").value, epochs: $("epochs").value,
      dropout: $("dropout").value, patience: $("patience").value,
      train: $("train").value / 100, val: $("val").value / 100,
    });
    $("train-btn").disabled = true;
    setStatus(out, "", "Entrenando… puede tardar unos segundos.");
    try {
      const r = await api(`/games/${key()}/train?${q}`, { method: "POST" });
      const p = await api(`/games/${key()}/predict`);
      clear(out);
      out.append(el("p", { className: "hint", textContent:
        `${r.config.kind.toUpperCase()} · ${r.epochs_run} épocas${r.stopped_early ? " (early stopping)" : ""} · mejor pérdida de validación ${r.best_val_loss} · test: ${r.split.test} sorteos.` }));
      out.append(el("div", { className: "chart-title", textContent: "Pérdida " },
        el("small", { textContent: "azul: entrenamiento · naranja: validación" })), lossChart(r.history));
      out.append(el("div", { className: "chart-title", textContent: "Test frente al azar" }),
        resultTable(Object.entries(r.test).map(([g, v]) => [g, v.hits.toFixed(3), v.random_expected.toFixed(3), v.z === null ? "—" : v.z.toFixed(2), v.significance.p_value.toFixed(3)]),
          ["Grupo", "Aciertos", "Azar esperado", "z", "p"]));
      out.append(el("p", { className: "hint", textContent: "|z| < 2 es indistinguible del azar. Si ves z altos en un solo grupo tras varias pruebas, es casualidad estadística." }));
      out.append(el("div", { className: "chart-title", textContent: "Puntuación del siguiente sorteo " },
        el("small", { textContent: "(no es una predicción fiable)" })),
        resultTable(Object.entries(p.numbers).map(([g, v]) => [g, v.join(" · ")]), ["Grupo", "Valores más puntuados"]));
      out.append(el("p", { className: "hint", textContent: r.disclaimer }));
    } catch (e) { setStatus(out, "err", e.message); }
    finally { $("train-btn").disabled = false; }
  }


  async function walkForward() {
    const out = $("wf-out");
    const q = new URLSearchParams({
      kind: $("kind").value, window: $("window").value, epochs: $("epochs").value,
      dropout: $("dropout").value, patience: $("patience").value,
      folds: $("folds").value, gap: $("gap").value, test_frac: $("wftest").value / 100,
    });
    $("wf-btn").disabled = true;
    setStatus(out, "", "Ejecutando folds…");
    try {
      const r = await api(`/games/${key()}/walkforward?${q}`, { method: "POST" });
      clear(out);
      const groups = Object.keys(r.pooled);
      out.append(resultTable(
        r.folds.map((f) => [`Fold ${f.fold}`, f.train_draws, f.test_draws, ...groups.map((g) => `${f.test[g].hits.toFixed(3)} (z ${f.test[g].z === null ? "—" : f.test[g].z})`)]),
        ["Fold", "Entrenamiento", "Test", ...groups]));
      out.append(el("div", { className: "chart-title", textContent: "Agregado de todos los folds" }),
        resultTable(groups.map((g) => {
          const v = r.pooled[g];
          return [g, v.rate.toFixed(4), v.p0.toFixed(4), `${v.ci95[0].toFixed(3)}–${v.ci95[1].toFixed(3)}`, v.p_value.toFixed(3), v.cohens_h.toFixed(3), v.contains_chance ? "sí" : "NO"];
        }), ["Grupo", "Tasa", "Azar", "IC 95 %", "p", "h de Cohen", "Azar dentro del IC"]));
      out.append(el("p", { className: "hint", textContent: "Cada valor predicho cuenta como un ensayo con probabilidad de azar k/N. Si el IC contiene el azar y p > 0,05, no hay evidencia de señal. Con varios modelos y grupos, algún p < 0,05 aparece por casualidad (corrige por comparaciones múltiples)." }),
        el("p", { className: "hint", textContent: r.disclaimer }));
    } catch (e) { setStatus(out, "err", e.message); }
    finally { $("wf-btn").disabled = false; }
  }

  $("wf-btn").addEventListener("click", walkForward);
  $("train-btn").addEventListener("click", trainModel);
  $("game").addEventListener("change", onGameChange);
  $("upload").addEventListener("click", upload);
  $("stats").addEventListener("click", refreshStats);
  $("dataset").addEventListener("click", dataset);
  $("backtest").addEventListener("click", backtest);
  loadGames().catch((e) => setStatus($("upload-status"), "err", e.message));
})();
