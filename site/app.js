const DIAS_SEMANA = ["dom", "seg", "ter", "qua", "qui", "sex", "sab"];
const COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];

function degToCompass(deg) {
  const i = Math.round(((deg % 360) + 360) % 360 / 22.5) % 16;
  return COMPASS[i];
}

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function lerpColor(a, b, f) {
  const pa = hexToRgb(a), pb = hexToRgb(b);
  const r = Math.round(pa[0] + (pb[0] - pa[0]) * f);
  const g = Math.round(pa[1] + (pb[1] - pa[1]) * f);
  const bl = Math.round(pa[2] + (pb[2] - pa[2]) * f);
  return `rgb(${r},${g},${bl})`;
}

function scaleColor(value, stops) {
  const t = Math.max(stops[0][0], Math.min(value, stops[stops.length - 1][0]));
  for (let i = 0; i < stops.length - 1; i++) {
    const [v0, c0] = stops[i], [v1, c1] = stops[i + 1];
    if (t >= v0 && t <= v1) return lerpColor(c0, c1, (t - v0) / (v1 - v0));
  }
  return stops[stops.length - 1][1];
}

const PERIOD_STOPS = [
  [5, "#2e6de0"], [6, "#22c1a6"], [7, "#4fd15a"], [8, "#a8d13a"],
  [9, "#e8d23a"], [10, "#f0922f"], [12, "#e8452f"], [15, "#c93fd6"],
];
const periodColor = (tp) => scaleColor(tp, PERIOD_STOPS);

const WIND_STOPS = [[0, "#3aa0d1"], [10, "#3ad17a"], [18, "#e8d23a"], [28, "#e8452f"]];
const windColor = (speedMs) => scaleColor(speedMs * 1.94384, WIND_STOPS);

const ENERGY_STOPS = [
  [500, "#2e6de0"], [1000, "#22c1a6"], [1500, "#4fd15a"], [2000, "#a8d13a"],
  [2500, "#e8d23a"], [3500, "#f0922f"], [5000, "#e8452f"], [8000, "#c93fd6"],
];
const energyColor = (j) => scaleColor(j, ENERGY_STOPS);

const POWER_STOPS = [
  [3, "#2e6de0"], [6, "#22c1a6"], [9, "#4fd15a"], [12, "#a8d13a"],
  [15, "#e8d23a"], [20, "#f0922f"], [30, "#e8452f"], [45, "#c93fd6"],
];
const powerColor = (kw) => scaleColor(kw, POWER_STOPS);

const TEMP_STOPS = [
  [20, "#2e6de0"], [23, "#22c1a6"], [25, "#4fd15a"], [27, "#e8d23a"],
  [29, "#f0922f"], [31, "#e8452f"],
];
const tempColor = (c) => scaleColor(c, TEMP_STOPS);

// Horario de Brasilia fixo (UTC-3, sem horario de verao). Todas as datas do
// pipeline vem em UTC (valid_time); "deslocamos" -3h e lemos os campos UTC
// do resultado, um truque padrao para simular fuso fixo sem biblioteca.
function toLocalDate(isoOrDate) {
  const d = typeof isoOrDate === "string"
    ? new Date(isoOrDate + (isoOrDate.length <= 10 ? "T00:00:00Z" : ""))
    : isoOrDate;
  return new Date(d.getTime() - 3 * 3600000);
}

function fmtHour(iso) {
  const d = toLocalDate(iso);
  return String(d.getUTCHours()).padStart(2, "0") + "h";
}

function dayKey(iso) {
  return toLocalDate(iso).toISOString().slice(0, 10);
}

function dayLabel(dayKeyStr, withMonth = false) {
  const d = new Date(dayKeyStr + "T12:00:00Z"); // meio-dia evita ambiguidade de fuso
  const day = String(d.getUTCDate()).padStart(2, "0");
  const datePart = withMonth ? `${day}/${String(d.getUTCMonth() + 1).padStart(2, "0")}` : day;
  return `${DIAS_SEMANA[d.getUTCDay()]} ${datePart}`;
}

