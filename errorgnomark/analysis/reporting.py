# File Path: errorgnomark/analysis/reporting.py
# [UPDATED - Added MRB plotting methods to ExcelReport]

import os
import io
import numpy as np
from typing import List, Dict, Any, Union, Tuple
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.axes_grid1 import make_axes_locatable

try:
    from openpyxl import Workbook
    from openpyxl.utils import get_column_letter
    from openpyxl.drawing.image import Image as OpenpyxlImage
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
except ImportError:
    print("Warning: 'openpyxl' library not found. Excel reporting will be unavailable.")
    Workbook = None

from .result import ExperimentResult
from .mrb import _mrb_decay_func # Import the decay function for plotting

# --- Tomography Plotting Function ---
def plot_density_matrix(rho: np.ndarray, title: str = "Density Matrix"):
    # ... (code from previous response, no changes needed here)
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise ValueError("Input rho must be a square 2D array.")
    dim = rho.shape[0]
    num_qubits = int(np.log2(dim))
    tick_labels = [format(i, f'0{num_qubits}b') for i in range(dim)]
    fig = plt.figure(figsize=(14, 6))
    fig.suptitle(title, fontsize=16)
    max_z = np.max(np.abs(rho)) if np.max(np.abs(rho)) > 0 else 1.0
    ax_real = fig.add_subplot(1, 2, 1, projection='3d')
    x, y = np.meshgrid(np.arange(dim), np.arange(dim))
    ax_real.bar3d(x.ravel(), y.ravel(), 0, 0.8, 0.8, np.real(rho).ravel(), shade=True)
    ax_real.set_title("Real Part")
    ax_real.set_zlim(-max_z, max_z)
    ax_real.set_xticks(np.arange(dim), tick_labels)
    ax_real.set_yticks(np.arange(dim), tick_labels)
    ax_imag = fig.add_subplot(1, 2, 2, projection='3d')
    ax_imag.bar3d(x.ravel(), y.ravel(), 0, 0.8, 0.8, np.imag(rho).ravel(), shade=True)
    ax_imag.set_title("Imaginary Part")
    ax_imag.set_zlim(-max_z, max_z)
    ax_imag.set_xticks(np.arange(dim), tick_labels)
    ax_imag.set_yticks(np.arange(dim), tick_labels)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    return fig

# --- Console Report Function ---
def generate_report(results: List[ExperimentResult]):
    # ... (code from previous response, no changes needed here)
    print("\n" + "="*50 + "\n" + " " * 15 + "ANALYSIS REPORT" + "\n" + "="*50)
    for i, result in enumerate(results):
        print(f"\n--- Result Set {i+1}: {result.name} ---")
        if "epc" in result.data: # MRB Decay Report
            epc = result.data.get('epc')
            epc_err = result.data.get('epc_err')
            print(f"  Qubit Group: {result.data.get('group')}")
            print(f"  Error Per Clifford (EPC): {epc:.3e} ± {epc_err:.2e}" if epc is not None else "Fit Failed")
        elif "reconstructed_rho" in result.data: # Tomography Report
            fidelity = result.data.get('fidelity_with_ideal')
            purity = result.data.get('purity')
            trace = result.data.get('trace')
            if fidelity is not None: print(f"  Fidelity with Ideal State: {fidelity:.4f}")
            if purity is not None: print(f"  Purity of Reconstructed State: {purity:.4f}")
            if trace is not None: print(f"  Trace of Reconstructed Matrix: {trace:.4f}")
        elif "avg_polarizations" in result.data: # MRB Direct Report
            print("  (See Excel report for heatmap visualization)")
    print("\n" + "="*50)

