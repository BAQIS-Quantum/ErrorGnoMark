# File Path: errorgnomark/analysis/reporting.py
# This version adds the DFE formula to the Excel summary sheet.

import os
import io
import numpy as np
from typing import List, Dict, Any
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

from errorgnomark.analysis.analysis_results import AnalysisResult

def plot_density_matrix(
    rho: np.ndarray,
    title: str = "Density Matrix",
    save_path: str = None
) -> plt.Figure:
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        raise ValueError("Input rho must be a square 2D array.")
    
    dim = rho.shape[0]
    num_qubits = int(np.log2(dim))
    tick_labels = [format(i, f'0{num_qubits}b') for i in range(dim)]

    fig = plt.figure(figsize=(16, 7))
    fig.suptitle(title, fontsize=18, y=0.98)

    max_z = np.max(np.abs(rho))
    z_lim = (-max_z * 1.1, max_z * 1.1) if max_z > 0 else (-1, 1)

    ax_real = fig.add_subplot(1, 2, 1, projection='3d')
    ax_real.set_title("Real Part", fontsize=14)
    
    xpos, ypos = np.meshgrid(np.arange(dim), np.arange(dim))
    xpos = xpos.flatten()
    ypos = ypos.flatten()
    zpos = np.zeros_like(xpos)
    
    dx = dy = 0.8
    dz_real = np.real(rho).flatten()
    
    min_val, max_val = np.min(dz_real), np.max(dz_real)
    colors_real = plt.cm.viridis((dz_real - min_val) / (max_val - min_val + 1e-9))

    ax_real.bar3d(xpos, ypos, zpos, dx, dy, dz_real, color=colors_real, shade=True)
    
    ax_real.set_xticks(np.arange(dim))
    ax_real.set_xticklabels(tick_labels, rotation=30, ha='right')
    ax_real.set_yticks(np.arange(dim))
    ax_real.set_yticklabels(tick_labels, rotation=-20, ha='left')
    ax_real.set_zlim(z_lim)
    ax_real.set_xlabel("Column", labelpad=10)
    ax_real.set_ylabel("Row", labelpad=10)
    ax_real.set_zlabel("Value", labelpad=10)

    ax_imag = fig.add_subplot(1, 2, 2, projection='3d')
    ax_imag.set_title("Imaginary Part", fontsize=14)
    
    dz_imag = np.imag(rho).flatten()
    min_val, max_val = np.min(dz_imag), np.max(dz_imag)
    colors_imag = plt.cm.viridis((dz_imag - min_val) / (max_val - min_val + 1e-9))
    
    ax_imag.bar3d(xpos, ypos, zpos, dx, dy, dz_imag, color=colors_imag, shade=True)
    
    ax_imag.set_xticks(np.arange(dim))
    ax_imag.set_xticklabels(tick_labels, rotation=30, ha='right')
    ax_imag.set_yticks(np.arange(dim))
    ax_imag.set_yticklabels(tick_labels, rotation=-20, ha='left')
    ax_imag.set_zlim(z_lim)
    ax_imag.set_xlabel("Column", labelpad=10)
    ax_imag.set_ylabel("Row", labelpad=10)
    ax_imag.set_zlabel("Value", labelpad=10)

    fig.tight_layout(rect=[0, 0, 1, 0.95])

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Density matrix plot saved to: {save_path}")

    return fig

def generate_report(results: List[AnalysisResult]):
    print("\n" + "="*50)
    print(" " * 15 + "ANALYSIS REPORT")
    print("="*50)
    for i, result in enumerate(results):
        print(f"\n--- Result Set {i+1}: {result.analysis_type} ---")
        print(f"  Reconstruction Method: {result.method}")
        if result.fidelity_with_ideal is not None:
            print(f"  Fidelity with Ideal State: {result.fidelity_with_ideal:.4f}")
        if result.purity is not None:
            print(f"  Purity of Reconstructed State: {result.purity:.4f}")
        if result.trace is not None:
            print(f"  Trace of Reconstructed Matrix: {result.trace:.4f}")
    print("\n" + "="*50)