function isNowColumn(iso, stepHours) {
  // Usa o inicio do "balde" de N horas em que o instante atual cai, em vez do
  // passo mais proximo em distancia absoluta - isso evita que, por exemplo,
  // 22h37 destaque o passo das 00h do dia seguinte so por estar 14min mais
  // perto (1h23 vs 1h37), o que confundiria o usuario antes da meia-noite real.
  const stepMs = stepHours * 3600000;
  const bucketStart = Math.floor(Date.now() / stepMs) * stepMs;
  return new Date(iso).getTime() === bucketStart;
}

// --- Calculo de nascer/por do sol (equacao solar padrao, precisao de minutos) ---
function sunTimes(dateUTCmidnight, lat, lngEast) {
  const rad = Math.PI / 180;
  const J2000 = 2451545.0;
  const dayMs = 86400000;
  const JD = dateUTCmidnight.getTime() / dayMs + 2440587.5 + 0.5; // meio-dia daquele dia UTC

  const nStar = (JD - J2000 - 0.0009) + lngEast / 360;
  const n = Math.round(nStar);
  const Jstar = J2000 + 0.0009 - lngEast / 360 + n;

  const M = ((357.5291 + 0.98560028 * (Jstar - J2000)) % 360 + 360) % 360;
  const Mrad = M * rad;
  const C = 1.9148 * Math.sin(Mrad) + 0.02 * Math.sin(2 * Mrad) + 0.0003 * Math.sin(3 * Mrad);
  const lambda = ((M + 102.9372 + C + 180) % 360 + 360) % 360;
  const lambdaRad = lambda * rad;

  const Jtransit = Jstar + 0.0053 * Math.sin(Mrad) - 0.0069 * Math.sin(2 * lambdaRad);
  const delta = Math.asin(Math.sin(lambdaRad) * Math.sin(23.4397 * rad));

  function hourAngle(elevationDeg) {
    const h = elevationDeg * rad;
    const phi = lat * rad;
    const cosOmega = (Math.sin(h) - Math.sin(phi) * Math.sin(delta)) / (Math.cos(phi) * Math.cos(delta));
    if (cosOmega > 1 || cosOmega < -1) return null;
    return Math.acos(cosOmega) / rad;
  }

  const toDate = (J) => new Date((J - 2440587.5) * dayMs);
  const omega0 = hourAngle(-0.83);
  const omega6 = hourAngle(-6);
  const out = {};
  if (omega0 !== null) {
    out.sunrise = toDate(Jtransit - omega0 / 360);
    out.sunset = toDate(Jtransit + omega0 / 360);
  }
  if (omega6 !== null) {
    out.firstLight = toDate(Jtransit - omega6 / 360);
    out.lastLight = toDate(Jtransit + omega6 / 360);
  }
  return out;
}

function fmtLocalHM(date) {
  if (!date) return "-";
  // horario de Brasilia fixo (UTC-3, sem horario de verao)
  const t = new Date(date.getTime() - 3 * 3600000);
  return `${String(t.getUTCHours()).padStart(2, "0")}:${String(t.getUTCMinutes()).padStart(2, "0")}`;
}

function buildDayLabels(forecast) {
  const row = document.createElement("div");
  row.className = "day-labels";
  let lastDay = null;
  const groups = [];
  for (const f of forecast) {
    const dk = dayKey(f.valid_time);
    if (dk !== lastDay) {
      groups.push({ day: dk, label: dayLabel(dk), count: 0 });
      lastDay = dk;
    }
    groups[groups.length - 1].count++;
  }
  for (const g of groups) {
    const el = document.createElement("div");
    el.className = "day-label";
    el.style.width = `${g.count * 34}px`;
    el.textContent = g.label;
    row.appendChild(el);
  }
  return row;
}

function addDirLabel(col, deg) {
  const dir = document.createElement("div");
  dir.className = "dir-label";
  dir.textContent = degToCompass(deg);
  col.appendChild(dir);
}

function markNow(col, f) {
  if (isNowColumn(f.valid_time, 3)) col.classList.add("is-now");
}