# --- Excel Report Class ---
if Workbook:
    class ExcelReport:
        def __init__(self, output_dir: str = "."):
            # ... (code from previous response, no changes needed here)
            self.workbook = Workbook()
            self.workbook.remove(self.workbook.active)
            self.output_dir = output_dir
            os.makedirs(self.output_dir, exist_ok=True)
            self._header_font = Font(bold=True, color="FFFFFF")
            self._header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
            self._center_align = Alignment(horizontal="center", vertical="center")
            self._thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

        def _apply_header_style(self, cell):
            cell.font, cell.fill, cell.alignment, cell.border = self._header_font, self._header_fill, self._center_align, self._thin_border
        
        def _save_fig_to_sheet(self, fig: plt.Figure, sheet_name: str):
            ws = self.workbook.create_sheet(title=sheet_name)
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight')
            plt.close(fig)
            img_buffer.seek(0)
            img = OpenpyxlImage(img_buffer)
            ws.add_image(img, 'A1')

        # --- Tomography Methods ---
        def create_summary_sheet(self, analysis_results: List[ExperimentResult], experiment_params: Dict[str, Any]):
            # ... (code from previous response, no changes needed here)
            ws = self.workbook.create_sheet(title="Summary")
            ws.cell(row=1, column=1, value="Experiment Parameters").font = Font(bold=True, size=14)
            row_idx = 2
            for key, value in experiment_params.items():
                ws.cell(row=row_idx, column=1, value=key).font = Font(bold=True)
                ws.cell(row=row_idx, column=2, value=str(value)); row_idx += 1
            row_idx += 1
            ws.cell(row=row_idx, column=1, value="Analysis Results").font = Font(bold=True, size=14); row_idx += 1
            
            # Dynamic headers based on results
            headers = ["Name"]
            has_tomo = any("fidelity_with_ideal" in r.data for r in analysis_results)
            has_mrb = any("epc" in r.data for r in analysis_results)
            if has_tomo: headers.extend(["Fidelity", "Purity", "Trace"])
            if has_mrb: headers.extend(["Qubit Group", "EPC", "EPC Error"])
            
            for col_idx, header in enumerate(headers, 1): self._apply_header_style(ws.cell(row=row_idx, column=col_idx, value=header))

            for result in analysis_results:
                if "avg_polarizations" in result.data: continue # Skip heatmap data in summary
                row_idx += 1
                ws.cell(row=row_idx, column=1, value=result.name).border = self._thin_border
                col_idx = 2
                if has_tomo and "fidelity_with_ideal" in result.data:
                    ws.cell(row=row_idx, column=col_idx, value=f"{result.data.get('fidelity_with_ideal', 'N/A'):.4f}").border = self._thin_border; col_idx+=1
                    ws.cell(row=row_idx, column=col_idx, value=f"{result.data.get('purity', 'N/A'):.4f}").border = self._thin_border; col_idx+=1
                    ws.cell(row=row_idx, column=col_idx, value=f"{result.data.get('trace', 'N/A'):.4f}").border = self._thin_border; col_idx+=1
                if has_mrb and "epc" in result.data:
                    ws.cell(row=row_idx, column=col_idx, value=str(result.data.get('group', 'N/A'))).border = self._thin_border; col_idx+=1
                    ws.cell(row=row_idx, column=col_idx, value=f"{result.data.get('epc', 'N/A'):.3e}").border = self._thin_border; col_idx+=1
                    ws.cell(row=row_idx, column=col_idx, value=f"{result.data.get('epc_err', 'N/A'):.2e}").border = self._thin_border; col_idx+=1

            self._auto_fit_columns(ws)
            return self
        
        def add_counts_sheet(self, raw_counts_by_basis: Dict[str, Dict[str, int]], sheet_name: str = "Detailed Counts"):
            # ... (code from previous response, no changes needed here)
            ws = self.workbook.create_sheet(title=sheet_name)
            all_outcomes = sorted(list(set(outcome for counts in raw_counts_by_basis.values() for outcome in counts.keys())))
            headers = ["Basis"] + [f"Count '{outcome}'" for outcome in all_outcomes]
            for col_idx, header in enumerate(headers, 1): self._apply_header_style(ws.cell(row=1, column=col_idx, value=header))
            for row_idx, basis in enumerate(sorted(raw_counts_by_basis.keys()), 2):
                counts_dict = raw_counts_by_basis[basis]
                ws.cell(row=row_idx, column=1, value=basis).border = self._thin_border
                for i, outcome in enumerate(all_outcomes):
                    cell = ws.cell(row=row_idx, column=2 + i, value=counts_dict.get(outcome, 0))
                    cell.border = self._thin_border
            self._auto_fit_columns(ws)
            return self

        def add_probabilities_sheet(self, raw_counts_by_basis: Dict[str, Dict[str, int]], sheet_name: str = "Detailed Probabilities"):
            # ... (code from previous response, no changes needed here)
            ws = self.workbook.create_sheet(title=sheet_name)
            all_outcomes = sorted(list(set(outcome for counts in raw_counts_by_basis.values() for outcome in counts.keys())))
            headers = ["Basis"] + [f"Prob. '{outcome}'" for outcome in all_outcomes]
            for col_idx, header in enumerate(headers, 1): self._apply_header_style(ws.cell(row=1, column=col_idx, value=header))
            for row_idx, basis in enumerate(sorted(raw_counts_by_basis.keys()), 2):
                counts_dict = raw_counts_by_basis[basis]
                total_shots = sum(counts_dict.values())
                ws.cell(row=row_idx, column=1, value=basis).border = self._thin_border
                for i, outcome in enumerate(all_outcomes):
                    prob = counts_dict.get(outcome, 0) / total_shots if total_shots > 0 else 0
                    cell = ws.cell(row=row_idx, column=2 + i, value=prob)
                    cell.border = self._thin_border
                    cell.number_format = '0.000000'
            self._auto_fit_columns(ws)
            return self

        def add_density_matrix_plot(self, rho: np.ndarray, sheet_name: str = "Density Matrix Plot"):
            fig = plot_density_matrix(rho, title=sheet_name)
            self._save_fig_to_sheet(fig, sheet_name)
            return self

        # =========================================================================
        # [NEW METHODS] For MRB Reporting
        # =========================================================================
        def add_mrb_decay_plot(self, result: ExperimentResult):
            """Adds a worksheet with the MRB decay curve plot."""
            fit_results = result.data['fit_params']
            survival_data = result.data['raw_data']
            num_qubits = result.data['num_qubits']
            group = result.data['group']
            
            fig, ax = plt.subplots(figsize=(10, 6))
            depths = np.array(sorted(survival_data.keys()))
            mean_survivals = np.array([np.mean(survival_data[d]) for d in depths])
            std_survivals = np.array([np.std(survival_data[d]) / np.sqrt(len(survival_data[d])) for d in depths])

            ax.errorbar(depths, mean_survivals, yerr=std_survivals, fmt='o', capsize=5, label='Mean Survival Probability')

            if fit_results['fit_successful']:
                plot_depths = np.linspace(0, max(depths), 200)
                A, p, B = fit_results['params']
                ax.plot(plot_depths, _mrb_decay_func(plot_depths, A, p, B), 'r-', 
                         label=f'Fit: $F = A \\cdot p^m + B$\n'
                               f'$p$ = {p:.4f}\n'
                               f'EPC = {result.data["epc"]:.2e}')

            ax.set_xlabel("Clifford Sequence Depth (m)")
            ax.set_ylabel("Survival Probability")
            ax.set_title(f"MRB Decay for Qubit Group: {group}")
            ax.legend()
            ax.grid(True, which='both', linestyle='--')
            
            self._save_fig_to_sheet(fig, f"MRB Decay {group}")
            return self

        def add_mrb_heatmap(self, result: ExperimentResult):
            """Adds a worksheet with the MRB direct polarization heatmap."""
            polarization_results = result.data['avg_polarizations']
            qubit_groups = result.data['qubit_groups']
            depths = result.data['depths']
            
            grid = np.array(polarization_results).T
            num_qubits_labels = [len(q) if isinstance(q, tuple) else 1 for q in qubit_groups]

            fig, ax = plt.subplots(figsize=(max(8, len(qubit_groups) * 1.8), max(6, len(depths) * 0.6)))
            im = ax.imshow(grid, cmap='Blues', interpolation='nearest', vmin=0, vmax=1, aspect='auto')

            ax.set_xticks(np.arange(grid.shape[1])); ax.set_yticks(np.arange(grid.shape[0]))
            ax.set_xticklabels(num_qubits_labels); ax.set_yticklabels([str(d) for d in depths])
            ax.invert_yaxis()
            ax.set_title("MRB Heatmap (Effective Polarization)", fontsize=16, pad=20)
            ax.set_xlabel("Number of Qubits", fontsize=12); ax.set_ylabel("Circuit Depth", fontsize=12)

            for row in range(grid.shape[0]):
                for col in range(grid.shape[1]):
                    value = grid[row, col]
                    text_color = "white" if value > 0.5 else "black"
                    ax.text(col, row, f'{value:.3f}', ha='center', va='center', color=text_color)

            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.2)
            fig.colorbar(im, cax=cax).set_label("Effective Polarization", rotation=270, labelpad=20)
            plt.tight_layout(rect=[0, 0, 1, 0.96])

            self._save_fig_to_sheet(fig, "MRB Heatmap")
            return self

        # --- General Methods ---
        def save(self, filename: str) -> str:
            if not filename.endswith('.xlsx'): filename += '.xlsx'
            save_path = os.path.join(self.output_dir, filename)
            self.workbook.save(save_path)
            print(f"Excel report saved to: {save_path}")
            return save_path

        def _auto_fit_columns(self, ws):
            for col in ws.columns:
                max_len = max((len(str(cell.value)) for cell in col if cell.value), default=0) + 2
                ws.column_dimensions[get_column_letter(col[0].column)].width = max_len