class ExcelReport:
    def __init__(self, output_dir: str):
        self.workbook = Workbook()
        self.workbook.remove(self.workbook.active)
        self.output_dir = output_dir
        self._header_font = Font(bold=True, color="FFFFFF")
        self._header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        self._center_align = Alignment(horizontal="center", vertical="center")
        self._thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    def _apply_header_style(self, cell):
        cell.font = self._header_font
        cell.fill = self._header_fill
        cell.alignment = self._center_align
        cell.border = self._thin_border

    # --- [MODIFIED METHOD] ---
    def create_summary_sheet(self, analysis_results: List[AnalysisResult], experiment_params: Dict[str, Any]):
        ws = self.workbook.create_sheet(title="Summary")
        
        # Experiment Parameters
        ws.cell(row=1, column=1, value="Experiment Parameters").font = Font(bold=True, size=14)
        row_idx = 2
        for key, value in experiment_params.items():
            ws.cell(row=row_idx, column=1, value=key).font = Font(bold=True)
            ws.cell(row=row_idx, column=2, value=str(value))
            row_idx += 1
        
        # Analysis Results
        row_idx += 2 # Add extra space
        ws.cell(row=row_idx, column=1, value="Analysis Results").font = Font(bold=True, size=14)
        row_idx += 1
        
        headers = ["Analysis Type", "Method", "Fidelity", "Purity", "Trace"]
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = header
            self._apply_header_style(cell)

        for result in analysis_results:
            row_idx += 1
            ws.cell(row=row_idx, column=1, value=result.analysis_type).border = self._thin_border
            ws.cell(row=row_idx, column=2, value=result.method).border = self._thin_border
            ws.cell(row=row_idx, column=3, value=f"{result.fidelity_with_ideal:.4f}" if result.fidelity_with_ideal is not None else "N/A").border = self._thin_border
            ws.cell(row=row_idx, column=4, value=f"{result.purity:.4f}" if result.purity is not None else "N/A").border = self._thin_border
            ws.cell(row=row_idx, column=5, value=f"{result.trace:.4f}" if result.trace is not None else "N/A").border = self._thin_border

        # --- [NEW SECTION]: Add DFE Formula to the sheet ---
        row_idx += 3 # Add more space
        ws.cell(row=row_idx, column=1, value="Direct Fidelity Estimation (DFE) Formula").font = Font(bold=True, size=12)
        row_idx += 1
        
        formula_str = "F = (1/d) * Σᵢ cᵢ * <Pᵢ>ₑₓₚ"
        ws.cell(row=row_idx, column=1, value=formula_str).font = Font(italic=True)
        row_idx += 1

        ws.cell(row=row_idx, column=1, value="Where:").font = Font(bold=True)
        row_idx += 1
        
        ws.cell(row=row_idx, column=1, value="d")
        ws.cell(row=row_idx, column=2, value="Dimension of the Hilbert space (2^num_qubits)")
        row_idx += 1
        
        ws.cell(row=row_idx, column=1, value="Pᵢ")
        ws.cell(row=row_idx, column=2, value="The i-th Pauli operator (e.g., IX, ZY, etc.)")
        row_idx += 1
        
        ws.cell(row=row_idx, column=1, value="cᵢ")
        ws.cell(row=row_idx, column=2, value="Classically computed coefficient: cᵢ = <ψ_ideal| Pᵢ |ψ_ideal>")
        row_idx += 1
        
        ws.cell(row=row_idx, column=1, value="<Pᵢ>ₑₓₚ")
        ws.cell(row=row_idx, column=2, value="Experimentally measured expectation value of Pᵢ")
        # --- [END OF NEW SECTION] ---

        self._auto_fit_columns(ws)
        return self

    def _add_wide_format_sheet(self, sheet_title: str, experiment_data: Dict[str, Any], data_key: str, value_format: str):
        ws = self.workbook.create_sheet(title=sheet_title)
        
        num_qubits = experiment_data.get("num_qubits")
        if num_qubits is None:
            ws.cell(row=1, column=1, value="Error: num_qubits not found in experiment_data.")
            return

        outcomes = [format(i, f'0{num_qubits}b') for i in range(2**num_qubits)]
        headers = ["Basis"] + outcomes
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.value = header
            self._apply_header_style(cell)

        row_idx = 2
        for basis, data in experiment_data.items():
            if basis == "num_qubits":
                continue
            
            ws.cell(row=row_idx, column=1, value=basis).border = self._thin_border
            
            source_data = data.get(data_key, {})
            for col_idx, outcome in enumerate(outcomes, 2):
                value = source_data.get(outcome, 0)
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.value = value
                cell.border = self._thin_border
                if value_format:
                    cell.number_format = value_format
            row_idx += 1
            
        self._auto_fit_columns(ws)

    def add_raw_data_sheet(self, experiment_data: Dict[str, Any]):
        self._add_wide_format_sheet("Raw Counts", experiment_data, 'counts', '0')
        return self

    def add_probabilities_sheet(self, experiment_data: Dict[str, Any]):
        self._add_wide_format_sheet("Observed Probabilities", experiment_data, 'probabilities', '0.0000')
        self._add_wide_format_sheet("Ideal Probabilities", experiment_data, 'ideal_probabilities', '0.0000')
        return self

    def add_density_matrix_plot(self, rho: np.ndarray, sheet_name: str = "Density Matrix Plot"):
        ws = self.workbook.create_sheet(title=sheet_name)
        fig = plot_density_matrix(rho, title=sheet_name)
        
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight')
        img_buffer.seek(0)
        
        img = OpenpyxlImage(img_buffer)
        ws.add_image(img, 'A1')
        
        plt.close(fig)
        return self

    def save(self, filename_prefix: str) -> str:
        if not filename_prefix.endswith('.xlsx'):
            filename = f"{filename_prefix}.xlsx"
        save_path = os.path.join(self.output_dir, f"{filename}.xlsx") # Corrected filename usage
        self.workbook.save(save_path)
        return save_path

    def _auto_fit_columns(self, worksheet):
        for col in worksheet.columns:
            max_length = 0
            column_letter = get_column_letter(col[0].column)
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 3)
            worksheet.column_dimensions[column_letter].width = adjusted_width