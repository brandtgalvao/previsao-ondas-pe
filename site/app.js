const DIAS_SEMANA = ["dom", "seg", "ter", "qua", "qui", "sex", "sab"];

function periodColor(tp) {
  // Escala de cor por periodo (s), estilo Surfguru: curto=azul/verde, longo=laranja/vermelho/magenta
  const stops = [
    [2, "#2e6de0"], [6, "#22c1a6"], [9, "#4fd15a"], [12, "#e8d23a"],
    [15, "#f0922f"], [18, "#e8452f"], [21, "#c93fd6"],
  ];
  const t = Math.max(stops[0][0], Math.min(tp, stops[stops.length - 1][0]));
  for (let i = 0; i < stops.length - 1; i++) {
    const [v0, c0] = stops[i], [v1, c1] = stops[i + 1];
    if (t >= v0 && t <= v1) return lerpColor(c0, c1, (t - v0) / (v1 - v0));
  }
  return stops[stops.length - 1][1];
}

function lerpColor(a, b, f) {
  const pa = hexToRgb(a), pb = hexToRgb(b);
  const r = Math.round(pa[0] + (pb[0] - pa[0]) * f);
  const g = Math.round(pa[1] + (pb[1] - pa[1]) * f);
  const bl = Math.round(pa[2] + (pb[2] - pa[2]) * f);
  return `rgb(${r},${g},${bl})`;
}

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function windColor(speedMs) {
  const kt = speedMs * 1.94384;
  const stops = [[0, "#3aa0d1"], [10, "#3ad17a"], [18, "#e8d23a"], [28, "#e8452f"]];
  const t = Math.max(0, Math.min(kt, stops[stops.length - 1][0]));
  for (let i = 0; i < stops.length - 1; i++) {
    const [v0, c0] = stops[i], [v1, c1] = stops[i + 1];
    if (t >= v0 && t <= v1) return lerpColor(c0, c1, (t - v0) / (v1 - v0));
  }
  return stops[stops.length - 1][1];
}

function fmtHour(iso) {
  const d = new Date(iso);
  return String(d.getUTCHours()).padStart(2, "0") + "h";
}

function dayKey(iso) {
  return iso.slice(0, 10);
}

function dayLabel(iso) {
  const d = new Date(iso);
  return `${DIAS_SEMANA[d.getUTCDay()]} ${String(d.getUTCDate()).padStart(2, "0")}`;
}

