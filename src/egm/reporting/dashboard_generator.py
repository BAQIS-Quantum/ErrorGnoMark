# File: errorgnomark/reporting/dashboard_generator.py
# ---------------------------------------------------------------------
# Module: Dashboard Generator (Debug Enhanced)
# ---------------------------------------------------------------------
# Fixes:
# - [CRITICAL] Removed silent try-except in 'save()' to show why reports fail.
# - Updated 'add_irb_result' to correctly categorize Simultaneous IRB.
# ---------------------------------------------------------------------

import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
from egm.schemas.results.base import BaseAnalysisResult
from egm.reporting.generators.html_generator import HTMLReportGenerator

# Setup logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


class HTMLDashboard:
    def __init__(self,
                 generator: HTMLReportGenerator,
                 output_dir: str = "reports",
                 title: str = "ErrorGnoMark Analysis Dashboard"):
        self.generator = generator
        self.output_dir = Path(output_dir)
        self.title = title

        self.results_tree = {"1Q": [], "2Q": [], "Others": []}
        self.report_map = {}

        # Topology Data
        self.topology = {
            "qubits": [],
            "edges": [],
            "node_coords": None
        }

        # Metrics Data Storage
        self.metric_data = {
            "device": "Unknown Device",
            "qubit_count": 0,
            # Standard RB EPCs
            "rb_1q_iso": [], "rb_1q_sim": [],
            "rb_2q_iso": [], "rb_2q_sim": [],
            # Interleaved RB EPGs
            "irb_1q_iso": [], "irb_1q_sim": [],
            "irb_2q_iso": [], "irb_2q_sim": []
        }

        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)

        # (CSS Omitted for brevity - keeps existing style)
        self.style = """
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; display: flex; height: 100vh; background-color: #f8f9fa; overflow: hidden; }
            * { box-sizing: border-box; }
            .sidebar { width: 280px; background-color: #2c3e50; color: #ecf0f1; display: flex; flex-direction: column; flex-shrink: 0; z-index: 20; box-shadow: 2px 0 5px rgba(0,0,0,0.1); }
            .sidebar-header { padding: 20px; border-bottom: 1px solid #34495e; background: #233140; }
            .sidebar-content { flex: 1; overflow-y: auto; padding: 10px 0; }
            .nav-group-title { padding: 10px 20px; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; color: #7f8c8d; margin-top: 10px; }
            .nav-item { padding: 8px 20px; cursor: pointer; border-left: 3px solid transparent; font-size: 0.9rem; color: #bdc3c7; transition: 0.2s; }
            .nav-item:hover { background-color: #34495e; color: #fff; }
            .nav-item.active { background-color: #2980b9; color: #fff; border-left-color: #3498db; }
            .main-content { flex: 1; position: relative; display: flex; flex-direction: column; background: #fff; }
            #topology-view { position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; flex-direction: column; background: #f4f6f8; z-index: 10; overflow-y: auto; }
            .dash-header { background: white; padding: 20px 40px; border-bottom: 1px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
            .dash-title h1 { margin: 0; font-size: 1.5rem; color: #2c3e50; }
            .dash-meta { display: flex; gap: 30px; font-size: 0.95rem; color: #546e7a; margin-top: 15px; }
            .meta-item b { color: #2c3e50; font-weight: 600; }
            .topo-body { flex: 1; display: flex; flex-direction: row; align-items: flex-start; justify-content: center; gap: 40px; padding: 40px; flex-wrap: wrap; }
            .map-wrapper { display: flex; flex-direction: column; align-items: center; gap: 15px; }
            .chip-container { position: relative; background: white; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); transition: transform 0.2s; border: 1px solid #eceff1; }
            svg.connections { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
            line.edge { stroke: #eceff1; stroke-width: 2; pointer-events: none; }
            line.edge.has-report { stroke: #90caf9; stroke-width: 4; pointer-events: auto; cursor: pointer; transition: all 0.2s; }
            line.edge.has-report:hover { stroke: #2196f3; stroke-width: 6; }
            .qubit-node { position: absolute; width: 28px; height: 28px; border-radius: 50%; background: #fff; border: 2px solid #cfd8dc; display: flex; align-items: center; justify-content: center; color: #b0bec5; font-size: 0.7rem; font-weight: bold; cursor: default; z-index: 2; transform: translate(-50%, -50%); transition: all 0.2s; }
            .qubit-node.has-report { background: #e3f2fd; border-color: #2196f3; color: #1565c0; cursor: pointer; box-shadow: 0 2px 5px rgba(33, 150, 243, 0.3); }
            .qubit-node.has-report:hover { background: #2196f3; color: white; transform: translate(-50%, -50%) scale(1.15); z-index: 10; }
            .spec-sheet { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); width: 600px; border: 1px solid #eceff1; }
            .spec-header { font-size: 1.1rem; font-weight: bold; margin-bottom: 15px; color: #2c3e50; border-bottom: 2px solid #2196f3; padding-bottom: 10px; display: inline-block; }
            .spec-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
            .spec-table th { text-align: left; padding: 10px; background-color: #f8f9fa; color: #546e7a; font-weight: 600; border-bottom: 2px solid #eceff1; }
            .spec-table td { padding: 10px; border-bottom: 1px solid #f1f2f6; color: #37474f; }
            .spec-table tr:last-child td { border-bottom: none; }
            .spec-section-row td { background-color: #eceff1; font-weight: bold; font-size: 0.85rem; padding: 6px 10px; color: #455a64; }
            .unit-col { color: #90a4ae; font-size: 0.85rem; }
            iframe.report-frame { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; background: white; z-index: 5; display: none; }
            .top-bar { height: 50px; background: white; border-bottom: 1px solid #eee; display: flex; align-items: center; padding: 0 20px; z-index: 20; justify-content: space-between; }
            .btn-back { padding: 6px 15px; border-radius: 20px; background: #e3f2fd; color: #1565c0; cursor: pointer; display: none; font-weight: 600; font-size: 0.9rem; }
            .btn-back:hover { background: #bbdefb; }
        """

        self.script = """
            var reportMap = {};
            function showTopology() {
                document.getElementById('topology-view').style.display = 'flex';
                document.getElementById('report-frame').style.display = 'none';
                document.getElementById('btn-back').style.display = 'none';
            }
            function loadReport(path, elementId) {
                document.getElementById('topology-view').style.display = 'none';
                var frame = document.getElementById('report-frame');
                frame.src = path;
                frame.style.display = 'block';
                document.getElementById('btn-back').style.display = 'block';
            }
            function onNodeClick(qubitsStr) {
                var reports = reportMap[qubitsStr];
                if (reports && reports.length > 0) {
                    loadReport(reports[reports.length-1].path, reports[reports.length-1].elemId);
                }
            }
        """

    def set_topology(self, qubits, edges, node_coords=None):
        self.topology["qubits"] = sorted(qubits)
        self.topology["edges"] = sorted([tuple(sorted(e)) for e in edges])
        self.topology["node_coords"] = node_coords
        self.metric_data["qubit_count"] = len(qubits)

    def set_device_name(self, name: str):
        self.metric_data["device"] = name

    def set_performance_metrics(self, device_name: str, median_1q: float, median_2q: float):
        """Legacy compatibility hook."""
        self.metric_data["device"] = device_name
        pass

    def add_experiments(self, results: List[BaseAnalysisResult], mode: str = "respective"):
        for res in results:
            nq = getattr(res, 'num_qubits', len(res.qubits))
            name = getattr(res, 'name', 'Experiment')
            res_id = str(getattr(res, "result_id", getattr(res, "id", "unknown")))

            cat = "1Q" if nq == 1 else "2Q" if nq == 2 else "Others"
            q_key = str(sorted(res.qubits))

            mode_label = "(Sim)" if "simultaneous" in mode.lower() else ""
            label = f"{name} {res.qubits} {mode_label}"

            if cat not in self.results_tree: self.results_tree[cat] = []

            entry = {'label': label, 'qubits': res.qubits, 'result': res, 'id': res_id, 'elem_id': f"nav-{res_id}"}
            self.results_tree[cat].append(entry)

            if q_key not in self.report_map: self.report_map[q_key] = []
            self.report_map[q_key].append(entry)

            # Metric Collection for Standard RB
            if res.success and "IRB" not in name:
                p_val = next((param.value for param in res.fit.params if param.name == 'p'), None)
                if p_val is not None:
                    d = 2 ** nq
                    epc = ((d - 1) / d) * (1 - p_val)
                    if nq == 1:
                        if "sim" in mode.lower():
                            self.metric_data["rb_1q_sim"].append(epc)
                        else:
                            self.metric_data["rb_1q_iso"].append(epc)
                    elif nq == 2:
                        if "sim" in mode.lower():
                            self.metric_data["rb_2q_sim"].append(epc)
                        else:
                            self.metric_data["rb_2q_iso"].append(epc)

    def add_irb_result(self, result: BaseAnalysisResult, epg: float, mode: str = "respective"):
        """
        Registers an IRB result and its EPG.
        [UPDATED] Now accepts 'mode' to correctly categorize Simultaneous IRB.
        """
        # Add to navigation tree
        self.add_experiments([result], mode="irb")

        # Store EPG Metric
        nq = len(result.qubits)
        is_sim = "simultaneous" in mode.lower() or "sim" in mode.lower()

        if nq == 1:
            target = self.metric_data["irb_1q_sim"] if is_sim else self.metric_data["irb_1q_iso"]
            target.append(epg)
        elif nq == 2:
            target = self.metric_data["irb_2q_sim"] if is_sim else self.metric_data["irb_2q_iso"]
            target.append(epg)

    def _generate_sidebar(self) -> str:
        html = '<div class="sidebar"><div class="sidebar-header"><h3>📊 Analysis DB</h3></div><div class="sidebar-content"><div class="nav-item" onclick="showTopology()">🏠 <b>Topology Overview</b></div>'
        for cat in ["1Q", "2Q", "Others"]:
            items = self.results_tree.get(cat, [])
            if not items: continue
            html += f'<div class="nav-group-title">{cat} Benchmarks</div>'
            for item in items:
                rel_path = item.get('path', '#')
                display_label = item['label']
                html += f'<div id="{item["elem_id"]}" class="nav-item" onclick="loadReport(\'{rel_path}\', \'{item["elem_id"]}\')"><div>{display_label}</div><span class="meta" style="font-size:0.7em; opacity:0.6">{item["id"][:6]}</span></div>'
        html += "</div></div>"
        return html

    def _generate_topology_html(self) -> str:
        node_coords = self.topology.get("node_coords")
        if not node_coords: return "<div>No coordinates available.</div>"

        xs = [p[0] for p in node_coords.values()]
        ys = [p[1] for p in node_coords.values()]
        if not xs: return ""

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        padding = 40
        scale = 50
        width = (max_x - min_x) * scale + (padding * 2)
        height = (max_y - min_y) * scale + (padding * 2)

        def transform(pos):
            tx = (pos[0] - min_x) * scale + padding
            ty = (pos[1] - min_y) * scale + padding
            return tx, height - ty

        html = f'<div class="chip-container" style="width:{width}px; height:{height}px;">'
        html += f'<svg class="connections" viewBox="0 0 {width} {height}">'

        for (u, v) in self.topology["edges"]:
            if u not in node_coords or v not in node_coords: continue
            x1, y1 = transform(node_coords[u])
            x2, y2 = transform(node_coords[v])
            key = str(sorted([u, v]))
            has_report = key in self.report_map
            cls = "edge has-report" if has_report else "edge"
            onclick = f"onclick=\"onNodeClick('{key}')\"" if has_report else ""
            html += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}" {onclick} />'

        html += '</svg>'

        for qid, pos in node_coords.items():
            x, y = transform(pos)
            key = str([qid])
            has_report = key in self.report_map
            cls = "qubit-node has-report" if has_report else "qubit-node"
            onclick = f"onclick=\"onNodeClick('{key}')\"" if has_report else ""
            html += f'<div class="{cls}" style="left:{x}px; top:{y}px;" {onclick}>{qid}</div>'

        html += '</div>'
        return html

    def _generate_spec_table(self) -> str:
        m = self.metric_data

        def fmt(val_list):
            if not val_list: return None
            return f"{np.median(val_list):.2e}"

        def create_row(title, iso_list, sim_list, units, fig):
            med_iso = fmt(iso_list)
            med_sim = fmt(sim_list)

            mode_str = ""
            val_str = ""
            if med_iso and med_sim:
                mode_str = "Iso. / Sim."
                val_str = f"{med_iso} / {med_sim}"
            elif med_iso:
                mode_str = "Iso."
                val_str = med_iso
            elif med_sim:
                mode_str = "Sim."
                val_str = med_sim
            else:
                return ""

            return f"""<tr>
                <td>{title}</td>
                <td style="text-align:center">{mode_str}</td>
                <td><b>{val_str}</b></td>
                <td>-</td>
                <td class="unit-col">{units}</td>
                <td style="font-family:monospace; font-size:0.8em; color:#78909c">{fig}</td>
            </tr>"""

        r_1q = create_row("1Q Standard RB (EPC)", m["rb_1q_iso"], m["rb_1q_sim"], "infidelity", "rb_1q")
        r_1q_irb = create_row("1Q Interleaved RB (EPG)", m["irb_1q_iso"], m["irb_1q_sim"], "infidelity", "irb_1q")

        r_2q = create_row("2Q Standard RB (EPC)", m["rb_2q_iso"], m["rb_2q_sim"], "EPC proxy", "rb_2q")
        r_2q_irb = create_row("2Q Interleaved RB (EPG)", m["irb_2q_iso"], m["irb_2q_sim"], "infidelity", "irb_2q")

        html = f"""
        <div class="spec-sheet">
            <div class="spec-header">Core Performance Metrics</div>
            <table class="spec-table">
                <thead>
                    <tr>
                        <th>Test Suite</th>
                        <th style="text-align:center">Mode</th>
                        <th>Median</th>
                        <th>Mean</th>
                        <th>Units</th>
                        <th>Source</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="spec-section-row"><td colspan="6">Single-Qubit Benchmarks</td></tr>
                    {r_1q if r_1q else '<tr><td colspan="6" style="text-align:center;color:#ccc">No Data</td></tr>'}
                    {r_1q_irb}

                    <tr class="spec-section-row"><td colspan="6">Two-Qubit Benchmarks</td></tr>
                    {r_2q if r_2q else '<tr><td colspan="6" style="text-align:center;color:#ccc">No Data</td></tr>'}
                    {r_2q_irb}
                </tbody>
            </table>
        </div>
        """
        return html

    def save(self, filename: str = "index.html") -> str:
        if not filename.endswith('.html'): filename += '.html'

        details_dir = self.output_dir / "details"
        details_dir.mkdir(exist_ok=True, parents=True)

        # [CRITICAL UPDATE] Removed try-except to show errors
        for cat, items in self.results_tree.items():
            for item in items:
                res = item['result']
                report_filename = f"report_{item['id']}.html"
                item['path'] = f"details/{report_filename}"

                # Now if this fails, we will see the traceback!
                self.generator.generate_rb_report(res, details_dir / report_filename)

        js_map = {}
        for key, items in self.report_map.items():
            js_map[key] = [{'id': i['id'], 'path': i['path'], 'elemId': i['elem_id']} for i in items]
        js_inject = f"reportMap = {json.dumps(js_map)};"

        topo_html = self._generate_topology_html()
        table_html = self._generate_spec_table()

        m = self.metric_data

        def get_stat(iso, sim, irb):
            vals = iso + sim + irb
            return f"{np.median(vals):.2e}" if vals else "N/A"

        med_1q = get_stat(m["rb_1q_iso"], m["rb_1q_sim"], m["irb_1q_iso"] + m["irb_1q_sim"])
        med_2q = get_stat(m["rb_2q_iso"], m["rb_2q_sim"], m["irb_2q_iso"] + m["irb_2q_sim"])

        header_html = f"""
        <div class="dash-header">
            <div class="dash-title">
                <h1>{m['device']} Performance Specification Sheet</h1>
                <div style="font-size:0.85rem; color:#90a4ae; margin-top:5px;">Generated by ErrorGnoMark (EGM v2.0)</div>
            </div>
            <div class="dash-meta">
                <div class="meta-item">Device: <b>{m['device']}</b></div>
                <div class="meta-item">Qubits: <b>{m['qubit_count']}</b></div>
                <div class="meta-item">Median 1Q Error: <b style="color:#e91e63">{med_1q}</b></div>
                <div class="meta-item">Median 2Q Error: <b style="color:#9c27b0">{med_2q}</b></div>
                <div class="meta-item">Date: <b>{datetime.now().strftime('%b %d, %Y')}</b></div>
            </div>
        </div>
        """

        html_content = f"""<!DOCTYPE html>
        <html>
        <head>
            <title>{self.title}</title>
            <style>{self.style}</style>
            <script>{self.script}{js_inject}</script>
        </head>
        <body>
            {self._generate_sidebar()}
            <div class="main-content">
                <div class="top-bar">
                    <span style="font-weight:bold; color:#2c3e50;">Topology Overview</span>
                    <div id="btn-back" class="btn-back" onclick="showTopology()">← Back to Overview</div>
                </div>

                <div id="topology-view">
                    {header_html}
                    <div class="topo-body">
                        <div class="map-wrapper">
                            {topo_html}
                            <div style="font-size:0.8rem; color:#b0bec5; margin-top:10px;">Interactive Map: Click Blue Nodes/Edges</div>
                        </div>
                        {table_html}
                    </div>
                </div>
                <iframe id="report-frame" class="report-frame"></iframe>
            </div>
        </body>
        </html>"""

        full_path = self.output_dir / filename
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return str(full_path)