# File: errorgnomark/reporting/generators/html_generator.py
# ---------------------------------------------------------------------
# Module: HTMLReportGenerator — Jinja2‑Based RB Report Renderer
# ---------------------------------------------------------------------
# Generates human‑readable HTML reports for Randomized Benchmarking (RB)
# analysis results. Plots are rendered via Matplotlib and embedded as
# base64‑encoded images directly in the report template.
#
# This module integrates with:
#   • schemas.results.rb.RBAnalysisResult
#   • reporting.templates.html.rb_report.jinja2
#
# ---------------------------------------------------------------------

import base64
import io
import logging
from pathlib import Path
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from egm.schemas.results.rb import RBAnalysisResult

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# ---------------------------------------------------------------------
# HTMLReportGenerator Definition
# ---------------------------------------------------------------------
class HTMLReportGenerator:
    """
    Generates HTML reports from Randomized Benchmarking (RB) result objects.

    This generator dynamically loads a Jinja2 template, embeds a
    base64‑encoded Matplotlib plot, and writes the rendered result to disk.
    """

    # -----------------------------------------------------------------
    # Initialization
    # -----------------------------------------------------------------
    def __init__(self, template_dir: Path):
        """
        Initialize the report generator.

        Args:
            template_dir: Directory path containing Jinja2 templates.
        """
        if not template_dir.is_dir():
            raise FileNotFoundError(f"Template directory not found: {template_dir}")

        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))
        logging.info(f"HTMLReportGenerator initialized (templates: {template_dir})")

    # -----------------------------------------------------------------
    # Plot Generation Helper
    # -----------------------------------------------------------------
    def _generate_plot_base64(self, result: RBAnalysisResult) -> str:
        """
        Create a Matplotlib summary plot and return it as a base64‑encoded string.

        Args:
            result: The RB analysis result to visualize.

        Returns:
            Base64‑encoded PNG image suitable for embedding in HTML.
        """
        try:
            plt.figure(figsize=(8, 5))

            if getattr(result, "sequence_data", None):
                try:
                    lengths = [dp.sequence_length for dp in result.sequence_data]
                    survs = [dp.survival_probability for dp in result.sequence_data]
                    plt.errorbar(lengths, survs, fmt="o-", capsize=4, label="Experimental Data")
                except Exception as e:
                    logging.warning(f"Data extraction from sequence_data failed: {e}")

                epc_value = getattr(result, "epc", None)
                epc_label = f"EPC: {epc_value:.2e}" if epc_value is not None else "EPC unavailable"
                plt.title(f"RB Decay Curve ({epc_label})")
                plt.xlabel("Clifford Length")
                plt.ylabel("Survival Probability")
                plt.grid(True, alpha=0.35)
                plt.legend()
            else:
                plt.text(
                    0.5,
                    0.5,
                    "No Plot Data Available",
                    ha="center",
                    va="center",
                    fontsize=12,
                )
                plt.title("RB Analysis Summary")

            buf = io.BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight")
            plt.close()
            buf.seek(0)
            return base64.b64encode(buf.getvalue()).decode("utf-8")

        except Exception as err:
            logging.warning(f"Plot generation failed: {err}")
            return ""

    # -----------------------------------------------------------------
    # Main Report Generation
    # -----------------------------------------------------------------
    def generate_rb_report(self, result: RBAnalysisResult, output_path: Path):
        """
        Render and export a complete RB analysis report as HTML.

        Args:
            result: An RBAnalysisResult object containing the analysis data.
            output_path: File path for the generated HTML output.
        """
        template_name = "rb_report.jinja2"

        try:
            template = self.env.get_template(template_name)
            plot_image_b64 = self._generate_plot_base64(result)

            # Resolve a robust result identifier (supports both `result_id` and `id`)
            result_identifier = getattr(result, "result_id", getattr(result, "id", "unknown"))

            context = {
                "result": result,
                "title": f"RB Report – {result_identifier}",
                "plot_image_base64": plot_image_b64,
            }

            html_content = template.render(context)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            logging.info(f"HTML report successfully written to: {output_path.resolve()}")

        except TemplateNotFound:
            msg = f"Report template '{template_name}' not found in '{self.template_dir}'."
            logging.error(msg)
            raise FileNotFoundError(msg)

        except Exception as err:
            msg = f"Error during HTML report generation: {err}"
            logging.error(msg)
            raise