function buildWaveChart(forecast, mode = "combined") {
  const chart = document.createElement("div");
  chart.className = "chart";

  const maxHs = Math.max(2, ...forecast.map((f) => f.hs_m)) * 1.15;
  const maxTp = Math.max(8, ...forecast.map((f) => f.tp_s)) * 1.15;

  let lastDay = null;
  for (const f of forecast) {
    const col = document.createElement("div");
    col.className = "col";
    const dk = dayKey(f.valid_time);
    if (dk !== lastDay) { col.classList.add("day-start"); lastDay = dk; }
    markNow(col, f);

    const track = document.createElement("div");
    track.className = "bar-track";

    if (mode !== "direction") {
      const bar = document.createElement("div");
      bar.className = "bar";
      if (mode === "period") {
        bar.style.height = `${(f.tp_s / maxTp) * 100}%`;
        bar.style.background = periodColor(f.tp_s);
        bar.title = `Tp ${f.tp_s} s`;
      } else if (mode === "height") {
        bar.style.height = `${(f.hs_m / maxHs) * 100}%`;
        bar.style.background = "var(--accent)";
        bar.title = `Hs ${f.hs_m} m`;
      } else {
        bar.style.height = `${(f.hs_m / maxHs) * 100}%`;
        bar.style.background = periodColor(f.tp_s);
        bar.title = `Hs ${f.hs_m} m | Tp ${f.tp_s} s | dir ${f.dir_deg}° (${degToCompass(f.dir_deg)})`;
      }
      track.appendChild(bar);
    }
    col.appendChild(track);

    if (mode !== "direction") {
      const val = document.createElement("div");
      val.className = "value-label";
      val.textContent = mode === "period" ? f.tp_s.toFixed(1) : f.hs_m.toFixed(1);
      col.appendChild(val);
    }

    if (mode === "combined" || mode === "direction") {
      const arrow = document.createElement("div");
      arrow.className = "arrow";
      arrow.style.transform = `rotate(${f.dir_deg + 180}deg)`;
      arrow.style.fontSize = mode === "direction" ? "1.4rem" : "0.85rem";
      arrow.textContent = "↑";
      col.appendChild(arrow);
      addDirLabel(col, f.dir_deg);
    }

    const time = document.createElement("div");
    time.className = "time-label";
    time.textContent = fmtHour(f.valid_time);
    col.appendChild(time);

    chart.appendChild(col);
  }
  return chart;
}

function buildDirectionLineChart(forecast) {
  // "desembrulha" os angulos para nao dar salto visual falso ao cruzar 0/360
  const raw = forecast.map((f) => f.dir_deg);
  const unwrapped = [raw[0]];
  for (let i = 1; i < raw.length; i++) {
    let d = raw[i] - (unwrapped[i - 1] % 360);
    while (d > 180) d -= 360;
    while (d < -180) d += 360;
    unwrapped.push(unwrapped[i - 1] + d);
  }

  const colW = 34;
  const width = forecast.length * colW;
  const height = 160;
  const min = Math.min(...unwrapped) - 15;
  const max = Math.max(...unwrapped) + 15;
  const x = (i) => i * colW + colW / 2;
  const y = (v) => height - ((v - min) / (max - min)) * height;

  let linePath = "";
  unwrapped.forEach((v, i) => {
    linePath += `${i === 0 ? "M" : "L"} ${x(i)} ${y(v)} `;
  });

  // eixo com linhas horizontais e graus dos dois lados, passo "redondo"
  const range = max - min;
  const niceSteps = [5, 10, 15, 20, 30, 45, 90];
  const step = niceSteps.find((s) => s >= range / 5) || 90;
  const firstTick = Math.ceil(min / step) * step;
  const ticks = [];
  for (let v = firstTick; v <= max; v += step) ticks.push(v);

  const gridLines = ticks.map((v) => {
    const yy = y(v);
    const label = Math.round(((v % 360) + 360) % 360);
    return `<line x1="0" y1="${yy}" x2="${width}" y2="${yy}" stroke="rgba(255,255,255,0.08)" stroke-width="1"></line>
      <text x="4" y="${yy - 3}" fill="var(--text-dim)" font-size="10">${label}°</text>
      <text x="${width - 4}" y="${yy - 3}" fill="var(--text-dim)" font-size="10" text-anchor="end">${label}°</text>`;
  }).join("");

  const wrap = document.createElement("div");
  wrap.innerHTML = `<svg width="${width}" height="${height}" style="display:block; overflow: visible;">
    ${gridLines}
    <path d="${linePath}" fill="none" stroke="var(--accent)" stroke-width="2.5"></path>
  </svg>`;

  const labels = document.createElement("div");
  labels.className = "chart";
  labels.style.paddingTop = "6px";
  let lastDay = null;
  forecast.forEach((f) => {
    const col = document.createElement("div");
    col.className = "col";
    col.style.height = "0";
    const dk = dayKey(f.valid_time);
    if (dk !== lastDay) { col.classList.add("day-start"); lastDay = dk; }
    const val = document.createElement("div");
    val.className = "value-label";
    val.textContent = degToCompass(f.dir_deg);
    col.appendChild(val);
    const time = document.createElement("div");
    time.className = "time-label";
    time.textContent = fmtHour(f.valid_time);
    col.appendChild(time);
    labels.appendChild(col);
  });

  const outer = document.createElement("div");
  outer.appendChild(wrap);
  outer.appendChild(labels);
  return outer;
}

