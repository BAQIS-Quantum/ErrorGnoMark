# File: errorgnomark/examples/benchmark_gui.py
"""
EGM Benchmark GUI (UX Optimized)

Updates:
- [UX] 'Interleaved Gate' input is now hidden by default and only appears when IRB is selected.
- [Validation] Added pre-flight check to ensure Interleaved Gate arity matches the experiment scope (1Q vs 2Q).
- [Validation] Added warning when using a 2Q Interleaved Gate with 'Respective' mode.
"""
import os
import sys
import json
import re
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
from uuid import uuid4
import numpy as np


# ------------------------------------------------
# Dynamic Import Setup
# ------------------------------------------------
def setup_path():
    current_path = Path(__file__).resolve()
    # Go up 3 levels: server -> egm -> src
    src_root = current_path.parents[2]
    if str(src_root) not in sys.path:
        sys.path.append(str(src_root))


setup_path()

try:
    from egm.core.data.hardware.topology_selector import interactive_select_resources, _get_chip_layout_params, \
        _generate_node_coordinates

    # --- Modular RB Imports ---
    from egm.core.experiments.benchmarking.rb import (
        gen_respectively_circuits,
        gen_simultaneously_circuits,
        AVAILABLE_NATIVE_GATES
    )
    from egm.core.analysis.rb import (
        analyze_rb_standard,
        analyze_rb_simultaneous,
        calculate_epg
    )
    from egm.core.circuits.native_gates import STANDARD_NATIVE_GATES
    from egm.core.circuits.circuit import Gate

    from egm.core.engine.executor import QuantumEngine
    from egm.core.backends.dummy_backend import DummyBackend
    from egm.schemas.results.rb import RBAnalysisResult
    from egm.reporting.generators.html_generator import HTMLReportGenerator
    from egm.reporting.dashboard_generator import HTMLDashboard
    import egm
except ImportError as e:
    print(f"[Critical Error] Import failed: {e}")
    sys.exit(1)

# ------------------------------------------------
# Constants for Validation
# ------------------------------------------------
GATES_1Q = {'x', 'y', 'z', 'h', 's', 'sdg', 't', 'tdg', 'sx', 'rx', 'ry', 'rz'}
GATES_2Q = {'cx', 'cy', 'cz', 'cnot', 'swap', 'iswap'}


# ------------------------------------------------
# GUI Application
# ------------------------------------------------

class TaskInitializerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EGM Task Initializer (Full Features)")
        self.root.geometry("1000x950")
        self.root.resizable(True, True)

        # --- Style Configuration ---
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.FONT_BODY = ('Segoe UI', 11)
        self.FONT_BOLD = ('Segoe UI', 11, 'bold')
        self.FONT_HEAD = ('Segoe UI', 12, 'bold')
        self.FONT_BTN = ('Segoe UI', 11, 'bold')

        self.COL_BG_HW = "#E1F5FE"
        self.COL_BG_SCH = "#F3E5F5"
        self.COL_BG_CIRC = "#E0F2F1"
        self.COL_BG_ACT = "#ECEFF1"
        self.COL_BG_LOG = "#FAFAFA"

        self.style.configure('Hw.TLabelframe', background=self.COL_BG_HW)
        self.style.configure('Hw.TLabelframe.Label', background=self.COL_BG_HW, font=self.FONT_HEAD,
                             foreground="#0277BD")
        self.style.configure('Hw.TFrame', background=self.COL_BG_HW)

        self.style.configure('Sch.TLabelframe', background=self.COL_BG_SCH)
        self.style.configure('Sch.TLabelframe.Label', background=self.COL_BG_SCH, font=self.FONT_HEAD,
                             foreground="#7B1FA2")
        self.style.configure('Sch.TFrame', background=self.COL_BG_SCH)

        self.style.configure('Circ.TLabelframe', background=self.COL_BG_CIRC)
        self.style.configure('Circ.TLabelframe.Label', background=self.COL_BG_CIRC, font=self.FONT_HEAD,
                             foreground="#00695C")
        self.style.configure('Circ.TFrame', background=self.COL_BG_CIRC)

        self.style.configure('Act.TFrame', background=self.COL_BG_ACT)
        self.style.configure('Log.TLabelframe', background=self.COL_BG_LOG)
        self.style.configure('Log.TLabelframe.Label', background=self.COL_BG_LOG, font=self.FONT_HEAD)

        self.style.configure('TLabel', font=self.FONT_BODY)
        self.style.configure('TRadiobutton', font=self.FONT_BODY)

        self.selected_qubits = []
        self.selected_edges = []
        self.last_report_path = None
        self.cached_circuits = {}
        self.cached_tasks_meta = []

        # --- UI Construction ---
        self.main_paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.frame_left = ttk.Frame(self.main_paned)
        self.frame_right = ttk.Frame(self.main_paned)

        self.main_paned.add(self.frame_left, weight=1)
        self.main_paned.add(self.frame_right, weight=1)

        self._init_vars()
        self._build_hardware_frame()
        self._build_scheme_frame()
        self._build_circuit_frame()
        self._build_actions_frame()
        self._build_log_frame()

        self.frame_bottom = ttk.Frame(root)
        self.frame_bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        self.progress = ttk.Progressbar(self.frame_bottom, orient="horizontal", mode="determinate")
        self.progress.pack(side=tk.TOP, fill=tk.X, pady=2)

        self.status_var = tk.StringVar(value="Ready. Select a chip to begin.")
        tk.Label(self.frame_bottom, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W,
                 font=('Segoe UI', 10)).pack(side=tk.TOP, fill=tk.X)

    def _init_vars(self):
        self.var_chip = tk.StringVar(value="Baihua")
        self.var_res_status = tk.StringVar(value="No topology selected")
        self.var_scheme = tk.StringVar(value="Standard Randomized Benchmarking")
        self.schemes = ["Standard Randomized Benchmarking", "Interleaved Randomized Benchmarking"]
        self.var_depths = tk.StringVar(value="2, 4, 8, 16, 32, 64")
        self.var_k = tk.IntVar(value=20)
        self.var_shots = tk.IntVar(value=1024)
        self.var_seed = tk.StringVar(value="42")
        self.var_same_struct = tk.BooleanVar(value=True)
        self.var_native_gates = tk.StringVar(value="None")
        self.var_exec_mode = tk.StringVar(value="Respective")
        self.var_run_1q = tk.BooleanVar(value=True)
        self.var_run_2q = tk.BooleanVar(value=True)
        self.var_run_multi = tk.BooleanVar(value=False)
        self.var_target_gate = tk.StringVar(value="x")

    def _build_hardware_frame(self):
        frame = ttk.LabelFrame(self.frame_left, text=" 1. Hardware & Resources ", padding=15, style='Hw.TLabelframe')
        frame.pack(fill="x", padx=10, pady=5)

        f_chip = ttk.Frame(frame, style='Hw.TFrame')
        f_chip.pack(fill="x", pady=5)

        ttk.Label(f_chip, text="Chip Name:", font=self.FONT_BOLD, background=self.COL_BG_HW).pack(side="left")
        ttk.Combobox(f_chip, textvariable=self.var_chip, values=["Baihua", "Yudu", "Dongling"], state="readonly",
                     font=self.FONT_BODY).pack(side="left", expand=True, fill="x", padx=5)

        tk.Button(frame, text="⚡ Open Topology Selector", command=self.open_resource_selector,
                  bg="#673AB7", fg="white", font=self.FONT_BTN, relief="raised").pack(fill="x", pady=8)

        ttk.Label(frame, textvariable=self.var_res_status, foreground="#D32F2F", font=("Consolas", 10, "bold"),
                  background=self.COL_BG_HW).pack(anchor="w")

    def _build_scheme_frame(self):
        frame = ttk.LabelFrame(self.frame_left, text=" 2. QCVV Scheme ", padding=15, style='Sch.TLabelframe')
        frame.pack(fill="x", padx=10, pady=5)

        f_row = ttk.Frame(frame, style='Sch.TFrame')
        f_row.pack(fill="x")

        ttk.Label(f_row, text="Method:", font=self.FONT_BOLD, background=self.COL_BG_SCH).pack(side="left")

        def on_scheme_change(event):
            scheme = self.var_scheme.get()
            if "Interleaved" in scheme:
                # Show gate input
                self.lbl_gate.grid()
                self.entry_gate.grid()
                self.entry_gate.config(state="normal")
            else:
                # Hide gate input
                self.lbl_gate.grid_remove()
                self.entry_gate.grid_remove()
                self.entry_gate.config(state="disabled")

        cb = ttk.Combobox(f_row, textvariable=self.var_scheme, values=self.schemes, state="readonly", width=35,
                          font=self.FONT_BODY)
        cb.pack(side="left", padx=5)
        cb.bind("<<ComboboxSelected>>", on_scheme_change)

    def _build_circuit_frame(self):
        frame = ttk.LabelFrame(self.frame_left, text=" 3. Circuit Parameters ", padding=15, style='Circ.TLabelframe')
        frame.pack(fill="x", padx=10, pady=5)

        def add_row(label, variable, row):
            l = ttk.Label(frame, text=label, background=self.COL_BG_CIRC)
            l.grid(row=row, column=0, sticky="w", pady=5)
            e = ttk.Entry(frame, textvariable=variable, font=self.FONT_BODY)
            e.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
            return l, e

        frame.columnconfigure(1, weight=1)
        add_row("Depths (List):", self.var_depths, 0)
        add_row("Circuits/Depth (K):", self.var_k, 1)
        add_row("Shots:", self.var_shots, 2)
        add_row("Random Seed:", self.var_seed, 3)

        # [UX] Gate Input (initially hidden)
        self.lbl_gate, self.entry_gate = add_row("Interleaved Gate:", self.var_target_gate, 4)
        self.lbl_gate.grid_remove()
        self.entry_gate.grid_remove()

        ttk.Separator(frame, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(frame, text="Methodology:", font=self.FONT_BOLD, background=self.COL_BG_CIRC).grid(row=6, column=0,
                                                                                                     sticky="w")
        f_mode = ttk.Frame(frame, style='Circ.TFrame')
        f_mode.grid(row=6, column=1, sticky="w")
        style_radio = ttk.Style()
        style_radio.configure('Circ.TRadiobutton', background=self.COL_BG_CIRC, font=self.FONT_BODY)
        ttk.Radiobutton(f_mode, text="Respectively (Isolated)", variable=self.var_exec_mode, value="Respective",
                        style='Circ.TRadiobutton').pack(side="left", padx=5)
        ttk.Radiobutton(f_mode, text="Simultaneously", variable=self.var_exec_mode, value="Simultaneous",
                        style='Circ.TRadiobutton').pack(side="left", padx=5)

        def create_native_chk(parent, text, var, state="normal"):
            return tk.Checkbutton(parent, text=text, variable=var,
                                  bg=self.COL_BG_CIRC, activebackground=self.COL_BG_CIRC,
                                  selectcolor="white", anchor="w", font=self.FONT_BODY, state=state)

        ttk.Label(frame, text="Experiment Type:", font=self.FONT_BOLD, background=self.COL_BG_CIRC).grid(row=7,
                                                                                                         column=0,
                                                                                                         sticky="w")
        f_scope = ttk.Frame(frame, style='Circ.TFrame')
        f_scope.grid(row=7, column=1, sticky="w")
        create_native_chk(f_scope, "Single-Qubit", self.var_run_1q).pack(side="left", padx=5)
        create_native_chk(f_scope, "Two-Qubit", self.var_run_2q).pack(side="left", padx=5)
        create_native_chk(f_scope, "Multi-Qubit", self.var_run_multi, state="disabled").pack(side="left", padx=5)

        chk_frame = ttk.Frame(frame, style='Circ.TFrame')
        chk_frame.grid(row=8, column=0, columnspan=2, sticky="w", pady=5)
        create_native_chk(chk_frame, "Same Circuit Structure per Qubit", self.var_same_struct).pack(anchor="w")

        # Native Gate Combobox
        f_gate = ttk.Frame(frame, style='Circ.TFrame')
        f_gate.grid(row=9, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Label(f_gate, text="Native Gate Set:", font=self.FONT_BODY, background=self.COL_BG_CIRC).pack(side="left")

        gate_options = ["None"] + AVAILABLE_NATIVE_GATES
        gate_combo = ttk.Combobox(f_gate, textvariable=self.var_native_gates, values=gate_options,
                                  state="readonly", width=15, font=self.FONT_BODY)
        gate_combo.pack(side="left", padx=10)

    def _build_actions_frame(self):
        frame = ttk.Frame(self.frame_left, padding=15, style='Act.TFrame')
        frame.pack(fill="x", padx=10, pady=10)

        f_circs = ttk.Frame(frame, style='Act.TFrame')
        f_circs.pack(fill="x", pady=5)

        tk.Button(f_circs, text="Generate Circuits Only", command=self.generate_circuits_only,
                  bg="#1976D2", fg="white", font=self.FONT_BTN, relief="flat").pack(side="left", fill="x", expand=True,
                                                                                    padx=2)

        self.btn_save_circs = tk.Button(f_circs, text="Save Circuits...", command=self.save_circuits, state="disabled",
                                        bg="#607D8B", fg="white", font=self.FONT_BTN, relief="flat")
        self.btn_save_circs.pack(side="left", fill="x", expand=True, padx=2)

        tk.Button(frame, text="Save Config to JSON...", command=self.save_to_json,
                  bg="#546E7A", fg="white", font=self.FONT_BTN, relief="flat").pack(fill="x", pady=5)

        tk.Button(frame, text="▶ RUN EXPERIMENT & GENERATE REPORT", command=self.run_experiment,
                  bg="#2E7D32", fg="white", font=('Segoe UI', 12, 'bold'), relief="raised", height=2).pack(fill="x",
                                                                                                           pady=10)

        self.btn_open_html = tk.Button(frame, text="🌐 Open Report in Browser", command=self.open_in_browser,
                                       state="disabled",
                                       bg="#00838F", fg="white", font=self.FONT_BTN, relief="flat")
        self.btn_open_html.pack(fill="x")

    def _build_log_frame(self):
        frame = ttk.LabelFrame(self.frame_right, text=" Execution Log ", padding=10, style='Log.TLabelframe')
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = tk.Text(frame, height=20, width=40, font=("Consolas", 10), state="disabled", bg="white",
                                fg="#333")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def log(self, message):
        ts = datetime.now().strftime("[%H:%M:%S]")
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"{ts} {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.root.update_idletasks()

    # ------------------------------------------------
    # Logic
    # ------------------------------------------------

    def open_resource_selector(self):
        chip = self.var_chip.get()
        self.log(f"Opening selector for {chip}...")
        try:
            qubits, edges, synthetic = interactive_select_resources(chip_name=chip, title=f"Select Resources")
            self.selected_qubits = qubits
            self.selected_edges = edges
            self.var_res_status.set(f"✔ Selected: {len(qubits)} Qubits, {len(edges)} Edges")
            self.log(f"Resources selected: {len(qubits)} qubits, {len(edges)} edges.")
        except Exception as e:
            messagebox.showerror("Selector Error", str(e))

    def _collect_config(self):
        try:
            raw_d = self.var_depths.get()
            depths = [int(x.strip()) for x in raw_d.split(',') if x.strip().isdigit()]
            if not depths: raise ValueError("Invalid depths list")

            gate_selection = self.var_native_gates.get()

            return {
                "meta": {"timestamp": datetime.now().isoformat(), "chip": self.var_chip.get(),
                         "scheme": self.var_scheme.get(), "mode": self.var_exec_mode.get()},
                "resources": {"qubits": self.selected_qubits, "connectivity": self.selected_edges},
                "circuit_params": {
                    "depths": depths, "circuits_per_depth": self.var_k.get(), "shots": self.var_shots.get(),
                    "seed": int(self.var_seed.get()) if self.var_seed.get() else 42,
                    "same_per_qubit": self.var_same_struct.get(),
                    "native_gate_set": gate_selection,
                    "target_gate": self.var_target_gate.get().strip().lower()
                }
            }
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return None

    def _prepare_tasks_modular(self, cfg):
        mode = cfg['meta']['mode']
        qubits = cfg['resources']['qubits']
        edges = cfg['resources']['connectivity']
        tasks = []

        do_1q = self.var_run_1q.get()
        do_2q = self.var_run_2q.get()

        if mode == "Respective":
            if do_1q and qubits:
                groups_1q = [[q] for q in qubits]
                tasks.append((groups_1q, "1Q_Respective_Batch", "1q_respective"))

            if do_2q and edges:
                groups_2q = [list(e) for e in edges]
                tasks.append((groups_2q, "2Q_Respective_Batch", "2q_respective"))

        else:  # Simultaneous
            if do_1q and qubits:
                groups_1q = [[q] for q in qubits]
                tasks.append((groups_1q, "1Q_Simultaneous_All", "1q_simultaneous"))

            if do_2q and edges:
                groups_2q = [list(e) for e in edges]
                tasks.append((groups_2q, "2Q_Simultaneous_All", "2q_simultaneous"))

        return tasks

    def _run_generator_with_retry(self, generator_func, gate_config, **kwargs):
        running_config = gate_config
        if running_config == "None":
            return generator_func(native_gates=None, **kwargs), "None"

        while True:
            try:
                return generator_func(native_gates=running_config, **kwargs), running_config
            except ValueError as e:
                msg = str(e)
                if "No decomposition for gate" in msg:
                    match = re.search(r"gate '([^']+)'", msg)
                    if match:
                        missing_gate = match.group(1)
                        user_choice = messagebox.askyesno(
                            "Decomposition Rule Missing",
                            f"Gate '{missing_gate}' missing in basis '{running_config}'.\n"
                            f"Treat '{missing_gate}' as Native (raw)?"
                        )
                        if user_choice:
                            if isinstance(running_config, str):
                                key = running_config.lower()
                                if key in STANDARD_NATIVE_GATES:
                                    running_config = list(STANDARD_NATIVE_GATES[key])
                                else:
                                    running_config = []
                            if missing_gate not in running_config:
                                running_config.append(missing_gate)
                                self.log(f"⚠ Added '{missing_gate}' to allowlist.")
                            continue
                raise e

    def generate_circuits_only(self):
        cfg = self._collect_config()
        if not cfg: return

        # Basic Check
        if not self.var_run_1q.get() and not self.var_run_2q.get() and not self.var_run_multi.get():
            messagebox.showwarning("Scope Error", "Please select at least one Run Scope.")
            return

        if not cfg['resources']['qubits'] and not cfg['resources']['connectivity']:
            messagebox.showwarning("No Resources", "Select resources first.")
            return

        params = cfg['circuit_params']
        is_irb = "Interleaved" in cfg['meta']['scheme']
        target_gate_name = params['target_gate']

        # --- [VALIDATION] Check Interleaved Gate Logic ---
        if is_irb:
            run_1q = self.var_run_1q.get()
            run_2q = self.var_run_2q.get()
            exec_mode = self.var_exec_mode.get()  # Get selected mode: Respective/Simultaneous

            is_1q_gate = target_gate_name in GATES_1Q
            is_2q_gate = target_gate_name in GATES_2Q

            # Check 1: Arity Mismatch (Experiment Scope vs Gate)
            error_msg = None
            if run_1q and not is_1q_gate:
                error_msg = f"You selected '1Q Tasks' but gate '{target_gate_name}' is not a known 1-qubit gate."
            elif run_2q and not is_2q_gate:
                error_msg = f"You selected '2Q Tasks' but gate '{target_gate_name}' is not a known 2-qubit gate."

            if error_msg:
                # Add helpful hint
                if run_2q and is_1q_gate:
                    error_msg += "\n\nFor 2Q IRB, please use a gate like 'cz', 'cx' or 'cnot'."

                # Show warning but allow override (for custom gates)
                if not messagebox.askyesno("Gate Mismatch Warning", f"{error_msg}\n\nDo you want to proceed anyway?"):
                    return

            # Check 2: 2Q Gate with Respective Mode
            # Warning that Respective 2Q IRB is unusual (Simultaneous usually preferred for crosstalk)
            if is_2q_gate and exec_mode == "Respective":
                warn_msg = (f"You selected a 2-Qubit Gate '{target_gate_name}' with 'Respective' (Isolated) mode.\n\n"
                            "Calibrating 2Q gates often requires 'Simultaneous' mode to account for crosstalk.\n\n"
                            "Do you really want to run in Respective mode?")
                if not messagebox.askyesno("Methodology Warning", warn_msg):
                    return

        self.log("Generating circuits using Modular API...")
        self.cached_circuits = {}
        self.cached_tasks_meta = []

        try:
            tasks = self._prepare_tasks_modular(cfg)
            if not tasks:
                self.log("No tasks generated.")
                return

            active_gate_config = params.get('native_gate_set', 'None')

            for groups_list, label, mode_key in tasks:
                self.log(f"Generating batch: {label} ({len(groups_list)} groups)...")

                gen_kwargs = {
                    "qubit_groups": groups_list,
                    "depths": params['depths'],
                    "circuits_per_depth": params['circuits_per_depth'],
                    "same_per_qubit": params['same_per_qubit'],
                    "seed": params['seed']
                }

                target_func = None
                if "respective" in mode_key:
                    target_func = gen_respectively_circuits
                elif "simultaneous" in mode_key:
                    target_func = gen_simultaneously_circuits

                # 1. Reference
                self.log(f"  > Generating Reference Batch...")
                ref_obj, active_gate_config = self._run_generator_with_retry(
                    target_func, active_gate_config, interleaved_gate=None, **gen_kwargs
                )
                self.cached_circuits[f"{label}_REF"] = ref_obj

                # 2. Interleaved (if selected)
                if is_irb:
                    self.log(f"  > Generating Interleaved Batch (Gate: {target_gate_name})...")
                    arity = 1 if "1q" in mode_key else 2
                    gate_obj = Gate(target_gate_name, qubits=tuple(range(arity)))

                    int_obj, active_gate_config = self._run_generator_with_retry(
                        target_func, active_gate_config, interleaved_gate=gate_obj, **gen_kwargs
                    )
                    self.cached_circuits[f"{label}_INT"] = int_obj

                    self.cached_tasks_meta.append({
                        "groups": groups_list,
                        "label": label,
                        "mode": mode_key,
                        "type": "IRB",
                        "gate_name": target_gate_name
                    })
                else:
                    self.cached_tasks_meta.append({
                        "groups": groups_list,
                        "label": label,
                        "mode": mode_key,
                        "type": "Standard"
                    })

            self.log(f"Generation complete. Batch sets cached.")
            self.btn_save_circs.config(state="normal", bg="#1565C0")
            messagebox.showinfo("Success", "Circuits generated and cached.\nReady to Run or Save.")

        except Exception as e:
            # traceback.print_exc()
            self.log(f"Error generating circuits: {e}")
            messagebox.showerror("Error", str(e))

    def save_circuits(self):
        if not self.cached_circuits: return
        target_dir = filedialog.askdirectory(title="Select Directory to Save Circuits")
        if not target_dir: return
        path = Path(target_dir)
        self.log(f"Saving circuits to {path}...")

        try:
            for label, data_obj in self.cached_circuits.items():
                task_dir = path / label
                task_dir.mkdir(exist_ok=True, parents=True)

                flat_circuits = []
                first_key = next(iter(data_obj.keys()))

                # Respective: Dict[GroupTuple, Dict[Depth, List]]
                if isinstance(first_key, tuple):
                    for group_tuple, depth_map in data_obj.items():
                        g_str = "_".join(map(str, group_tuple))
                        for d, qcs in depth_map.items():
                            for i, qc in enumerate(qcs):
                                flat_circuits.append((f"G{g_str}_d{d}_i{i}", qc))
                # Simultaneous: Dict[Depth, List]
                else:
                    for d, qcs in data_obj.items():
                        for i, qc in enumerate(qcs):
                            flat_circuits.append((f"Simul_d{d}_i{i}", qc))

                for name, qc in flat_circuits:
                    with open(task_dir / f"{name}.txt", "w", encoding="utf-8") as f:
                        try:
                            import io
                            from contextlib import redirect_stdout
                            f_str = io.StringIO()
                            with redirect_stdout(f_str):
                                qc.draw("text")
                            f.write(f_str.getvalue())
                        except:
                            f.write(str(qc))

                    json_data = {"qubits": qc.qubits,
                                 "gates": [{"name": g.name, "qubits": g.qubits, "params": [str(p) for p in g.params]}
                                           for g in qc.gates]}
                    with open(task_dir / f"{name}.json", "w") as f:
                        json.dump(json_data, f, indent=2)

            self.log("Circuits saved successfully.")
            messagebox.showinfo("Saved", f"Circuits saved to {target_dir}")
        except Exception as e:
            self.log(f"Error saving: {e}")
            messagebox.showerror("Save Error", str(e))

    def save_to_json(self):
        cfg = self._collect_config()
        if cfg:
            path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
            if path:
                with open(path, 'w') as f: json.dump(cfg, f, indent=4)
                self.log(f"Configuration saved to {path}")

    def open_in_browser(self):
        if self.last_report_path and os.path.exists(self.last_report_path):
            webbrowser.open(f"file://{os.path.abspath(self.last_report_path)}")
        else:
            messagebox.showerror("Error", "Report file not found.")

    def _create_progress_popup(self, title="Running Experiment"):
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("450x180")
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 225
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 90
        popup.geometry(f"+{x}+{y}")
        popup.transient(self.root)
        popup.grab_set()
        f_main = ttk.Frame(popup, padding=20)
        f_main.pack(fill=tk.BOTH, expand=True)
        lbl_status = ttk.Label(f_main, text="Initializing...", font=('Segoe UI', 11), wraplength=400)
        lbl_status.pack(pady=(0, 10), fill=tk.X)
        pbar = ttk.Progressbar(f_main, orient="horizontal", mode="determinate")
        pbar.pack(fill=tk.X, pady=10)
        lbl_detail = ttk.Label(f_main, text="Starting engine...", font=('Segoe UI', 9), foreground="gray")
        lbl_detail.pack(anchor=tk.W)
        return popup, pbar, lbl_status, lbl_detail

    def run_experiment(self):
        cfg = self._collect_config()
        if not cfg: return

        if not self.var_run_1q.get() and not self.var_run_2q.get() and not self.var_run_multi.get():
            messagebox.showwarning("Scope Error", "Please select at least one Run Scope.")
            return

        self.log("Waiting for output directory selection...")
        selected_dir = filedialog.askdirectory(title="Select Output Directory for Report")
        output_dir = Path(selected_dir) if selected_dir else Path("reports_gui")
        self.log(f"Output directory: {output_dir}")

        popup, pbar, lbl_status, lbl_detail = self._create_progress_popup()
        self.root.update()

        stats_1q_epc = []
        stats_2q_epc = []

        try:
            lbl_status.config(text="Setting up Quantum Engine...")
            popup.update()
            backend = DummyBackend()
            engine = QuantumEngine(backend=backend)

            lbl_detail.config(text="Configuring Report Dashboard...")
            popup.update()
            package_root = Path(egm.__file__).parent
            template_path = package_root / "reporting" / "templates" / "html"
            html_gen = HTMLReportGenerator(template_dir=template_path)
            dashboard = HTMLDashboard(html_gen, output_dir=output_dir, title=f"EGM Report - {cfg['meta']['chip']}")

            chip_name = cfg['meta']['chip']
            layout_info = _get_chip_layout_params(chip_name, 200)
            coords = _generate_node_coordinates(layout_info['type'], layout_info['rows'], layout_info['cols'])
            dashboard.set_topology(qubits=cfg['resources']['qubits'], edges=cfg['resources']['connectivity'],
                                   node_coords=coords)
            dashboard.set_device_name(cfg['meta']['chip'])

            if not self.cached_tasks_meta:
                messagebox.showerror("Flow Error", "Please click 'Generate Circuits Only' before running.")
                popup.destroy()
                return

            total_steps = len(self.cached_tasks_meta)
            pbar['maximum'] = total_steps

            for idx, task in enumerate(self.cached_tasks_meta):
                label = task['label']
                mode = task['mode']
                groups = task['groups']
                task_type = task.get("type", "Standard")

                msg = f"Running Task {idx + 1}/{total_steps}: {label} ({task_type})"
                self.log(msg)
                lbl_status.config(text=msg)
                popup.update()

                # --- Execution Helper ---
                def execute_and_analyze(data_obj, dashboard_mode):
                    """Helper to execute batch and return fit results"""
                    try:
                        if "respective" in mode:
                            fits = []
                            for group_tuple, depth_map in data_obj.items():
                                g_list = list(group_tuple)
                                flat = []
                                for d in sorted(depth_map.keys()): flat.extend(depth_map[d])

                                batch = engine.execute_with_ideal(flat, shots=cfg['circuit_params']['shots'])
                                cnts = [r[1] for r in batch]

                                fit = analyze_rb_standard(cnts, flat)  # [API Update] No num_qubits
                                fits.append(fit)
                            return fits

                        elif "simultaneous" in mode:
                            flat = []
                            for d in sorted(data_obj.keys()): flat.extend(data_obj[d])
                            batch = engine.execute_with_ideal(flat, shots=cfg['circuit_params']['shots'])
                            cnts = [r[1] for r in batch]

                            fit_dict = analyze_rb_simultaneous(cnts, flat, groups)  # [API Update] No plot
                            return list(fit_dict.values())
                        return []
                    except ValueError as e:
                        if "mismatch in its core dimension" in str(e):
                            self.log(f"⚠ Skipping {label}: Dimension mismatch (applied 2Q gate to 1Q task?).")
                        else:
                            self.log(f"⚠ Error executing {label}: {e}")
                        return []

                lbl_detail.config(text="Executing circuits...")
                popup.update()

                if task_type == "Standard":
                    ref_data = self.cached_circuits[f"{label}_REF"]
                    dash_mode = "respective" if "respective" in mode else "simultaneous"
                    results = execute_and_analyze(ref_data, dash_mode)

                    dashboard.add_experiments(results, mode=dash_mode)

                    for res in results:
                        if res.success:
                            p_val = next((p.value for p in res.fit.params if p.name == 'p'), None)
                            if p_val is not None:
                                nq = len(res.qubits)
                                d = 2 ** nq
                                epc = ((d - 1) / d) * (1 - p_val)
                                if nq == 1:
                                    stats_1q_epc.append(epc)
                                elif nq == 2:
                                    stats_2q_epc.append(epc)

                elif task_type == "IRB":
                    gate_name = task.get("gate_name", "U")
                    lbl_detail.config(text=f"IRB: Executing Reference & Interleaved ({gate_name})...")
                    popup.update()

                    ref_data = self.cached_circuits[f"{label}_REF"]
                    fits_ref = execute_and_analyze(ref_data, mode)

                    int_data = self.cached_circuits[f"{label}_INT"]
                    fits_int = execute_and_analyze(int_data, mode)

                    if len(fits_ref) == len(fits_int):
                        for f_r, f_i in zip(fits_ref, fits_int):
                            dashboard.add_experiments([f_r], mode=f"{mode}_ref")

                            if f_r.success and f_i.success:
                                p_ref = next(p.value for p in f_r.fit.params if p.name == 'p')
                                p_int = next(p.value for p in f_i.fit.params if p.name == 'p')
                                epg = calculate_epg(p_ref, p_int, len(f_r.qubits))

                                self.log(f"  > IRB Result {f_r.qubits}: EPG({gate_name}) = {epg:.4e}")

                                f_i.notes = f"IRB Gate: {gate_name} | EPG: {epg:.4e}"
                                f_i.tags.append("IRB_Result")
                                dashboard.add_irb_result(f_i, epg, mode=mode)

                            else:
                                self.log(f"  > IRB Fit Failed for {f_r.qubits}")
                    else:
                        self.log("⚠ IRB Error: Mismatch in reference vs interleaved results count.")

                pbar['value'] = idx + 1
                popup.update()

            lbl_status.config(text="Saving Report...")
            lbl_detail.config(text="Rendering HTML dashboard...")
            popup.update()

            median_1q = float(np.median(stats_1q_epc)) if stats_1q_epc else None
            median_2q = float(np.median(stats_2q_epc)) if stats_2q_epc else None
            dashboard.set_performance_metrics(
                device_name=cfg['meta']['chip'],
                median_1q=median_1q,
                median_2q=median_2q
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"RB_Modular_Results_{timestamp}.html"
            report_path = dashboard.save(filename)

            self.last_report_path = report_path
            self.log(f"Success! Report saved: {report_path}")
            self.status_var.set("Experiment Finished.")
            self.btn_open_html.config(state="normal", bg="#00838F")
            popup.destroy()
            messagebox.showinfo("Success", f"Experiment Finished.\nReport: {report_path}")

        except Exception as e:
            popup.destroy()
            import traceback
            traceback.print_exc()
            self.log(f"ERROR: {e}")
            messagebox.showerror("Execution Error", f"Failed to run experiment:\n{e}")
            self.status_var.set("Error during execution.")


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskInitializerApp(root)
    root.mainloop()