# File: errorgnomark/src/egm/core/data/hardware/topology_selector.py
"""
Enhanced Chip Resource Selector UI.

Updates:
- [Fix] Edges with 0.0 fidelity are now explicitly ignored during parsing and selection.
"""
from __future__ import annotations

import math
import json
import os
import re
from typing import Dict, List, Optional, Tuple, Set, Union, Any
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.patheffects as import_patheffects
from matplotlib.patches import Circle, Rectangle
from matplotlib.widgets import Button, RadioButtons
from matplotlib.backend_bases import MouseEvent

# ------------------------------------------------
# Constants & Helpers
# ------------------------------------------------

DEFAULT_CHIP = "Baihua"


def _get_hardware_data_dir() -> Path:
    current_file = Path(__file__).resolve()
    d = current_file.parent
    for _ in range(5):
        candidate = d / "core" / "data" / "hardware"
        if candidate.exists():
            return candidate
        d = d.parent
    return Path("src/egm/core/data/hardware").resolve()


def _get_chip_layout_params(chip_name: str, num_qubits: int) -> Dict:
    chip_lower = chip_name.lower()
    if "yudu" in chip_lower or "dongling" in chip_lower:
        layout_type = "diagonal"
        if "dongling" in chip_lower:
            return {"type": layout_type, "rows": 12, "cols": 7}
        else:
            return {"type": layout_type, "rows": 12, "cols": 6}
    elif "baihua" in chip_lower:
        return {"type": "grid", "rows": 12, "cols": 13}
    else:
        sq = int(math.ceil(math.sqrt(num_qubits)))
        return {"type": "grid", "rows": sq, "cols": sq}


def _generate_node_coordinates(layout_type: str, rows: int, cols: int) -> Dict[int, Tuple[float, float]]:
    coords = {}
    if layout_type == "diagonal":
        scale_x = 0.8
        scale_y = 0.8
        for r in range(rows):
            for c in range(cols):
                qid = r * cols + c
                x = (c + r) * scale_x
                y = (r - c) * scale_y
                coords[qid] = (x, -y)
    else:
        for r in range(rows):
            for c in range(cols):
                qid = r * cols + c
                coords[qid] = (float(c), -float(r))
    return coords


def _parse_connectivity_with_values(df: pd.DataFrame) -> Dict[Tuple[int, int], float]:
    """
    Parses connectivity data from DataFrame.
    [UPDATED] Explicitly ignores edges with fidelity <= 0.
    """
    edge_data = {}
    target_col = None

    for col in df.columns:
        c_lower = col.lower()
        if "cz" in c_lower and "fidelity" in c_lower:
            target_col = col;
            break
        if "connectivity" in c_lower:
            target_col = col;
            break

    if not target_col and len(df.columns) > 5:
        target_col = df.columns[5]

    if not target_col: return {}

    print(f"[Parser] Reading edge metrics from: '{target_col}'")

    for idx, row in df.iterrows():
        raw_val = str(row[target_col])
        if not raw_val or raw_val.lower() == 'nan': continue

        lines = re.split(r'[\n;]+', raw_val)
        for line in lines:
            line = line.strip()
            if not line: continue

            val = 0.0
            pair_str = line
            if ':' in line:
                parts = line.split(':')
                pair_str = parts[0].strip()
                try:
                    val = float(parts[1].strip())
                except:
                    val = 0.0

            # [FIX] Ignore invalid edges immediately
            if val <= 1e-6:
                continue

            if '_' in pair_str:
                node_parts = pair_str.split('_')
                if len(node_parts) >= 2:
                    try:
                        u = int(re.sub(r"[^0-9]", "", node_parts[0]))
                        v = int(re.sub(r"[^0-9]", "", node_parts[1]))
                        key = tuple(sorted((u, v)))

                        # Only update if new value is better or key doesn't exist
                        if key not in edge_data or val > edge_data[key]:
                            edge_data[key] = val
                    except ValueError:
                        pass
    return edge_data