function buildWindChart(forecast) {
  const chart = document.createElement("div");
  chart.className = "chart";
  const maxWs = Math.max(5, ...forecast.map((f) => f.wind_speed_ms)) * 1.15;
  let lastDay = null;
  for (const f of forecast) {
    const col = document.createElement("div");
    col.className = "col";
    const dk = dayKey(f.valid_time);
    if (dk !== lastDay) { col.classList.add("day-start"); lastDay = dk; }
    markNow(col, f);

    const track = document.createElement("div");
    track.className = "bar-track";
    const bar = document.createElement("div");
    bar.className = "bar";
    bar.style.height = `${(f.wind_speed_ms / maxWs) * 100}%`;
    bar.style.background = windColor(f.wind_speed_ms);
    const kt = (f.wind_speed_ms * 1.94384).toFixed(0);
    bar.title = `${kt} kt | dir ${f.wind_dir_deg}° (${degToCompass(f.wind_dir_deg)})`;
    track.appendChild(bar);
    col.appendChild(track);

    const val = document.createElement("div");
    val.className = "value-label";
    val.textContent = kt;
    col.appendChild(val);

    const arrow = document.createElement("div");
    arrow.className = "arrow";
    arrow.style.transform = `rotate(${f.wind_dir_deg + 180}deg)`;
    arrow.textContent = "↑";
    col.appendChild(arrow);

    addDirLabel(col, f.wind_dir_deg);

    const time = document.createElement("div");
    time.className = "time-label";
    time.textContent = fmtHour(f.valid_time);
    col.appendChild(time);

    chart.appendChild(col);
  }
  return chart;
}

function buildEPChart(forecast, mode = "power") {
  const chart = document.createElement("div");
  chart.className = "chart";
  const key = mode === "energy" ? "energy_j_m2" : "power_kw_m";
  const colorFn = mode === "energy" ? energyColor : powerColor;
  const unit = mode === "energy" ? "J/m²" : "kW/m";
  const maxV = Math.max(mode === "energy" ? 500 : 5, ...forecast.map((f) => f[key])) * 1.15;

  let lastDay = null;
  for (const f of forecast) {
    const col = document.createElement("div");
    col.className = "col";
    const dk = dayKey(f.valid_time);
    if (dk !== lastDay) { col.classList.add("day-start"); lastDay = dk; }
    markNow(col, f);

    const track = document.createElement("div");
    track.className = "bar-track";
    const bar = document.createElement("div");
    bar.className = "bar";
    bar.style.height = `${(f[key] / maxV) * 100}%`;
    bar.style.background = colorFn(f[key]);
    bar.title = `${f[key]} ${unit}`;
    track.appendChild(bar);
    col.appendChild(track);

    const val = document.createElement("div");
    val.className = "value-label";
    val.textContent = mode === "energy" ? f[key].toFixed(0) : f[key].toFixed(1);
    col.appendChild(val);

    const time = document.createElement("div");
    time.className = "time-label";
    time.style.marginTop = "20px";
    time.textContent = fmtHour(f.valid_time);
    col.appendChild(time);

    chart.appendChild(col);
  }
  return chart;
}

