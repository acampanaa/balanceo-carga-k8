import os
from flask import Flask, jsonify
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient(os.environ.get("MONGO_URI", "mongodb://mongo:27017/"))
db = client["demo"]
contador = db["contador"]

POD_NAME = os.environ.get("POD_NAME", "desconocido")
peticiones_este_pod = 0

DASHBOARD = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>K8s Load Balancer Demo</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Courier New', monospace; background: #0d1117; color: #c9d1d9; padding: 2rem; min-height: 100vh; }
  h1 { color: #58a6ff; font-size: 1.4rem; margin-bottom: 0.3rem; }
  .subtitle { color: #8b949e; font-size: 0.85rem; margin-bottom: 2rem; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1.2rem; }
  .card h2 { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1rem; }
  .total { font-size: 3rem; color: #58a6ff; font-weight: bold; }
  .total-label { font-size: 0.8rem; color: #8b949e; margin-top: 0.2rem; }
  .pod-row { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.8rem; padding: 0.6rem; border-radius: 6px; background: #0d1117; }
  .pod-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .pod-name { font-size: 0.78rem; color: #c9d1d9; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .pod-count { font-size: 0.9rem; font-weight: bold; flex-shrink: 0; }
  .bar-wrap { width: 100%; height: 4px; background: #21262d; border-radius: 2px; margin-top: 0.3rem; }
  .bar { height: 4px; border-radius: 2px; transition: width 0.4s ease; }
  .pod-inner { flex: 1; min-width: 0; }
  .log-entry { font-size: 0.78rem; padding: 0.35rem 0; border-bottom: 1px solid #21262d; display: flex; gap: 0.8rem; }
  .log-time { color: #484f58; flex-shrink: 0; }
  .log-pod { font-weight: bold; }
  .log-total { color: #8b949e; margin-left: auto; flex-shrink: 0; }
  .status { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.75rem; color: #3fb950; margin-bottom: 1.5rem; }
  .dot { width: 8px; height: 8px; background: #3fb950; border-radius: 50%; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
  .last-pod { font-size: 1rem; color: #c9d1d9; margin-top: 0.5rem; }
  .empty { color: #484f58; font-size: 0.85rem; }
  @media (max-width: 700px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<h1>Mini-cluster K8s &mdash; Balanceo de Carga</h1>
<p class="subtitle">Cada peticion es atendida por un pod distinto. Observa como se distribuye la carga automaticamente.</p>
<div class="status"><div class="dot"></div> Enviando peticion cada 1.5s &mdash; puerto-forward activo</div>

<div class="grid">
  <div class="card">
    <h2>Peticiones totales (MongoDB)</h2>
    <div class="total" id="total">&mdash;</div>
    <div class="total-label">contador compartido entre todos los pods</div>
    <div style="margin-top:1.4rem">
      <h2 style="margin-bottom:0.5rem">Ultimo pod que respondio</h2>
      <div class="last-pod" id="last-pod"><span style="color:#484f58">esperando...</span></div>
    </div>
  </div>

  <div class="card">
    <h2>Distribucion por pod (esta sesion)</h2>
    <div id="pod-stats"><p class="empty">Esperando peticiones...</p></div>
  </div>

  <div class="card" style="grid-column: span 2">
    <h2>Log de peticiones recientes</h2>
    <div id="log"><p class="empty">Esperando peticiones...</p></div>
  </div>
</div>

<script>
const COLORS = ['#58a6ff','#3fb950','#f78166','#d2a8ff','#ffa657','#79c0ff'];
const podColors = {};
let colorIdx = 0;
const podCounts = {};
let maxCount = 0;

function color(pod) {
  if (!podColors[pod]) podColors[pod] = COLORS[colorIdx++ % COLORS.length];
  return podColors[pod];
}

function shortName(pod) {
  const parts = pod.split('-');
  return parts.length > 2 ? '...-' + parts.slice(-2).join('-') : pod;
}

function renderPods() {
  const el = document.getElementById('pod-stats');
  const entries = Object.entries(podCounts).sort((a,b) => b[1]-a[1]);
  if (!entries.length) return;
  el.innerHTML = entries.map(([pod, count]) => {
    const pct = maxCount > 0 ? Math.round(count / maxCount * 100) : 0;
    const c = color(pod);
    return `<div class="pod-row">
      <div class="pod-dot" style="background:${c}"></div>
      <div class="pod-inner">
        <div class="pod-name" title="${pod}">${shortName(pod)}</div>
        <div class="bar-wrap"><div class="bar" style="width:${pct}%;background:${c}"></div></div>
      </div>
      <div class="pod-count" style="color:${c}">${count}</div>
    </div>`;
  }).join('');
}

function addLog(pod, total) {
  const el = document.getElementById('log');
  if (el.querySelector('.empty')) el.innerHTML = '';
  const now = new Date().toLocaleTimeString('es', {hour12: false});
  const c = color(pod);
  const entry = document.createElement('div');
  entry.className = 'log-entry';
  entry.innerHTML = `<span class="log-time">${now}</span><span class="log-pod" style="color:${c}">${shortName(pod)}</span><span class="log-total">total: ${total}</span>`;
  el.prepend(entry);
  while (el.children.length > 8) el.removeChild(el.lastChild);
}

async function ping() {
  try {
    const res = await fetch('/');
    const d = await res.json();
    const pod = d.pod;
    const total = d.peticiones_totales;

    podCounts[pod] = (podCounts[pod] || 0) + 1;
    maxCount = Math.max(maxCount, podCounts[pod]);

    document.getElementById('total').textContent = total;
    document.getElementById('last-pod').innerHTML = `<span style="color:${color(pod)}">${pod}</span>`;

    renderPods();
    addLog(pod, total);
  } catch(e) {
    console.error('Error al conectar con la app:', e);
  }
}

ping();
setInterval(ping, 1500);
</script>
</body>
</html>"""


@app.route("/")
def index():
    global peticiones_este_pod
    peticiones_este_pod += 1
    doc = contador.find_one_and_update(
        {"_id": "global"},
        {"$inc": {"total": 1}},
        upsert=True,
        return_document=True,
    )
    return jsonify({
        "pod": POD_NAME,
        "peticiones_totales": doc["total"],
    })


@app.route("/stats")
def stats():
    doc = contador.find_one({"_id": "global"}) or {"total": 0}
    return jsonify({
        "pod": POD_NAME,
        "peticiones_este_pod": peticiones_este_pod,
        "peticiones_totales": doc.get("total", 0),
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok", "pod": POD_NAME})


@app.route("/stress")
def stress():
    limite = 100000
    iteraciones = 3
    total = 0
    for _ in range(iteraciones):
        primos = [n for n in range(2, limite) if all(n % d != 0 for d in range(2, int(n**0.5) + 1))]
        total = len(primos)
    return jsonify({
        "pod": POD_NAME,
        "primos_encontrados": total,
    })


@app.route("/dashboard")
def dashboard():
    return DASHBOARD


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
