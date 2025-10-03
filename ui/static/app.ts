const tickList = /** @type {HTMLUListElement} */ (document.getElementById("tick-list"));
const workspaceEl = /** @type {HTMLPreElement} */ (document.getElementById("workspace"));
const chart = /** @type {HTMLCanvasElement} */ (document.getElementById("chart"));

async function refresh() {
  const stateResp = await fetch("/api/run/state");
  const state = await stateResp.json();
  const tracesResp = await fetch("/api/run/traces");
  const traces = await tracesResp.json();
  tickList.innerHTML = "";
  traces.forEach((trace: any) => {
    const li = document.createElement("li");
    li.textContent = `Tick ${trace.tick}: ${trace.broadcast ? trace.broadcast.summary : "None"}`;
    tickList.appendChild(li);
  });
  workspaceEl.textContent = JSON.stringify(state.workspace, null, 2);
  renderChart(traces.map((trace: any) => trace.metrics.brier ?? 0.0));
}

function renderChart(values: number[]) {
  const ctx = chart.getContext("2d");
  if (!ctx) return;
  ctx.clearRect(0, 0, chart.width, chart.height);
  ctx.strokeStyle = "#2b8a3e";
  ctx.beginPath();
  values.forEach((value, idx) => {
    const x = (idx / Math.max(1, values.length - 1)) * chart.width;
    const y = chart.height - value * chart.height;
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

refresh();
setInterval(refresh, 2000);