def _extract_qubit_metrics(df: pd.DataFrame) -> Dict[int, Dict[str, float]]:
    data = {}
    col_map = {}
    for col in df.columns:
        c = col.lower()
        if 'qubit' in c and 'fidelity' not in c:
            col_map['id'] = col
        elif 't1' in c:
            col_map['T1'] = col
        elif 't2' in c:
            col_map['T2'] = col
        elif 'freq' in c:
            col_map['Freq'] = col
        elif 'fidelity' in c and 'single' in c:
            col_map['Fidelity'] = col

    for idx, row in df.iterrows():
        try:
            if 'id' in col_map:
                qid = int(re.sub(r"[^0-9]", "", str(row[col_map['id']])))
            else:
                qid = int(re.sub(r"[^0-9]", "", str(row.iloc[0])))

            metrics = {}
            for key in ['T1', 'T2', 'Freq', 'Fidelity']:
                val = math.nan
                if key in col_map:
                    try:
                        val = float(row[col_map[key]])
                    except:
                        pass
                metrics[key] = val
            data[qid] = metrics
        except:
            continue
    return data


def _resolve_csv_path(chip_name: str, csv_file_path: Optional[str]) -> Path:
    if csv_file_path:
        p = Path(csv_file_path)
        if not p.exists(): raise FileNotFoundError(f"File not found: {p}")
        return p

    hw_dir = _get_hardware_data_dir()
    chip_dir = hw_dir / chip_name
    if not chip_dir.exists(): raise FileNotFoundError(f"Chip folder not found: {chip_dir}")

    csv_candidates = list(chip_dir.glob("*.csv"))
    if not csv_candidates: raise FileNotFoundError(f"No CSVs in {chip_dir}")

    csv_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return csv_candidates[0]


# ------------------------------------------------
# Modernized UI Class
# ------------------------------------------------