function buildTempChart(forecast, mode = "water") {
  const chart = document.createElement("div");
  chart.className = "chart";
  const key = mode === "air" ? "air_temp_c" : "water_temp_c";
  const maxV = Math.max(32, ...forecast.map((f) => f[key])) * 1.05;
  const minV = Math.min(18, ...forecast.map((f) => f[key])) * 0.95;

  let lastDay = null;
  for (const f of forecast) {
    const col = document.createElement("div");
    col.className = "col";
    const dk = dayKey(f.valid_time);
    if (dk !== lastDay) { col.classList.add("day-start"); lastDay = dk; }
    markNow(col, f);

    const track = document.createElement("div");
    track.className = "bar-track";
    const bar = document.createElement("div");
    bar.className = "bar";
    bar.style.height = `${((f[key] - minV) / (maxV - minV)) * 100}%`;
    bar.style.background = tempColor(f[key]);
    bar.title = `${f[key]} °C`;
    track.appendChild(bar);
    col.appendChild(track);

    const val = document.createElement("div");
    val.className = "value-label";
    val.textContent = mode === "water" ? f[key].toFixed(1) : f[key].toFixed(0);
    col.appendChild(val);

    const time = document.createElement("div");
    time.className = "time-label";
    time.style.marginTop = "20px";
    time.textContent = fmtHour(f.valid_time);
    col.appendChild(time);

    chart.appendChild(col);
  }
  return chart;
}

function tideExtremaToTimestamps(tideExtrema) {
  return tideExtrema.map((e) => ({
    t: new Date(`${e.date_local}T${e.time_local}:00-03:00`).getTime(),
    h: e.height_m,
  }));
}

function tideHeightAt(points, tMs) {
  if (!points.length) return null;
  if (tMs <= points[0].t) return points[0].h;
  if (tMs >= points[points.length - 1].t) return points[points.length - 1].h;
  for (let i = 0; i < points.length - 1; i++) {
    if (tMs >= points[i].t && tMs <= points[i + 1].t) {
      const frac = (tMs - points[i].t) / (points[i + 1].t - points[i].t);
      return points[i].h + (points[i + 1].h - points[i].h) * (1 - Math.cos(Math.PI * frac)) / 2;
    }
  }
  return null;
}

function buildTideGraph(tideExtrema) {
  if (!tideExtrema || tideExtrema.length < 2) {
    const div = document.createElement("div");
    div.className = "loading";
    div.style.padding = "16px";
    div.textContent = "Maré indisponível para este ponto.";
    return div;
  }

  const points = tideExtremaToTimestamps(tideExtrema);
  const t0 = points[0].t, t1 = points[points.length - 1].t;
  const totalHours = (t1 - t0) / 3600000;
  const pxPerHour = 34 / 3;
  const width = Math.max(300, totalHours * pxPerHour);
  const height = 160;

  const heights = points.map((p) => p.h);
  const minH = Math.min(...heights) - 0.2;
  const maxH = Math.max(...heights) + 0.2;
  const x = (t) => ((t - t0) / (t1 - t0)) * width;
  const y = (h) => height - ((h - minH) / (maxH - minH)) * height;

  const stepMin = 15;
  const samples = [];
  for (let t = t0; t <= t1; t += stepMin * 60000) {
    samples.push({ t, h: tideHeightAt(points, t) });
  }

  let linePath = "";
  let areaPath = `M ${x(samples[0].t)} ${height} `;
  samples.forEach((s, i) => {
    linePath += `${i === 0 ? "M" : "L"} ${x(s.t)} ${y(s.h)} `;
    areaPath += `L ${x(s.t)} ${y(s.h)} `;
  });
  areaPath += `L ${x(samples[samples.length - 1].t)} ${height} Z`;

  const now = Date.now();
  let nowLine = "";
  if (now >= t0 && now <= t1) {
    nowLine = `<line x1="${x(now)}" y1="0" x2="${x(now)}" y2="${height}" stroke="var(--accent-strong)" stroke-width="1.5" stroke-dasharray="4,3"></line>`;
  }

  const extremaLabels = points.map((p) => {
    const d = new Date(p.t);
    return `<text x="${x(p.t)}" y="${y(p.h) - 8}" fill="var(--text-dim)" font-size="10" text-anchor="middle">${fmtLocalHM(d)} · ${p.h.toFixed(1)}m</text>`;
  }).join("");

  const wrap = document.createElement("div");
  wrap.className = "tide-graph-wrap";
  wrap.innerHTML = `
    <svg width="${width}" height="${height + 20}" style="display:block; overflow: visible;">
      <path d="${areaPath}" fill="var(--accent)" opacity="0.18"></path>
      <path d="${linePath}" fill="none" stroke="var(--accent)" stroke-width="2.5"></path>
      ${nowLine}
      ${extremaLabels}
      <line class="hover-crosshair" x1="0" y1="0" x2="0" y2="${height}" stroke="var(--text-dim)" stroke-width="1" style="display:none"></line>
    </svg>
    <div class="tide-tooltip"></div>`;

  const svg = wrap.querySelector("svg");
  const crosshair = wrap.querySelector(".hover-crosshair");
  const tooltip = wrap.querySelector(".tide-tooltip");

  svg.addEventListener("mousemove", (ev) => {
    const rect = svg.getBoundingClientRect();
    const px = ev.clientX - rect.left;
    const t = t0 + (px / width) * (t1 - t0);
    const h = tideHeightAt(points, t);
    if (h === null) return;
    crosshair.style.display = "block";
    crosshair.setAttribute("x1", px);
    crosshair.setAttribute("x2", px);
    tooltip.style.display = "block";
    tooltip.style.left = `${px}px`;
    tooltip.style.top = `${y(h)}px`;
    tooltip.textContent = `${fmtLocalHM(new Date(t))} — ${h.toFixed(2)} m`;
  });
  svg.addEventListener("mouseleave", () => {
    crosshair.style.display = "none";
    tooltip.style.display = "none";
  });

  const labels = document.createElement("div");
  labels.className = "day-labels";
  let lastDay = null;
  samples.forEach((s) => {
    const dk = new Date(s.t).toISOString().slice(0, 10);
    if (dk !== lastDay) lastDay = dk;
  });
  // rotulos de dia simples, um por dia coberto
  const dayGroups = [];
  let curDay = null;
  samples.forEach((s) => {
    const d = new Date(s.t - 3 * 3600000);
    const dk = d.toISOString().slice(0, 10);
    if (dk !== curDay) { dayGroups.push({ dk, startX: x(s.t) }); curDay = dk; }
  });
  labels.style.position = "relative";
  labels.style.height = "18px";
  labels.style.minWidth = `${width}px`;
  dayGroups.forEach((g) => {
    const el = document.createElement("div");
    el.className = "day-label";
    el.style.position = "absolute";
    el.style.left = `${g.startX}px`;
    el.style.borderLeft = "2px solid var(--day-sep)";
    el.style.paddingLeft = "4px";
    el.textContent = dayLabel(g.dk);
    labels.appendChild(el);
  });

  const outer = document.createElement("div");
  outer.appendChild(labels);
  outer.appendChild(wrap);
  return outer;
}

