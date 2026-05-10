#!/usr/bin/env python3
"""Build a static WDSM formalization progress visualization.

The output is intentionally self-contained enough for GitHub Pages: the HTML
embeds the data snapshot used for rendering, and the JSON is written next to it
for downstream tools.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = ROOT / "artifacts" / "wdsm_formalization_pilot.json"
WDSM_DIR = ROOT / "StatInference" / "Matching" / "WDSM"
DOCS_DIR = ROOT / "docs"
DATA_PATH = DOCS_DIR / "wdsm_visualization_data.json"
HTML_PATH = DOCS_DIR / "wdsm_visualization.html"


ORDINAL_TARGETS = {
    "first_target": 1,
    "second_target": 2,
    "third_target": 3,
    "fourth_target": 4,
    "fifth_target": 5,
    "sixth_target": 6,
    "seventh_target": 7,
    "eighth_target": 8,
    "ninth_target": 9,
    "tenth_target": 10,
}


LANES = [
    "deterministic algebra",
    "normalized counts",
    "count ratios and shares",
    "approximation",
    "stochastic interfaces",
    "variance and Wald",
    "reference and gaps",
    "infrastructure",
]


BLOCKERS = [
    {
        "name": "Conditional expectation and score-space identification",
        "status": "open interface",
        "lane": "stochastic interfaces",
    },
    {
        "name": "Survey-weighted double-score balancing theorem",
        "status": "open proof",
        "lane": "normalized counts",
    },
    {
        "name": "Chen-Han nearest-neighbor geometry and reuse moments",
        "status": "reference interface",
        "lane": "reference and gaps",
    },
    {
        "name": "Residual martingale-array CLT",
        "status": "open probability proof",
        "lane": "stochastic interfaces",
    },
    {
        "name": "Estimated-score local expansion and Godambe variance",
        "status": "open asymptotic proof",
        "lane": "variance and Wald",
    },
    {
        "name": "Full lake build StatInference after target 335",
        "status": "deferred: Lake monitor stall",
        "lane": "infrastructure",
    },
]


def lane_for_text(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["wald", "variance", "studentized", "positivevariance"]):
        return "variance and Wald"
    if any(k in t for k in ["approximation", "negligible", "envelope"]):
        return "approximation"
    if any(k in t for k in ["countratio", "share", "hajek", "ratio"]):
        return "count ratios and shares"
    if any(k in t for k in ["normalizedcount", "indicatorbridge", "countpositivity", "finitecell"]):
        return "normalized counts"
    if any(k in t for k in ["asymptotic", "clt", "martingale", "stochastic", "empiricalprocess"]):
        return "stochastic interfaces"
    if any(k in t for k in ["reference", "chen", "han", "audit", "estimatedscore"]):
        return "reference and gaps"
    if any(k in t for k in ["finite", "algebra", "matching", "survey", "population"]):
        return "deterministic algebra"
    return "infrastructure"


def target_number(key: str, record: dict[str, Any], fallback: int) -> int:
    if key in ORDINAL_TARGETS:
        return ORDINAL_TARGETS[key]
    text = " ".join(
        str(record.get(field, ""))
        for field in ["verification_note", "informal_source", "reason"]
    )
    match = re.search(r"\b[Tt]arget\s+(\d+)\b", text)
    if match:
        return int(match.group(1))
    return fallback


def target_label(number: int) -> str:
    return f"target {number}" if number else "target ?"


def load_targets(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    fallback = 1
    for key, value in artifact.items():
        if not key.endswith("_target") or not isinstance(value, dict):
            continue
        if "proved_objects" not in value and "lean_file" not in value:
            continue
        number = target_number(key, value, fallback)
        fallback = max(fallback + 1, number + 1)
        module = str(value.get("lean_module", ""))
        lean_file = str(value.get("lean_file", ""))
        informal = str(value.get("informal_source", ""))
        lane = lane_for_text(" ".join([module, lean_file, informal]))
        proved_objects = [str(obj) for obj in value.get("proved_objects", [])]
        records.append(
            {
                "key": key,
                "number": number,
                "label": target_label(number),
                "lane": lane,
                "lean_module": module,
                "lean_file": lean_file,
                "verification_status": str(value.get("verification_status", "")),
                "informal_source": informal,
                "proved_objects": proved_objects,
                "proved_count": len(proved_objects),
                "verification_note": str(value.get("verification_note", "")),
            }
        )
    records.sort(key=lambda item: item["number"])
    return records


def module_short_name(module: str, lean_file: str) -> str:
    if module.startswith("StatInference.Matching.WDSM."):
        return module.rsplit(".", 1)[-1]
    if lean_file.endswith(".lean"):
        return Path(lean_file).stem
    return module or "(unknown)"


def load_module_graph(targets: list[dict[str, Any]]) -> dict[str, Any]:
    target_counts = Counter(
        module_short_name(t["lean_module"], t["lean_file"]) for t in targets
    )
    proved_counts = Counter()
    lanes: dict[str, str] = {}
    for t in targets:
        name = module_short_name(t["lean_module"], t["lean_file"])
        proved_counts[name] += t["proved_count"]
        lanes[name] = t["lane"]

    import_edges: list[dict[str, str]] = []
    modules: dict[str, dict[str, Any]] = {}
    if WDSM_DIR.exists():
        for path in sorted(WDSM_DIR.glob("*.lean")):
            current = path.stem
            text = path.read_text(encoding="utf-8")
            lane = lanes.get(current, lane_for_text(current))
            modules[current] = {
                "id": current,
                "lane": lane,
                "target_count": target_counts[current],
                "proved_count": proved_counts[current],
            }
            for line in text.splitlines():
                match = re.match(r"import\s+StatInference\.Matching\.WDSM\.([A-Za-z0-9_']+)\s*$", line)
                if match:
                    imported = match.group(1)
                    import_edges.append({"source": imported, "target": current})

    for edge in import_edges:
        for endpoint in [edge["source"], edge["target"]]:
            modules.setdefault(
                endpoint,
                {
                    "id": endpoint,
                    "lane": lanes.get(endpoint, lane_for_text(endpoint)),
                    "target_count": target_counts[endpoint],
                    "proved_count": proved_counts[endpoint],
                },
            )

    visible = {
        name
        for name, node in modules.items()
        if node["target_count"] > 0 or node["proved_count"] > 0
    }
    # Add immediate WDSM imports around formalized modules so the graph shows
    # local context without becoming the full repository import graph.
    for edge in import_edges:
        if edge["source"] in visible or edge["target"] in visible:
            visible.add(edge["source"])
            visible.add(edge["target"])

    nodes = [modules[name] for name in sorted(visible)]
    edges = [
        edge
        for edge in import_edges
        if edge["source"] in visible and edge["target"] in visible
    ]
    return {"nodes": nodes, "edges": edges}


def build_data() -> dict[str, Any]:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    targets = load_targets(artifact)
    latest = max((t["number"] for t in targets), default=0)
    theorem_count = sum(t["proved_count"] for t in targets)
    lane_counts = Counter(t["lane"] for t in targets)
    lane_theorem_counts = Counter()
    module_counts = Counter()
    module_theorem_counts = Counter()
    for target in targets:
        lane_theorem_counts[target["lane"]] += target["proved_count"]
        module = module_short_name(target["lean_module"], target["lean_file"])
        module_counts[module] += 1
        module_theorem_counts[module] += target["proved_count"]

    top_modules = [
        {
            "module": module,
            "targets": module_counts[module],
            "proved_objects": module_theorem_counts[module],
            "lane": lane_for_text(module),
        }
        for module, _ in module_counts.most_common(24)
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_artifact": str(ARTIFACT_PATH.relative_to(ROOT)),
        "status": artifact.get("status", ""),
        "root_lake_build": artifact.get("verification", {}).get("root_lake_build", ""),
        "latest_target": latest,
        "target_count": len(targets),
        "proved_object_count": theorem_count,
        "lanes": [
            {
                "name": lane,
                "targets": lane_counts[lane],
                "proved_objects": lane_theorem_counts[lane],
            }
            for lane in LANES
        ],
        "top_modules": top_modules,
        "blockers": BLOCKERS,
        "targets": targets,
        "recent_targets": targets[-160:],
        "module_graph": load_module_graph(targets),
    }


def render_html(data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
    generated = escape(data["generated_at"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WDSM Lean Formalization Territory</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #1b2430;
      --muted: #657184;
      --line: #d8dee8;
      --surface: #f7f9fc;
      --panel: #ffffff;
      --green: #16825d;
      --amber: #b36b00;
      --red: #ba3a36;
      --blue: #2f65c9;
      --purple: #7758bb;
      --teal: #17828e;
      --gray: #6d7785;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--surface);
      line-height: 1.45;
    }}
    header {{
      padding: 28px clamp(18px, 4vw, 48px) 20px;
      background: #ffffff;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(28px, 4vw, 46px);
      letter-spacing: 0;
    }}
    h2 {{ margin: 0 0 14px; font-size: 20px; }}
    h3 {{ margin: 0 0 8px; font-size: 15px; }}
    p {{ margin: 0; color: var(--muted); max-width: 980px; }}
    main {{ padding: 22px clamp(18px, 4vw, 48px) 48px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 18px 0;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px 16px;
      min-width: 0;
    }}
    .metric {{ font-size: 28px; font-weight: 750; }}
    .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }}
    .section {{ margin-top: 20px; }}
    .lanes {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .lane-row {{
      display: grid;
      grid-template-columns: minmax(180px, 1fr) 2fr 90px;
      align-items: center;
      gap: 10px;
      font-size: 13px;
    }}
    .bar {{
      height: 10px;
      background: #edf1f7;
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar > span {{ display: block; height: 100%; background: var(--blue); }}
    .status {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 8px;
      border-radius: 999px;
      background: #e9f6f1;
      color: var(--green);
      font-size: 12px;
      font-weight: 650;
    }}
    .warn {{ background: #fff5df; color: var(--amber); }}
    .blockers {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .blocker strong {{ display: block; margin-bottom: 6px; }}
    .toolbar {{
      display: flex;
      gap: 10px;
      align-items: center;
      margin-bottom: 10px;
    }}
    input, select {{
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      background: #fff;
      color: var(--ink);
      min-height: 36px;
    }}
    input {{ flex: 1; min-width: 200px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      font-size: 13px;
    }}
    th, td {{
      padding: 9px 10px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
      text-align: left;
    }}
    th {{ background: #f0f3f8; font-size: 12px; color: #3f4b5e; }}
    tr:last-child td {{ border-bottom: 0; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; }}
    .timeline {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(26px, 1fr));
      gap: 5px;
    }}
    .dot {{
      height: 22px;
      border-radius: 5px;
      border: 1px solid rgba(0,0,0,.08);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-size: 10px;
      cursor: default;
    }}
    .graph-wrap {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: auto;
    }}
    svg {{ display: block; min-width: 980px; }}
    .node text {{ font-size: 11px; fill: #1b2430; }}
    .node circle {{ stroke: #fff; stroke-width: 2px; }}
    .edge {{ stroke: #aab4c4; stroke-opacity: .35; stroke-width: 1; }}
    .footnote {{ margin-top: 10px; font-size: 12px; color: var(--muted); }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .lanes {{ grid-template-columns: 1fr; }}
      .blockers {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 560px) {{
      .grid {{ grid-template-columns: 1fr; }}
      .toolbar {{ flex-direction: column; align-items: stretch; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>WDSM Lean Formalization Territory</h1>
    <p>Static proof-progress map generated from <code>artifacts/wdsm_formalization_pilot.json</code> and the local WDSM Lean import graph. It is an audit view, not a replacement for Lean checking.</p>
  </header>
  <main>
    <section class="grid" id="metrics"></section>
    <section class="section card">
      <h2>Proof Lanes</h2>
      <div class="lanes" id="lanes"></div>
    </section>
    <section class="section">
      <h2>Open Blockers</h2>
      <div class="blockers" id="blockers"></div>
    </section>
    <section class="section card">
      <h2>Recent Target Timeline</h2>
      <div class="timeline" id="timeline"></div>
      <div class="footnote">Showing the latest 160 target records from the artifact snapshot.</div>
    </section>
    <section class="section">
      <h2>Module Territory Graph</h2>
      <div class="graph-wrap"><svg id="graph" width="1180" height="780" role="img" aria-label="WDSM module territory graph"></svg></div>
      <div class="footnote">Edges are WDSM module imports. Node size reflects proved object count recorded in the target artifact.</div>
    </section>
    <section class="section">
      <h2>Target Explorer</h2>
      <div class="toolbar">
        <input id="search" type="search" placeholder="Search theorem, module, target, or informal source">
        <select id="laneFilter"><option value="">All lanes</option></select>
      </div>
      <table>
        <thead><tr><th>Target</th><th>Lane</th><th>Module</th><th>Objects</th><th>Informal Source</th></tr></thead>
        <tbody id="targetRows"></tbody>
      </table>
    </section>
    <p class="footnote">Generated at {generated}. If this page is viewed through GitHub Pages, it is fully static and requires no server.</p>
  </main>
  <script id="wdsm-data" type="application/json">{payload}</script>
  <script>
    const DATA = JSON.parse(document.getElementById('wdsm-data').textContent);
    const colors = {{
      'deterministic algebra': '#2f65c9',
      'normalized counts': '#17828e',
      'count ratios and shares': '#7758bb',
      'approximation': '#16825d',
      'stochastic interfaces': '#b36b00',
      'variance and Wald': '#ba3a36',
      'reference and gaps': '#6d7785',
      'infrastructure': '#3f4b5e'
    }};
    const $ = (id) => document.getElementById(id);
    function metric(label, value, note, cls='') {{
      return `<div class="card"><div class="label">${{label}}</div><div class="metric">${{value}}</div><p class="${{cls}}">${{note}}</p></div>`;
    }}
    $('metrics').innerHTML = [
      metric('Latest target', DATA.latest_target, DATA.status),
      metric('Target records', DATA.target_count, 'Lean-checked slices in artifact'),
      metric('Proved objects', DATA.proved_object_count, 'Named theorem/definition objects'),
      metric('Root build gate', '<span class="status warn">deferred</span>', DATA.root_lake_build)
    ].join('');
    const maxLane = Math.max(...DATA.lanes.map(l => l.proved_objects), 1);
    $('lanes').innerHTML = DATA.lanes.map(l => {{
      const width = Math.round(100 * l.proved_objects / maxLane);
      return `<div class="lane-row"><strong>${{l.name}}</strong><div class="bar"><span style="width:${{width}}%;background:${{colors[l.name] || '#2f65c9'}}"></span></div><span>${{l.targets}} targets / ${{l.proved_objects}} objs</span></div>`;
    }}).join('');
    $('blockers').innerHTML = DATA.blockers.map(b => `<div class="card blocker"><strong>${{b.name}}</strong><span class="status warn">${{b.status}}</span><p>${{b.lane}}</p></div>`).join('');
    $('timeline').innerHTML = DATA.recent_targets.map(t => `<div class="dot" style="background:${{colors[t.lane] || '#777'}}" title="${{t.label}}: ${{t.lean_module}}">${{t.number}}</div>`).join('');
    const laneFilter = $('laneFilter');
    DATA.lanes.forEach(l => {{
      const opt = document.createElement('option');
      opt.value = l.name;
      opt.textContent = l.name;
      laneFilter.appendChild(opt);
    }});
    function renderRows() {{
      const q = $('search').value.toLowerCase();
      const lane = $('laneFilter').value;
      const rows = DATA.targets.slice().reverse().filter(t => {{
        const hay = [t.label, t.lane, t.lean_module, t.lean_file, t.informal_source, ...(t.proved_objects || [])].join(' ').toLowerCase();
        return (!lane || t.lane === lane) && (!q || hay.includes(q));
      }}).slice(0, 180);
      $('targetRows').innerHTML = rows.map(t => `<tr><td><strong>${{t.label}}</strong><br><code>${{t.verification_status}}</code></td><td><span style="color:${{colors[t.lane] || '#555'}}">${{t.lane}}</span></td><td><code>${{t.lean_module || t.lean_file}}</code></td><td>${{t.proved_count}}<br><code>${{(t.proved_objects || []).slice(0,3).join('<br>')}}${{t.proved_count > 3 ? '<br>...' : ''}}</code></td><td>${{t.informal_source}}</td></tr>`).join('');
    }}
    $('search').addEventListener('input', renderRows);
    laneFilter.addEventListener('change', renderRows);
    renderRows();

    function renderGraph() {{
      const svg = $('graph');
      const nodes = DATA.module_graph.nodes;
      const edges = DATA.module_graph.edges;
      const byLane = {{}};
      nodes.forEach(n => (byLane[n.lane] ||= []).push(n));
      const laneNames = DATA.lanes.map(l => l.name).filter(l => byLane[l]?.length);
      const width = 1180, rowH = 92, marginX = 150, top = 50;
      const height = Math.max(620, top + laneNames.length * rowH + 80);
      svg.setAttribute('height', height);
      const pos = {{}};
      laneNames.forEach((lane, row) => {{
        const arr = byLane[lane].sort((a,b) => (b.proved_count - a.proved_count) || a.id.localeCompare(b.id));
        arr.forEach((n, i) => {{
          const colCount = Math.max(arr.length - 1, 1);
          pos[n.id] = {{
            x: marginX + i * ((width - marginX - 80) / colCount),
            y: top + row * rowH + 34
          }};
        }});
      }});
      let html = '';
      laneNames.forEach((lane, row) => {{
        const y = top + row * rowH + 34;
        html += `<text x="20" y="${{y + 4}}" font-size="12" fill="#657184">${{lane}}</text>`;
        html += `<line x1="150" y1="${{y}}" x2="${{width - 40}}" y2="${{y}}" stroke="#edf1f7"/>`;
      }});
      edges.forEach(e => {{
        if (!pos[e.source] || !pos[e.target]) return;
        const a = pos[e.source], b = pos[e.target];
        html += `<line class="edge" x1="${{a.x}}" y1="${{a.y}}" x2="${{b.x}}" y2="${{b.y}}"/>`;
      }});
      nodes.forEach(n => {{
        if (!pos[n.id]) return;
        const p = pos[n.id];
        const r = 5 + Math.min(16, Math.sqrt(Math.max(n.proved_count, n.target_count, 1)) * 2.2);
        const c = colors[n.lane] || '#777';
        html += `<g class="node"><circle cx="${{p.x}}" cy="${{p.y}}" r="${{r}}" fill="${{c}}"><title>${{n.id}}: ${{n.proved_count}} proved objects, ${{n.target_count}} targets</title></circle><text x="${{p.x + r + 4}}" y="${{p.y + 4}}">${{n.id}}</text></g>`;
      }});
      svg.innerHTML = html;
    }}
    renderGraph();
  </script>
</body>
</html>
"""


def main() -> None:
    data = build_data()
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    HTML_PATH.write_text(render_html(data), encoding="utf-8")
    print(f"wrote {DATA_PATH.relative_to(ROOT)}")
    print(f"wrote {HTML_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