class QubitSelectorUI:
    COLOR_BG = "#F8F9FA"
    COLOR_SELECTION_BORDER = "#FF0044"
    COLOR_TEXT_NORMAL = "#263238"

    # Z-Order Constants
    Z_BG_EDGE = 1
    Z_SEL_EDGE = 10
    Z_NODE = 20
    Z_TEXT = 21
    Z_DRAG = 30

    def __init__(self, node_coords: Dict[int, Tuple[float, float]], qubit_data, edge_data,
                 title, export_prefix, csv_path, save_dir):
        self.node_coords = node_coords
        self.qubit_data = qubit_data
        self.edge_data = edge_data
        self.avail_qubits = set(qubit_data.keys())

        self.title = title
        self.export_prefix = export_prefix
        self.csv_path = csv_path
        self.save_dir = Path(save_dir) if save_dir else Path.cwd()

        self.selected: Set[int] = set()
        self.current_metric = 'T1'
        self.is_dragging = False
        self.press_start = None
        self.drag_rect_patch = None

        self._setup_figure()
        self._prepare_colormaps()
        self._draw_board()

        self.sm = cm.ScalarMappable(norm=self.metric_norms[self.current_metric],
                                    cmap=self.metric_cmaps[self.current_metric])
        self.cbar = self.fig.colorbar(self.sm, cax=self.ax_cbar)

        self._draw_controls()
        self._connect_events()

        self.update_coloring()
        self._update_status()

    def _setup_figure(self):
        xs = [p[0] for p in self.node_coords.values()]
        ys = [p[1] for p in self.node_coords.values()]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        width_span = max_x - min_x + 2
        height_span = max_y - min_y + 2

        scale_factor = 0.6
        base_w = max(13.0, width_span * scale_factor + 4)
        base_h = max(8.0, height_span * scale_factor)

        self.fig = plt.figure(figsize=(base_w, base_h))
        self.fig.patch.set_facecolor(self.COLOR_BG)

        try:
            mng = plt.get_current_fig_manager()
            backend = plt.get_backend().lower()
            if 'tk' in backend:
                if os.name == 'nt':
                    mng.window.state('zoomed')
                else:
                    mng.window.attributes('-zoomed', True)
            elif 'qt' in backend:
                mng.window.showMaximized()
            elif 'wx' in backend:
                mng.frame.Maximize(True)
        except Exception:
            pass

        self.ax = self.fig.add_axes([0.02, 0.15, 0.68, 0.75])
        self.ax.set_facecolor(self.COLOR_BG)
        self.ax.set_aspect("equal")
        self.ax.set_xlim(min_x - 1, max_x + 1)
        self.ax.set_ylim(min_y - 1, max_y + 1)
        self.ax.axis("off")

        self.ax_cbar = self.fig.add_axes([0.65, 0.15, 0.015, 0.75])

        self.fig.suptitle(f"{self.title} Resource Selector", fontsize=20, weight="bold", color="#37474F", x=0.38,
                          y=0.97)

        self.status_text = self.fig.text(
            0.02, 0.02, "Initializing...",
            fontsize=12, color="#455A64", family="monospace", va="bottom",
            bbox=dict(facecolor="white", edgecolor="#CFD8DC", pad=2, boxstyle="round")
        )

    def _prepare_colormaps(self):
        # Only consider positive values for colormap
        cz_vals = [v for v in self.edge_data.values() if v > 0]
        if not cz_vals: cz_vals = [0, 1]
        self.norm_edge = mcolors.Normalize(vmin=min(cz_vals) * 0.9, vmax=1.0)
        self.cmap_edge = plt.get_cmap('GnBu')

        unified_cmap = plt.get_cmap('Blues')
        self.metric_norms = {}
        self.metric_cmaps = {}

        for metric in ['T1', 'T2', 'Freq', 'Fidelity']:
            vals = [d[metric] for d in self.qubit_data.values() if pd.notna(d.get(metric))]
            if vals:
                vmin, vmax = np.percentile(vals, 5), np.percentile(vals, 95)
                self.metric_norms[metric] = mcolors.Normalize(vmin=vmin, vmax=vmax)
            else:
                self.metric_norms[metric] = mcolors.Normalize(0, 1)
            self.metric_cmaps[metric] = unified_cmap

    def _draw_board(self):
        self.line_map = {}
        for (u, v), val in self.edge_data.items():
            if u not in self.node_coords or v not in self.node_coords: continue

            # Double check (though parser should handle it)
            if val <= 0: continue

            pos_u = self.node_coords[u]
            pos_v = self.node_coords[v]

            color = self.cmap_edge(self.norm_edge(val))
            ln, = self.ax.plot([pos_u[0], pos_v[0]], [pos_u[1], pos_v[1]],
                               color=color, lw=3, zorder=self.Z_BG_EDGE, solid_capstyle='round')
            self.line_map[(u, v)] = ln

        self.circle_map = {}
        self.text_map = {}

        for qid, pos in self.node_coords.items():
            is_avail = qid in self.avail_qubits
            radius = 0.38

            if is_avail:
                circle = Circle(pos, radius, edgecolor="#555", linewidth=1, zorder=self.Z_NODE)
                self.ax.add_patch(circle)
                self.circle_map[qid] = circle

                txt = self.ax.text(pos[0], pos[1], str(qid), ha="center", va="center",
                                   fontsize=9, color="black", weight="bold", zorder=self.Z_TEXT)
                self.text_map[qid] = txt

    def _draw_controls(self):
        panel_left = 0.77
        panel_width = 0.21

        ax_radio = self.fig.add_axes([panel_left, 0.70, panel_width, 0.20], facecolor="#E3F2FD")
        ax_radio.text(0.5, 1.08, "Select Data View", transform=ax_radio.transAxes,
                      ha='center', va='bottom', fontsize=14, weight='bold', color="#1565C0")

        labels = ('T1', 'T2', 'Fidelity', 'Freq')
        self.radio = RadioButtons(ax_radio, labels, active=0)

        for p in ax_radio.patches:
            if isinstance(p, Circle):
                p.set_radius(0.08)
                p.set_edgecolor("#1565C0")
                p.set_facecolor("#BBDEFB")

        if hasattr(self.radio, 'labels'):
            for lbl in self.radio.labels:
                lbl.set_fontsize(13)
                lbl.set_weight('bold')
                lbl.set_color("#37474F")

        def change_metric(label):
            key = label.split()[0]
            self.current_metric = key
            self.update_coloring()
            self.fig.canvas.draw_idle()

        self.radio.on_clicked(change_metric)

        info_text = (
            "HOW TO USE:\n"
            "• Click node to Select\n"
            "• Drag to Box Select\n"
            "• [A] Select All\n"
            "• [C] Clear All\n"
            "• [S] Save Data"
        )
        self.fig.text(panel_left, 0.65, info_text, fontsize=11, family="sans-serif", color="#455A64", va="top",
                      linespacing=1.8)

        btn_h = 0.06
        btn_w = panel_width
        gap = 0.07
        start_y = 0.32

        def make_btn(y, label, color, hover, cb):
            ax = self.fig.add_axes([panel_left, y, btn_w, btn_h])
            b = Button(ax, label, color=color, hovercolor=hover)
            b.label.set_fontsize(11)
            b.label.set_weight('bold')
            b.on_clicked(cb)
            return b

        self.btn_all = make_btn(start_y, "Select All", "#FFF", "#E1F5FE", lambda e: self.select_all(True))
        self.btn_clr = make_btn(start_y - gap, "Clear", "#FFF", "#FFEBEE", lambda e: self.select_all(False))
        self.btn_save = make_btn(start_y - gap * 2, "Export", "#E0F7FA", "#B2EBF2", lambda e: self.export_selection())
        self.btn_done = make_btn(start_y - gap * 3, "DONE", "#29B6F6", "#0288D1", lambda e: plt.close(self.fig))
        self.btn_done.label.set_color("white")

    def _connect_events(self):
        self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_drag)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)

    def update_coloring(self):
        metric_key = self.current_metric
        norm = self.metric_norms.get(metric_key)
        cmap = self.metric_cmaps.get(metric_key)

        self.sm.set_norm(norm)
        self.sm.set_cmap(cmap)
        self.cbar.update_normal(self.sm)
        self.cbar.set_label(metric_key, fontsize=11, weight='bold')

        for qid, circle in self.circle_map.items():
            val = self.qubit_data[qid].get(metric_key, math.nan)

            if pd.isna(val):
                face_c = "#B0BEC5"
                text_c = "black"
            else:
                rgba = cmap(norm(val))
                face_c = rgba
                lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
                text_c = "white" if lum < 0.6 else "black"

            if qid in self.selected:
                edge_c = self.COLOR_SELECTION_BORDER
                lw = 4.0
                self.text_map[qid].set_path_effects([
                    import_patheffects.withStroke(linewidth=2.5, foreground=self.COLOR_SELECTION_BORDER)
                ])
            else:
                edge_c = "#607D8B"
                lw = 1.0
                self.text_map[qid].set_path_effects([])

            circle.set_facecolor(face_c)
            circle.set_edgecolor(edge_c)
            circle.set_linewidth(lw)
            self.text_map[qid].set_color(text_c)

        for (u, v), ln in self.line_map.items():
            if u in self.selected and v in self.selected:
                ln.set_linewidth(4.5)
                ln.set_path_effects(
                    [import_patheffects.withStroke(linewidth=6.5, foreground=self.COLOR_SELECTION_BORDER)])
                ln.set_zorder(self.Z_SEL_EDGE)
            else:
                ln.set_linewidth(3.0)
                ln.set_path_effects([])
                ln.set_zorder(self.Z_BG_EDGE)

        self.fig.canvas.draw_idle()

    def _update_status(self):
        n_q = len(self.selected)
        n_e = sum(1 for (u, v) in self.line_map if u in self.selected and v in self.selected)

        vals = [self.qubit_data[q].get(self.current_metric) for q in self.selected]
        vals = [v for v in vals if pd.notna(v)]

        if vals:
            avg_str = f"Avg {self.current_metric}: {np.mean(vals):.2f}"
            min_str = f"Min: {np.min(vals):.2f}"
            max_str = f"Max: {np.max(vals):.2f}"
            stats = f" | {avg_str} [{min_str}, {max_str}]"
        else:
            stats = ""

        self.status_text.set_text(f"► Selected: {n_q} Qubits, {n_e} Edges{stats}")

    def select_all(self, enable=True):
        if enable:
            self.selected = set(self.avail_qubits)
        else:
            self.selected.clear()
        self.update_coloring()
        self._update_status()

    def toggle_qubit(self, qid):
        if qid not in self.avail_qubits: return
        if qid in self.selected:
            self.selected.remove(qid)
        else:
            self.selected.add(qid)

    def on_press(self, event: MouseEvent):
        if event.inaxes != self.ax or event.button != 1: return
        self.is_dragging = True
        self.press_start = (event.xdata, event.ydata)
        if self.drag_rect_patch: self.drag_rect_patch.remove()
        self.drag_rect_patch = Rectangle(self.press_start, 0, 0, facecolor=self.COLOR_SELECTION_BORDER, alpha=0.2,
                                         zorder=self.Z_DRAG)
        self.ax.add_patch(self.drag_rect_patch)
        self.fig.canvas.draw_idle()

    def on_drag(self, event: MouseEvent):
        if not self.is_dragging or event.inaxes != self.ax: return
        x0, y0 = self.press_start
        self.drag_rect_patch.set_width(event.xdata - x0)
        self.drag_rect_patch.set_height(event.ydata - y0)
        self.drag_rect_patch.set_xy((x0, y0))
        self.fig.canvas.draw_idle()

    def on_release(self, event: MouseEvent):
        if not self.is_dragging: return
        self.is_dragging = False
        if self.drag_rect_patch:
            self.drag_rect_patch.remove()
            self.drag_rect_patch = None
        if event.inaxes != self.ax: return

        x0, y0 = self.press_start
        x1, y1 = event.xdata, event.ydata

        xmin, xmax = sorted([x0, x1])
        ymin, ymax = sorted([y0, y1])

        is_click = (xmax - xmin) < 0.2 and (ymax - ymin) < 0.2
        click_radius_sq = 0.4 ** 2

        for qid, pos in self.node_coords.items():
            if qid not in self.avail_qubits: continue
            px, py = pos
            if is_click:
                dist_sq = (px - x1) ** 2 + (py - y1) ** 2
                if dist_sq < click_radius_sq:
                    self.toggle_qubit(qid)
            else:
                if xmin <= px <= xmax and ymin <= py <= ymax:
                    self.toggle_qubit(qid)

        self.update_coloring()
        self._update_status()

    def on_key(self, event):
        if event.key == 'a':
            self.select_all(True)
        elif event.key == 'c':
            self.select_all(False)
        elif event.key == 's':
            self.export_selection()
        elif event.key in ['q', 'enter']:
            plt.close(self.fig)

    def export_selection(self):
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        prefix = self.export_prefix or 'selection'
        if not self.save_dir.exists(): self.save_dir.mkdir(parents=True, exist_ok=True)

        # [UPDATED] Filter out edges with 0 fidelity again during export to be safe
        valid_edges = []
        for (u, v), val in self.edge_data.items():
            if u in self.selected and v in self.selected and val > 0:
                valid_edges.append((u, v))

        data = {
            'chip_name': self.title,
            'chosen_qubits': sorted(list(self.selected)),
            'chosen_connectivity': valid_edges,
            'csv_file_path': str(self.csv_path),
            'timestamp': stamp
        }
        with open(self.save_dir / f"{prefix}-{stamp}.json", 'w') as f:
            json.dump(data, f, indent=2)
        self.fig.savefig(self.save_dir / f"{prefix}-{stamp}.png", dpi=150, bbox_inches='tight')
        print(f"[UI] Exported to {self.save_dir}")