function buildTideTable(tideExtrema) {
  if (!tideExtrema || tideExtrema.length === 0) {
    const div = document.createElement("div");
    div.className = "loading";
    div.style.padding = "16px";
    div.textContent = "Maré indisponível para este ponto.";
    return div;
  }

  const typed = tideExtrema.map((e, i) => {
    const prev = tideExtrema[i - 1];
    const isHigh = prev ? e.height_m > prev.height_m : e.height_m > tideExtrema[i + 1]?.height_m;
    return { ...e, isHigh };
  });

  const days = [];
  const byDay = {};
  for (const e of typed) {
    if (!byDay[e.date_local]) { byDay[e.date_local] = []; days.push(e.date_local); }
    byDay[e.date_local].push(e);
  }
  const maxRows = Math.max(...days.map((d) => byDay[d].length));

  const table = document.createElement("table");
  table.className = "tide-table";

  const thead = document.createElement("tr");
  for (const d of days) {
    const th = document.createElement("th");
    th.textContent = dayLabel(d);
    thead.appendChild(th);
  }
  table.appendChild(thead);

  for (let r = 0; r < maxRows; r++) {
    const tr = document.createElement("tr");
    for (const d of days) {
      const td = document.createElement("td");
      const entry = byDay[d][r];
      if (entry) {
        td.innerHTML = `<span class="tide-icon">${entry.isHigh ? "▲" : "▼"}</span> ${entry.time_local}h — ${entry.height_m.toFixed(1)} m`;
      }
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }
  return table;
}

function buildLegend() {
  const wrap = document.createElement("div");
  wrap.className = "legend";
  const label = document.createElement("span");
  label.textContent = "Período (s):";
  wrap.appendChild(label);
  const bands = [5, 6, 7, 8, 9, 10, 12, 15];
  for (const s of bands) {
    const item = document.createElement("span");
    item.className = "legend-item";
    const sw = document.createElement("span");
    sw.className = "swatch";
    sw.style.background = periodColor(s);
    item.appendChild(sw);
    item.appendChild(document.createTextNode(s));
    wrap.appendChild(item);
  }
  return wrap;
}

function closestForecastEntry(forecast) {
  // Mesmo raciocinio do isNowColumn: pega o ultimo passo que ja aconteceu,
  // nao o mais proximo em distancia absoluta (que poderia "pular" pro
  // proximo dia antes da meia-noite real).
  const now = Date.now();
  let best = forecast[0];
  for (const f of forecast) {
    if (new Date(f.valid_time).getTime() <= now) best = f;
    else break;
  }
  return best;
}

function buildSummaryCard(place, gp) {
  const f = closestForecastEntry(gp.forecast);
  const points = gp.tide_extrema && gp.tide_extrema.length >= 2 ? tideExtremaToTimestamps(gp.tide_extrema) : null;
  const now = Date.now();
  const tideNow = points ? tideHeightAt(points, now) : null;
  let tideTrend = "";
  if (points) {
    const h1 = tideHeightAt(points, now + 15 * 60000);
    if (tideNow !== null && h1 !== null) tideTrend = h1 > tideNow ? "▲ subindo" : "▼ vazando";
  }

  const today = new Date(Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth(), new Date().getUTCDate()));
  const sun = sunTimes(today, place.lat, place.lon);

  const stats = [
    { label: "Onda", value: `${f.hs_m.toFixed(1)} m`, sub: `Tp ${f.tp_s}s · ${degToCompass(f.dir_deg)}` },
    { label: "Vento", value: `${(f.wind_speed_ms * 1.94384).toFixed(0)} kt`, sub: degToCompass(f.wind_dir_deg) },
    { label: "Potência", value: `${f.power_kw_m.toFixed(0)} kW/m`, sub: "" },
    { label: "Maré estimada", value: tideNow !== null ? `${tideNow.toFixed(1)} m` : "-", sub: tideTrend },
    { label: "Água", value: `${f.water_temp_c.toFixed(0)}°C`, sub: "" },
    { label: "Ar", value: `${f.air_temp_c.toFixed(0)}°C`, sub: "" },
    { label: "Sol", value: `${fmtLocalHM(sun.sunrise)} - ${fmtLocalHM(sun.sunset)}`, sub: "nascer - pôr" },
  ];

  const wrap = document.createElement("div");
  wrap.style.display = "contents";
  for (const s of stats) {
    const el = document.createElement("div");
    el.className = "summary-stat";
    el.innerHTML = `<div class="stat-label">${s.label}</div><div class="stat-value">${s.value}</div><div class="stat-sub">${s.sub}</div>`;
    wrap.appendChild(el);
  }
  return wrap;
}