function buildDayLabels(forecast) {
  const row = document.createElement("div");
  row.className = "day-labels";
  let lastDay = null;
  let count = 0;
  const groups = [];
  for (const f of forecast) {
    const dk = dayKey(f.valid_time);
    if (dk !== lastDay) {
      groups.push({ day: dk, label: dayLabel(f.valid_time), count: 0 });
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

function buildWaveChart(forecast) {
  const chart = document.createElement("div");
  chart.className = "chart";
  const maxHs = Math.max(2, ...forecast.map((f) => f.hs_m)) * 1.15;
  let lastDay = null;
  for (const f of forecast) {
    const col = document.createElement("div");
    col.className = "col";
    const dk = dayKey(f.valid_time);
    if (dk !== lastDay) { col.classList.add("day-start"); lastDay = dk; }

    const track = document.createElement("div");
    track.className = "bar-track";
    const bar = document.createElement("div");
    bar.className = "bar";
    bar.style.height = `${(f.hs_m / maxHs) * 100}%`;
    bar.style.background = periodColor(f.tp_s);
    bar.title = `Hs ${f.hs_m} m | Tp ${f.tp_s} s | dir ${f.dir_deg}°`;
    track.appendChild(bar);
    col.appendChild(track);

    const val = document.createElement("div");
    val.className = "value-label";
    val.textContent = f.hs_m.toFixed(1);
    col.appendChild(val);

    const arrow = document.createElement("div");
    arrow.className = "arrow";
    arrow.style.transform = `rotate(${f.dir_deg + 180}deg)`;
    arrow.textContent = "↑";
    col.appendChild(arrow);

    const time = document.createElement("div");
    time.className = "time-label";
    time.textContent = fmtHour(f.valid_time);
    col.appendChild(time);

    chart.appendChild(col);
  }
  return chart;
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

    const track = document.createElement("div");
    track.className = "bar-track";
    const bar = document.createElement("div");
    bar.className = "bar";
    bar.style.height = `${(f.wind_speed_ms / maxWs) * 100}%`;
    bar.style.background = windColor(f.wind_speed_ms);
    const kt = (f.wind_speed_ms * 1.94384).toFixed(0);
    bar.title = `${kt} kt | dir ${f.wind_dir_deg}°`;
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

    const time = document.createElement("div");
    time.className = "time-label";
    time.textContent = fmtHour(f.valid_time);
    col.appendChild(time);

    chart.appendChild(col);
  }
  return chart;
}

function buildPowerChart(forecast) {
  const chart = document.createElement("div");
  chart.className = "chart";
  const maxP = Math.max(5, ...forecast.map((f) => f.power_kw_m)) * 1.15;
  let lastDay = null;
  for (const f of forecast) {
    const col = document.createElement("div");
    col.className = "col";
    const dk = dayKey(f.valid_time);
    if (dk !== lastDay) { col.classList.add("day-start"); lastDay = dk; }

    const track = document.createElement("div");
    track.className = "bar-track";
    const bar = document.createElement("div");
    bar.className = "bar";
    bar.style.height = `${(f.power_kw_m / maxP) * 100}%`;
    bar.style.background = "#4fc3e0";
    bar.title = `${f.power_kw_m} kW/m`;
    track.appendChild(bar);
    col.appendChild(track);

    const val = document.createElement("div");
    val.className = "value-label";
    val.textContent = f.power_kw_m.toFixed(0);
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

function buildTideChart(forecast) {
  const wrap = document.createElement("div");
  const width = forecast.length * 34;
  const height = 160;
  const vals = forecast.map((f) => f.tide_m).filter((v) => v !== null && v !== undefined);

  if (vals.length === 0) {
    wrap.className = "loading";
    wrap.style.padding = "16px";
    wrap.textContent = "Maré indisponível para este ponto.";
    return wrap;
  }

  const min = Math.min(...vals) - 0.2;
  const max = Math.max(...vals) + 0.2;
  const x = (i) => i * 34 + 17;
  const y = (v) => height - ((v - min) / (max - min)) * height;

  let linePath = "";
  let areaPath = `M ${x(0)} ${height} `;
  forecast.forEach((f, i) => {
    const v = f.tide_m;
    const py = v == null ? height : y(v);
    linePath += `${i === 0 ? "M" : "L"} ${x(i)} ${py} `;
    areaPath += `L ${x(i)} ${py} `;
  });
  areaPath += `L ${x(forecast.length - 1)} ${height} Z`;

  wrap.innerHTML = `
    <svg width="${width}" height="${height}" style="display:block">
      <path d="${areaPath}" fill="#4fc3e0" opacity="0.18"></path>
      <path d="${linePath}" fill="none" stroke="#4fc3e0" stroke-width="2"></path>
    </svg>`;

  const labels = document.createElement("div");
  labels.className = "chart";
  labels.style.paddingTop = "4px";
  let lastDay = null;
  forecast.forEach((f) => {
    const col = document.createElement("div");
    col.className = "col";
    col.style.height = "0";
    const dk = dayKey(f.valid_time);
    if (dk !== lastDay) { col.classList.add("day-start"); lastDay = dk; }
    const val = document.createElement("div");
    val.className = "value-label";
    val.textContent = f.tide_m != null ? f.tide_m.toFixed(1) : "-";
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

function buildLegend() {
  const wrap = document.createElement("div");
  wrap.className = "legend";
  const label = document.createElement("span");
  label.textContent = "Período (s):";
  wrap.appendChild(label);
  const bands = [3, 6, 9, 12, 15, 18, 21];
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

async function main() {
  const root = document.getElementById("app");
  let data;
  try {
    const res = await fetch("data/forecast.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    root.innerHTML = `<div class="error">Não foi possível carregar a previsão (${err.message}). Se você está abrindo este arquivo localmente, rode um servidor estático (veja o README).</div>`;
    return;
  }

  document.getElementById("meta").textContent =
    `Rodada do modelo: ${data.model_run_wave} UTC · Gerado em: ${data.generated_at} · Fonte: ${data.source}`;

  const select = document.getElementById("place-select");
  select.innerHTML = "";
  for (const [id, place] of Object.entries(data.places)) {
    const opt = document.createElement("option");
    opt.value = place.grid_point;
    opt.textContent = place.label;
    select.appendChild(opt);
  }

  function render(gridPointId) {
    const gp = data.grid_points[gridPointId];
    const forecast = gp.forecast;

    const waveDayLabels = document.getElementById("wave-day-labels");
    const waveChartHost = document.getElementById("wave-chart");
    waveDayLabels.innerHTML = "";
    waveChartHost.innerHTML = "";
    waveDayLabels.appendChild(buildDayLabels(forecast));
    waveChartHost.appendChild(buildWaveChart(forecast));

    const windChartHost = document.getElementById("wind-chart");
    windChartHost.innerHTML = "";
    windChartHost.appendChild(buildWindChart(forecast));

    const powerChartHost = document.getElementById("power-chart");
    powerChartHost.innerHTML = "";
    powerChartHost.appendChild(buildPowerChart(forecast));

    const tideChartHost = document.getElementById("tide-chart");
    tideChartHost.innerHTML = "";
    tideChartHost.appendChild(buildTideChart(forecast));
    document.getElementById("tide-note").textContent =
      "Maré estimada por interpolação entre marés altas/baixas (Tábua de Maré DHN, estação de referência mais próxima).";

    document.getElementById("grid-info").textContent =
      `Ponto de grade: ${gp.grid_lat}, ${gp.grid_lon} (ECMWF Open Data, 0,25°)`;
  }

  select.addEventListener("change", () => render(select.value));
  document.getElementById("legend-host").appendChild(buildLegend());
  render(select.value);
}

main();