# ------------------------------------------------
# Main Entry Point
# ------------------------------------------------

def interactive_select_resources(
        chip_name: Optional[str] = None,
        csv_file_path: Optional[str] = None,
        *,
        title: Optional[str] = None,
        export_prefix: Optional[str] = None,
        save_dir: Optional[Union[str, Path]] = None
) -> Tuple[List[int], List[Tuple[int, int]], bool]:
    if not chip_name and not csv_file_path: chip_name = DEFAULT_CHIP

    try:
        if chip_name:
            csv_path = _resolve_csv_path(chip_name, csv_file_path)
            display_title = title or chip_name
        else:
            csv_path = Path(csv_file_path)
            display_title = title or csv_path.stem

        print(f"[Loader] Reading: {csv_path.name}")
        df = pd.read_csv(csv_path)

        edge_data = _parse_connectivity_with_values(df)
        qubit_data = _extract_qubit_metrics(df)

        print(f"[Loader] Qubits: {len(qubit_data)} | Couplers: {len(edge_data)}")

        layout_cfg = _get_chip_layout_params(chip_name or csv_path.stem, len(qubit_data))
        node_coords = _generate_node_coordinates(layout_cfg['type'], layout_cfg['rows'], layout_cfg['cols'])

    except FileNotFoundError as e:
        print(f"[Warning] {e}")
        qubit_data = {i: {'T1': 30.0, 'T2': 30.0, 'Freq': 5.0, 'Fidelity': 0.99} for i in range(12 * 13)}
        edge_data = {}
        csv_path = None
        display_title = "Synthetic Grid"
        export_prefix = "synthetic"
        node_coords = _generate_node_coordinates("grid", 12, 13)

    ui = QubitSelectorUI(
        node_coords, qubit_data, edge_data,
        title=display_title,
        export_prefix=export_prefix or csv_path.stem if csv_path else "export",
        csv_path=csv_path,
        save_dir=save_dir
    )

    plt.show()

    chosen_qubits = sorted(list(ui.selected))

    # [UPDATED] Filter edges during return as well
    chosen_connectivity = []
    for (u, v), val in ui.edge_data.items():
        if u in ui.selected and v in ui.selected and val > 0:
            chosen_connectivity.append((u, v))

    return chosen_qubits, chosen_connectivity, False


if __name__ == "__main__":
    qs, conns, _ = interactive_select_resources(chip_name='Baihua')
    print(f"Result: {len(qs)} qubits, {len(conns)} edges.")