function buildWeekStrip(forecast) {
  const byDay = {};
  const order = [];
  for (const f of forecast) {
    const dk = dayKey(f.valid_time);
    if (!byDay[dk]) { byDay[dk] = []; order.push(dk); }
    byDay[dk].push(f);
  }
  const wrap = document.createElement("div");
  wrap.style.display = "contents";
  for (const dk of order) {
    const items = byDay[dk];
    const minHs = Math.min(...items.map((f) => f.hs_m));
    const maxHs = Math.max(...items.map((f) => f.hs_m));
    const midEntry = items[Math.floor(items.length / 2)];
    const day = document.createElement("div");
    day.className = "week-day";
    day.innerHTML = `
      <div class="wd-label">${dayLabel(dk)}</div>
      <div class="wd-range">${minHs.toFixed(1)}-${maxHs.toFixed(1)}m</div>
      <div class="wd-arrow" style="transform:rotate(${midEntry.dir_deg + 180}deg)">↑</div>
      <div class="dir-label">${degToCompass(midEntry.dir_deg)}</div>`;
    wrap.appendChild(day);
  }
  return wrap;
}

let currentWaveMode = "combined";
let currentEPMode = "power";
let currentTempMode = "water";
let currentTideMode = "graph";

async function main() {
  const root = document.getElementById("app");
  let data;
  try {
    const res = await fetch("data/forecast.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    root.innerHTML = `<div class="error">Não foi possível carregar a previsão (${err.message}). Se você está abrindo este arquivo localmente, rode um servidor estático.</div>`;
    return;
  }

  document.getElementById("meta").textContent =
    `Rodada do modelo: ${data.model_run_wave} UTC · Atualizado em: ${data.generated_at} · Fonte: ${data.source}`;

  const select = document.getElementById("place-select");
  select.innerHTML = "";
  for (const [id, place] of Object.entries(data.places)) {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = place.label;
    select.appendChild(opt);
  }
  const defaultPlaceId = "ipojuca_suape";
  if (data.places[defaultPlaceId]) select.value = defaultPlaceId;

  function render(placeId) {
    const place = data.places[placeId];
    const gp = data.grid_points[place.grid_point];
    const forecast = gp.forecast;

    const summaryHost = document.getElementById("summary-card");
    summaryHost.innerHTML = "";
    summaryHost.appendChild(buildSummaryCard(place, gp));

    const weekHost = document.getElementById("week-strip");
    weekHost.innerHTML = "";
    weekHost.appendChild(buildWeekStrip(forecast));

    const waveDayLabels = document.getElementById("wave-day-labels");
    const waveChartHost = document.getElementById("wave-chart");
    waveDayLabels.innerHTML = "";
    waveChartHost.innerHTML = "";
    if (currentWaveMode === "direction") {
      waveDayLabels.style.display = "none";
      waveChartHost.appendChild(buildDirectionLineChart(forecast));
    } else {
      waveDayLabels.style.display = "";
      waveDayLabels.appendChild(buildDayLabels(forecast));
      waveChartHost.appendChild(buildWaveChart(forecast, currentWaveMode));
    }

    const epChartHost = document.getElementById("ep-chart");
    epChartHost.innerHTML = "";
    epChartHost.appendChild(buildEPChart(forecast, currentEPMode));

    const windChartHost = document.getElementById("wind-chart");
    windChartHost.innerHTML = "";
    windChartHost.appendChild(buildWindChart(forecast));

    const tempChartHost = document.getElementById("temp-chart");
    tempChartHost.innerHTML = "";
    tempChartHost.appendChild(buildTempChart(forecast, currentTempMode));

    const tideHost = document.getElementById("tide-host");
    tideHost.innerHTML = "";
    if (currentTideMode === "table") {
      tideHost.appendChild(buildTideTable(gp.tide_extrema));
    } else {
      tideHost.appendChild(buildTideGraph(gp.tide_extrema));
    }
    document.getElementById("tide-note").textContent =
      "Marés altas (▲) e baixas (▼), horário de Brasília.";

    const st = gp.tide_station;
    document.getElementById("tide-panel-title").textContent = st
      ? `Tábua de maré (Ref.: ${st.name}, ${st.lon.toFixed(2)} ${st.lat.toFixed(2)})`
      : "Tábua de maré";

    const distTxt = place.grid_distance_km != null ? ` · ~${place.grid_distance_km} km da costa` : "";
    document.getElementById("grid-info").textContent =
      `Ponto de grade mais próximo: ${gp.grid_lat}, ${gp.grid_lon} (ECMWF Open Data, 0,25°)${distTxt} · Previsão em ponto oceânico do ECMWF; não representa diretamente a arrebentação na praia.`;

    const f = closestForecastEntry(forecast);
    document.getElementById("summary-updated").textContent =
      `Valores referentes a ${dayLabel(dayKey(f.valid_time), true)}, ${fmtHour(f.valid_time)}`;

    const staleEl = document.getElementById("stale-warning");
    const ageH = (Date.now() - new Date(data.generated_at).getTime()) / 3600000;
    if (ageH > 18) {
      staleEl.hidden = false;
      staleEl.textContent = "Aviso: dados desatualizados (mais de 18h desde a última atualização). A previsão pode não refletir as condições mais recentes.";
    } else {
      staleEl.hidden = true;
    }
  }

  select.addEventListener("change", () => render(select.value));
  document.getElementById("legend-host").appendChild(buildLegend());

  function wireTabs(containerId, setter) {
    document.querySelectorAll(`#${containerId} .tab-btn`).forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(`#${containerId} .tab-btn`).forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        setter(btn.dataset.mode);
        render(select.value);
      });
    });
  }
  wireTabs("wave-tabs", (m) => { currentWaveMode = m; });
  wireTabs("ep-tabs", (m) => { currentEPMode = m; });
  wireTabs("temp-tabs", (m) => { currentTempMode = m; });
  wireTabs("tide-tabs", (m) => { currentTideMode = m; });

  render(select.value);
}

main();
