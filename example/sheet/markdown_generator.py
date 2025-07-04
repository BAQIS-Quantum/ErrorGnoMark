# 先定义几个变量
title = "Baihua Quantum-Chip ErrorGnoMark Report"
description = (
    "ErrorGnoMark (EGM) is a benchmarking-and-characterization suite "
    "from the Beijing Academy for Quantum Information Sciences’ Quantum OS & Software team. "
    "It automates quantum-chip evaluation across qubit, circuit, system, and algorithm levels, "
    "delivering comprehensive diagnostics and visual feedback. "
    "https://github.com/BAQIS-Quantum/ErrorGnoMark"
)
notes = [
    "This benchmarking report is focused on the native gates of the quantum chip. Accordingly, all one- and two-qubit gate operations are executed without compilation (i.e., compile = false), ensuring that the results directly reflect hardware-level gate performance.",
    "For multi-qubit (“algorithm-level”) quality and speed metrics, circuit execution involves logical compilation (i.e., compile = true), as these tasks require algorithmic mapping to the device’s native gate set.",
    "Unless otherwise specified, all other benchmarking and characterization results are obtained with compilation disabled (compile = false), so as to represent the intrinsic characteristics of the physical gates."
]

# section 1 : Latest Public Calibration Information
section_1_title       = "1. Latest Public Calibration Information"
section_1_URL         = "https://quafu-sqc.baqis.ac.cn/framework/home"
section_1_image_path  = "E:/Repositories/ErrorGnoMark/example/sheet/section1.png"

# section 2 : ErrorGnoMark Testing Report
section_2_title       = "2. ErrorGnoMark Testing Report"
section_2_Benchmarking_title       = "2.1 Benchmarking"

# single qubit metrics
rb_iso_median     = 0.0003
rb_sim_median     = 0.0005
rb_iso_mean       = 0.0002
rb_sim_mean       = 0.0003
rb_fig           = "Egmbq1_fig1"

rb_pur_iso_med    = 0.0003
rb_pur_sim_med    = 0.0005
rb_pur_iso_mean   = 0.0002
rb_pur_sim_mean   = 0.0003
rb_pur_fig       = "Egmbq1_fig2"

xeb_iso_median     = 0.0003
xeb_sim_median     = 0.0005
xeb_iso_mean       = 0.0002
xeb_sim_mean       = 0.0003
xeb_fig           = "Egmbq1_fig1"

xebp_iso_med    = 0.0003
xebp_sim_med    = 0.0005
xebp_iso_mean   = 0.0002
xebp_sim_mean   = 0.0003
xebp_fig       = "Egmbq1_fig2"

csb_proc_iso_med    = 0.0003
csb_proc_sim_med    = 0.0005
csb_proc_iso_mean   = 0.0002
csb_proc_sim_mean   = 0.0003
csb_proc_fig       = "Egmbq1_fig2"

csb_stat_iso_med    = 0.0003
csb_stat_sim_med    = 0.0005
csb_stat_iso_mean   = 0.0002
csb_stat_sim_mean   = 0.0003
csb_stat_fig       = "Egmbq1_fig2"

csb_rot_iso_med    = 0.0003
csb_rot_sim_med    = 0.0005
csb_rot_iso_mean   = 0.0002
csb_rot_sim_mean   = 0.0003
csb_rot_fig       = "Egmbq1_fig2"

ro0_iso_med    = 0.0003
ro0_sim_med    = 0.0005
ro0_iso_mean   = 0.0002
ro0_sim_mean   = 0.0003
ro0_fig       = "Egmbq1_fig2"

ro1_iso_med    = 0.0003
ro1_sim_med    = 0.0005
ro1_iso_mean   = 0.0002
ro1_sim_mean   = 0.0003
ro1_fig       = "Egmbq1_fig2"

meas_iso_med    = 0.0003
meas_sim_med    = 0.0005
meas_iso_mean   = 0.0002
meas_sim_mean   = 0.0003
meas_fig       = "Egmbq1_fig2"

reset_iso_med    = 0.0003
reset_sim_med    = 0.0005
reset_iso_mean   = 0.0002
reset_sim_mean   = 0.0003
reset_fig       = "Egmbq1_fig2"

# two qubit metrics

rb2_iso_median     = 0.0003
rb2_sim_median     = 0.0005
rb2_iso_mean       = 0.0002
rb2_sim_mean       = 0.0003
rb2_fig           = "Egmbq1_fig1"

rb2_pur_iso_med    = 0.0003
rb2_pur_sim_med    = 0.0005
rb2_pur_iso_mean   = 0.0002
rb2_pur_sim_mean   = 0.0003
rb2_pur_fig       = "Egmbq1_fig2"

xeb2_iso_median     = 0.0003
xeb2_sim_median     = 0.0005
xeb2_iso_mean       = 0.0002
xeb2_sim_mean       = 0.0003
xeb2_fig           = "Egmbq1_fig1"

xebp2_iso_med    = 0.0003
xebp2_sim_med    = 0.0005
xebp2_iso_mean   = 0.0002
xebp2_sim_mean   = 0.0003
xebp2_fig       = "Egmbq1_fig2"

csb2_proc_iso_med    = 0.0003
csb2_proc_sim_med    = 0.0005
csb2_proc_iso_mean   = 0.0002
csb2_proc_sim_mean   = 0.0003
csb2_proc_fig       = "Egmbq1_fig2"

csb2_stat_iso_med    = 0.0003
csb2_stat_sim_med    = 0.0005
csb2_stat_iso_mean   = 0.0002
csb2_stat_sim_mean   = 0.0003
csb2_stat_fig       = "Egmbq1_fig2"

csb2_rot_iso_med    = 0.0003
csb2_rot_sim_med    = 0.0005
csb2_rot_iso_mean   = 0.0002
csb2_rot_sim_mean   = 0.0003
csb2_rot_fig       = "Egmbq1_fig2"

csb2_phi_iso_med    = 0.0003
csb2_phi_sim_med    = 0.0005
csb2_phi_iso_mean   = 0.0002
csb2_phi_sim_mean   = 0.0003
csb2_phi_fig       = "Egmbq1_fig2"

reset2_iso_med    = 0.0003
reset2_sim_med    = 0.0005
reset2_iso_mean   = 0.0002
reset2_sim_mean   = 0.0003
reset2_fig       = "Egmbq1_fig2"

# Multi qubits metrics

section_2_analysis_for_Benchmarking_title       = "2.2 A brief analysis for the Benchmarking results"

section_2_analysis_for_Incoherent_Statistical_title       = "2.2.1 Incoherent / Statistical Noise"
section_2_Incoherent_Statistical_analysis_lines = [
    "RB / XEB decays (isolated) fit single-exponential curves with pure-depolarizing rates ~7 × 10⁻⁴ (1-Q) and 1.6 × 10⁻² (2-Q).",
    "CSB “statistical-infidelity” channels match RB numbers to within 10 %, confirming that most loss is stochastic rather than coherent."
]
section_2_Incoherent_Statistical_analysis_section = (
    f"#### *{section_2_analysis_for_Incoherent_Statistical_title}*\n\n"
    + "\n".join(f"- {line}" for line in section_2_Incoherent_Statistical_analysis_lines)
)

section_2_analysis_for_Nearest_Neighbour_Crosstalk_Noise_title       = "2.2.2 Nearest-Neighbour Crosstalk"
section_2_Nearest_Neighbour_Crosstalk_Noise_lines = [
    "Going from isolated to simultaneous operation worsens 1-Q and 2-Q metrics by a factor ≈ 1.7 ×. Rough upper bound: inter-qubit crosstalk contributes ≤ 40 % of the total stochastic error budget.",
    "Purity-based fits show no systematic drift across rows/columns, indicating crosstalk is short-ranged."
]
section_2_Nearest_Neighbour_Crosstalk_Noise_section = (
    f"#### {section_2_analysis_for_Nearest_Neighbour_Crosstalk_Noise_title}\n\n"
    + "\n".join(f"- {line}" for line in section_2_Nearest_Neighbour_Crosstalk_Noise_lines)
)

section_2_analysis_for_Coherent_Error_Estimate_title       = "2.2.3 Coherent Error Estimate"
section_2_Coherent_Error_Estimate_lines = [
    "CSB “process-infidelity” minus “statistical-infidelity” yields a residual phase/rotation component ≤ 3 × 10⁻³ (1-Q) and ≤ 5 × 10⁻³ (2-Q).",
    "The gap between median and mean errors is < 20 % in all categories, suggesting coherent hot-spots are few and chip-wide spread is limited."
]
section_2_Coherent_Error_Estimate_section = (
    f"#### {section_2_analysis_for_Coherent_Error_Estimate_title}\n\n"
    + "\n".join(f"- {line}" for line in section_2_Coherent_Error_Estimate_lines)
)

section_2_analysis_for_Higher_Order_Behavior_title       = "2.2.4 Higher-Order Behavior"
section_2_Higher_Order_Behavior_lines = [
    "MRB shows depth-independent λ≈0.998 for qubit groups up to 10 → error per two-cycle ≈ 0.002, consistent with pair-wise data.",
    "•	Quantum Volume 32 confirms the error model extrapolates to small-footprint applications."
]
section_2_Higher_Order_Behavior_section = (
    f"#### {section_2_analysis_for_Higher_Order_Behavior_title}\n\n"
    + "\n".join(f"- {line}" for line in section_2_Higher_Order_Behavior_lines)
)

section_2_conclusion_for_Benchmarking_title       = "2.2.5 Conclusion"
section_2_conclusion_lines = [
    "The Baihua device is currently stochastic-noise limited; coherent components are already at the few-millipercent level. Nearest-neighbour crosstalk accounts for < 0.4 × total 2-Q error and ~0.2 × total 1-Q error.",
]
section_2_conclusion_section = (
    f"#### {section_2_conclusion_for_Benchmarking_title}\n\n"
    + "\n".join(section_2_conclusion_lines)
)

incoh_stat_med      = 0.0003
incoh_stat_sim_med  = 0.0005
incoh_stat_mean     = 0.0002
incoh_stat_sim_mean = 0.0003
incoh_stat_fig      = "Egmcq1_fig1"

coh_stat_med        = 0.0003
coh_stat_sim_med    = 0.0005
coh_stat_mean       = 0.0002
coh_stat_sim_mean   = 0.0003
coh_stat_fig        = "Egmcq1_fig2"

mu_err_med          = 0.0003
mu_err_sim_med      = 0.0005
mu_err_mean         = 0.0002
mu_err_sim_mean     = 0.0003
mu_err_fig          = "Egmcq1_fig3"

zeta1_err_med       = 0.0003
zeta1_err_sim_med   = 0.0005
zeta1_err_mean      = 0.0002
zeta1_err_sim_mean  = 0.0003
zeta1_err_fig       = "Egmcq1_fig4"

zeta2_err_med       = 0.0003
zeta2_err_sim_med   = 0.0005
zeta2_err_mean      = 0.0002
zeta2_err_sim_mean  = 0.0003
zeta2_err_fig       = "Egmcq1_fig5"

crosstalk_med       = 0.0003
crosstalk_sim_med   = 0.0005
crosstalk_mean      = 0.0002
crosstalk_sim_mean  = 0.0003
crosstalk_fig       = "Egmcq1_fig6"

section_2_Characterization_title       = "2.3 Characterization"
arbitrary_SU_2_matrix = r"""
$$
R(\mu,\zeta,\chi)
=
\begin{pmatrix}
e^{-i\zeta}\cos\frac{\mu}{2} & -\,i\,e^{i\chi}\sin\frac{\mu}{2}\\[6pt]
-\,i\,e^{-i\chi}\sin\frac{\mu}{2} & e^{i\zeta}\cos\frac{\mu}{2}
\end{pmatrix}
$$
"""

twoq_incoh_med        = 0.0003
twoq_incoh_sim_med    = 0.0005
twoq_incoh_mean       = 0.0002
twoq_incoh_sim_mean   = 0.0003
twoq_incoh_fig        = "Egmcq1_fig1"

twoq_coh_med          = 0.0003
twoq_coh_sim_med      = 0.0005
twoq_coh_mean         = 0.0002
twoq_coh_sim_mean     = 0.0003
twoq_coh_fig          = "Egmcq1_fig2"

twoq_mu_med           = 0.0003
twoq_mu_sim_med       = 0.0005
twoq_mu_mean          = 0.0002
twoq_mu_sim_mean      = 0.0003
twoq_mu_fig           = "Egmcq1_fig3"

twoq_zeta1_med        = 0.0003
twoq_zeta1_sim_med    = 0.0005
twoq_zeta1_mean       = 0.0002
twoq_zeta1_sim_mean   = 0.0003
twoq_zeta1_fig        = "Egmcq1_fig4"

twoq_zeta2_med        = 0.0003
twoq_zeta2_sim_med    = 0.0005
twoq_zeta2_mean       = 0.0002
twoq_zeta2_sim_mean   = 0.0003
twoq_zeta2_fig        = "Egmcq1_fig5"

twoq_crosstalk_med    = 0.0003
twoq_crosstalk_sim_med= 0.0005
twoq_crosstalk_mean   = 0.0002
twoq_crosstalk_sim_mean=0.0003
twoq_crosstalk_fig    = "Egmcq1_fig6"

characterization_footer = r"""
General Form of Two-Qubit Gates An arbitrary excitation-preserving two-qubit unitary W (up to global phase), in the basis { |00⟩; |01⟩; |10⟩; |11⟩}; {|00⟩,|01⟩,|10⟩,|11⟩}, can be parameterized by five angles: swap angle (θ), swap azimuthal phase (χ), controlled phase (φ), and two differential Z phases (ζ, γ).
$$W=\begin{pmatrix}{e^{i\gamma}}&{0}&{0}&{0}\\{0}&{e^{-i\zeta}\cos\theta}&{-ie^{i\chi}\sin\theta}&{0}\\{0}&{-ie^{-i\chi}\sin\theta}&{e^{i\zeta}\cos\theta}&{0}\\{0}&{0}&{0}&{e^{-i(\gamma+\phi)}}\end{pmatrix}$$
$\theta$ (Swap Angle): Degree of population swap between |01⟩ and |10⟩; controls entanglement strength.
$\chi$ (Swap Azimuthal Phase): Phase for swap transition; equivalent to a relative Z rotation between qubits.
$\phi$ (Controlled Phase): Conditional phase on |11⟩; sets entangling type (e.g., CZ if $\phi$ = $\pi$).
$\zeta$, $\gamma$ (Z Phases): Relative Z phases, sensitive to flux noise and control drift.
"""

section_2_analysis_for_Characterization_title       = "2.4 A brief analysis for the Characterization Results"
section_2_analysis_for_C_Incoherent_Statistical_title       = "2.4.1 Incoherent / Statistical Noise"
section_2_Incoherent_Statistical_analysis_lines = [
    "RB/XEB (isolated) and CSB statistical-infidelity yield pure-depolarizing rates around 3 × 10⁻⁴ (1-Q) and 3 × 10⁻³ (2-Q), consistent with stochastic noise as the dominant channel.",
    "The close agreement between “incoherent/statistical” and “coherent/statistical” error estimates confirms that most gate errors arise from random processes rather than systematic drifts."
]
section_2_C_Incoherent_Statistical_analysis_section = (
    f"#### *{section_2_analysis_for_C_Incoherent_Statistical_title}*\n\n"
    + "\n".join(f"- {line}" for line in section_2_Incoherent_Statistical_analysis_lines)
)

section_2_analysis_for_C_Coherent_Error_Components_title       = "2.4.2 Incoherent / Statistical Noise"
section_2_C_Coherent_Error_Components_analysis_lines = [
    "The difference between “process-infidelity” and “statistical-infidelity” in CSB results gives an upper bound for coherent errors: ≲ 2 × 10⁻³ for 1-Q gates and ≲ 3 × 10⁻³ for 2-Q gates.",
    "Parameter μ (rotation error) and φ (controlled phase) are near their ideal values (e.g., φ ≈ π for CZ), and the residual ζ, γ phase errors remain small, typically a few 10⁻³ or less.",
    "The small difference between median and mean error rates (< 20%) indicates coherent error “hot spots” are not widespread."
]
section_2_C_Coherent_Error_Components_analysis_section = (
    f"#### *{section_2_analysis_for_C_Coherent_Error_Components_title}*\n\n"
    + "\n".join(f"- {line}" for line in section_2_C_Coherent_Error_Components_analysis_lines)
)

section_2_analysis_for_C_Z_Crosstalk_title       = "2.4.3 Z Phase (ζ, γ) and Crosstalk"
section_2_C_Z_Crosstalk_analysis_lines = [
    "Differential Z phases (ζ, γ), extracted per gate, are stable across the chip, except for minor fluctuations likely due to slow flux noise and residual control drift.",
    "Crosstalk values (from dedicated crosstalk measurements) remain below 5 × 10⁻³ for most qubit pairs, with no evidence of systematic or long-range patterns."
]
section_2_C_Z_Crosstalk_analysis_section = (
    f"#### *{section_2_analysis_for_C_Z_Crosstalk_title}*\n\n"
    + "\n".join(f"- {line}" for line in section_2_C_Z_Crosstalk_analysis_lines)
)

section_2_analysis_for_Higher_Order_Characterization_title       = "2.4.4 Higher-Order Characterization"
section_2_C_Higher_Order_Characterization_analysis_lines = [
    "μ error (rotation axis misalignment) and crosstalk remain within benchmarked limits, indicating no significant hidden coherent error at the system level.",
]
section_2_C_Higher_Order_Characterization_section = (
    f"#### *{section_2_analysis_for_Higher_Order_Characterization_title}*\n\n"
    + "\n".join(f"- {line}" for line in section_2_C_Higher_Order_Characterization_analysis_lines)
)

section_2_conclusion_for_Characterization_title       = "2.4.5 Conclusion"
section_2_C_conclusion_lines = [
    "Baihua’s characterization reveals gate error rates dominated by stochastic (incoherent) channels, with coherent error and Z-phase-related drift suppressed to the sub-percent level. Crosstalk and rotation-axis errors are well controlled.",
]
section_2_C_conclusion_section = (
    f"#### {section_2_conclusion_for_Characterization_title}\n\n"
    + "\n".join(section_2_C_conclusion_lines)
)

section_3_Visualized_Figures_title       = "2.5 Visualized Figures"


# 用 f-string 生成 markdown
markdown_content = (f"""
# **{title}**

*{description}*

*Notes on Compilation and Benchmarking Scope:*
""" + "\n".join(f"{i+1}. *{notes[i]}*" for i in range(len(notes))) + f"""

## **{section_1_title}**
![Section 1]({section_1_image_path})
{section_1_URL}
""" + f"""

## **{section_2_title}**
### **{section_2_Benchmarking_title}**

|                                               |  Single-qubit gates |       |             |
|-----------------------------------------------|---------------------|---------------------|------------------|
|                                               |                     |       |     Metrics for Quality        |
| Metric                                        | Median (iso/sim)    | Mean (iso/sim)      | Figure           |
| 1Q-RB, isolated/simultaneous                  | {rb_iso_median}/{rb_sim_median} | {rb_iso_mean}/{rb_sim_mean} | {rb_fig} |
| 1Q-RB Purity, isolated/simultaneous           | {rb_pur_iso_med}/{rb_pur_sim_med} | {rb_pur_iso_mean}/{rb_pur_sim_mean} | {rb_pur_fig} |
| 1Q-XEB, isolated/simultaneous                 | {xeb_iso_median}/{xeb_sim_median} | {xeb_iso_mean}/{xeb_sim_mean} | {xeb_fig}|
| 1Q-XEB Purity, isolated/simultaneous          | {xebp_iso_med}/{xebp_sim_med}| {xebp_iso_mean}/{xebp_sim_mean} | {xebp_fig}|
| 1Q-CSB, isolated/simultaneous – Process infid.| {csb_proc_iso_med}/{csb_proc_sim_med} | {csb_proc_iso_mean}/{csb_proc_sim_mean} | {csb_proc_fig} |
| 1Q-CSB, isolated/simultaneous – Statistical infid.| {csb_stat_iso_med}/{csb_stat_sim_med} | {csb_stat_iso_mean}/{csb_stat_sim_mean} | {csb_stat_fig} |
| 1Q-CSB, isolated/simultaneous – Rotation infid.| {csb_rot_iso_med}/{csb_rot_sim_med} | {csb_rot_iso_mean}/{csb_rot_sim_mean} | {csb_rot_fig} |
| Readout \|0⟩                                   | {ro0_iso_med}/{ro0_sim_med} | {ro0_iso_mean}/{ro0_sim_mean} | {ro0_fig} |
| Readout \|1⟩                                   | {ro1_iso_med}/{ro1_sim_med} | {ro1_iso_mean}/{ro1_sim_mean} | {ro1_fig} |
| Measurement, isolated/simultaneous            | {meas_iso_med}/{meas_sim_med} | {meas_iso_mean}/{meas_sim_mean} | {meas_fig} |
|                                               |                     |         |     Metrics for Speed           |
| 1Q-Reset Rate                                | {reset_iso_med}/{reset_sim_med} | {reset_iso_mean}/{reset_sim_mean} | {reset_fig} |

|                                               |  Two-qubit gates |       |             |
|-----------------------------------------------|---------------------|---------------------|------------------|
|                                               |                     |       |     Metrics for Quality        |
| Metric                                        | Median (iso/sim)    | Mean (iso/sim)      | Figure           |
| 2Q-RB, isolated/simultaneous                  | {rb2_iso_median}/{rb2_sim_median} | {rb2_iso_mean}/{rb2_sim_mean} | {rb2_fig} |
| 2Q-RB Purity, isolated/simultaneous           | {rb2_pur_iso_med}/{rb2_pur_sim_med} | {rb2_pur_iso_mean}/{rb2_pur_sim_mean} | {rb2_pur_fig} |
| 2Q-XEB, isolated/simultaneous                 | {xeb2_iso_median}/{xeb2_sim_median} | {xeb2_iso_mean}/{xeb2_sim_mean} | {xeb2_fig}|
| 2Q-XEB Purity, isolated/simultaneous          | {xebp2_iso_med}/{xebp2_sim_med}| {xebp2_iso_mean}/{xebp2_sim_mean} | {xebp2_fig}|
| 2Q-CSB, isolated/simultaneous – Process infid.| {csb2_proc_iso_med}/{csb2_proc_sim_med} | {csb2_proc_iso_mean}/{csb2_proc_sim_mean} | {csb2_proc_fig} |
| 2Q-CSB, isolated/simultaneous – Statistical infid.| {csb2_stat_iso_med}/{csb2_stat_sim_med} | {csb2_stat_iso_mean}/{csb2_stat_sim_mean} | {csb2_stat_fig} |
| 2Q-CSB, isolated/simultaneous – Rotation infid.| {csb2_rot_iso_med}/{csb2_rot_sim_med} | {csb2_rot_iso_mean}/{csb2_rot_sim_mean} | {csb2_rot_fig} |
| 2Q-CSB, isolated/simultaneous – Phi infid.| {csb2_phi_iso_med}/{csb2_phi_sim_med} | {csb2_phi_iso_mean}/{csb2_phi_sim_mean} | {csb2_phi_fig} |
|                                               |                     |         |     Metrics for Speed           |
| 2Q-Reset Rate                                | {reset_iso_med}/{reset_sim_med} | {reset_iso_mean}/{reset_sim_mean} | {reset_fig} |

<sub>Randomized  Benchmarking, RB, Knill, Emanuel, et al. Physical Review A—Atomic, Molecular, and Optical Physics 77.1 (2008): 012307.</sub>

<sub>Cross Entropy Benchmarking, XEB, Arute, F., Arya, K., Babbush, R. et al. Nature 574, 505–510 (2019). https://doi.org/10.1038/s41586-019-1666-5</sub>

<sub>Channel Spectrum Benchmarking, CSB, , Yanwu Gu, Wei-Feng Zhuang, Xudan Chai & Dong E. Liu , Nature Communications, 14, 5880 (2023).</sub>

---

|                                  |  Multi-qubit gates |       |             |
|----------------------------------|--------------------|-------|-------------|
|                                  |                    |       |     Metrics for Quality        |
| Metric                           | Median         | Mean           | Figure       |
| GHZ State Fidelity (Compiling=TRUE) |             |                |              |
| Qubits: 4                         |               |                | Egmbqm_fig1  |
| Qubits: 5                         |               |                |              |
| Qubits: 6                         |               |                |              |
| Qubits: 8                         |               |                |              |
| Qubits: 10                        |               |                |              |
| XEB Fidelity (Compiling=TRUE)     |               |                |              |
| Qubits: 9, Depth: 20              |               |                | Egmbqm_fig2  |
| Qubits: 16, Depth: 20             |               |                |              |
| Qubits: 25, Depth: 20             |               |                |              |
| MRB                               |     Median    |      Mean      |     Figure   | 
| MRB, Qubits:2, Depth:2            | 0.0003/0.0005 | 0.0002/0.0003  |              |
| MRB, Qubits:4, Depth:4            |               |                | Egmbqm_fig3  |
| MRB, Qubits:6, Depth:6            |               |                |              |
| MRB, Qubits:…, Depth:…            |               |                |              |
| MRB, Qubits:10, Depth:10          |               |                |              |
| QV                                |               |      32        |              |

<sub>MRB, Mirror Randomized Benchmarking. Proctor, Timothy, et al. Nature Physics 18.1 (2022): 75-79.</sub>

<sub>QV, Quantum Volumn, Jurcevic, Petar, et al. Quantum Science and Technology 6.2 (2021): 025020.</sub>

|                                  |  Multi-qubit gates |
|----------------------------------|--------------------|
|                                  | Metrics for Application |
| Metric                           | Figure                  |
| Text here the problem and the solution… |   Egmbqm_fig4    |

---

### **{section_2_analysis_for_Benchmarking_title}**
{section_2_Incoherent_Statistical_analysis_section}
{section_2_Nearest_Neighbour_Crosstalk_Noise_section}
{section_2_Coherent_Error_Estimate_section}
{section_2_Higher_Order_Behavior_section}
---
{section_2_conclusion_section}

---
For detailed phase-map, rotation-axis spread, and leakage diagnostics, consult the corresponding Characterization section of the ErrorGnoMark report.
||Single-qubit gates|||
|:-----------------------------------------|:--------------------------:|:--------------------------:|:------------------:|
||||Metrics for Quality|
| Metric                                   | Median (iso/sim)           | Mean (iso/sim)             | Figure             |
| 1Q Incoherent Error / Statistic Error    | {incoh_stat_med}/{incoh_stat_sim_med}   | {incoh_stat_mean}/{incoh_stat_sim_mean}   | {incoh_stat_fig}   |
| 1Q Coherent Error / Statistic Error      | {coh_stat_med}/{coh_stat_sim_med}       | {coh_stat_mean}/{coh_stat_sim_mean}       | {coh_stat_fig}     |
| 1Q μ Error                               | {mu_err_med}/{mu_err_sim_med}           | {mu_err_mean}/{mu_err_sim_mean}           | {mu_err_fig}       |
| 1Q ζ Error (first)                       | {zeta1_err_med}/{zeta1_err_sim_med}     | {zeta1_err_mean}/{zeta1_err_sim_mean}     | {zeta1_err_fig}    |
| 1Q ζ Error (second)                      | {zeta2_err_med}/{zeta2_err_sim_med}     | {zeta2_err_mean}/{zeta2_err_sim_mean}     | {zeta2_err_fig}    |
| Crosstalk                                | {crosstalk_med}/{crosstalk_sim_med}     | {crosstalk_mean}/{crosstalk_sim_mean}     | {crosstalk_fig}    |

### **{section_2_Characterization_title}**
Single-qubit XY rotations (microwave gates). An arbitrary SU(2) matrix can be parameterized using three angles as：
{arbitrary_SU_2_matrix}

||Two-qubit gates|||
|:-----------------------------------------|:--------------------------:|:--------------------------:|:------------------:|
||||Metrics for Quality|
| Metric                                   | Median (iso/sim)           | Mean (iso/sim)             | Figure             |
| 2Q Incoherent Error / Statistic Error    | {twoq_incoh_med}/{twoq_incoh_sim_med}   | {twoq_incoh_mean}/{twoq_incoh_sim_mean}   | {twoq_incoh_fig}   |
| 2Q Coherent Error / Statistic Error      | {twoq_coh_med}/{twoq_coh_sim_med}       | {twoq_coh_mean}/{twoq_coh_sim_mean}       | {twoq_coh_fig}     |
| 2Q μ Error                               | {twoq_mu_med}/{twoq_mu_sim_med}         | {twoq_mu_mean}/{twoq_mu_sim_mean}         | {twoq_mu_fig}      |
| 2Q ζ Error (first)                       | {twoq_zeta1_med}/{twoq_zeta1_sim_med}   | {twoq_zeta1_mean}/{twoq_zeta1_sim_mean}   | {twoq_zeta1_fig}   |
| 2Q ζ Error (second)                      | {twoq_zeta2_med}/{twoq_zeta2_sim_med}   | {twoq_zeta2_mean}/{twoq_zeta2_sim_mean}   | {twoq_zeta2_fig}   |
| Crosstalk                                | {twoq_crosstalk_med}/{twoq_crosstalk_sim_med} | {twoq_crosstalk_mean}/{twoq_crosstalk_sim_mean} | {twoq_crosstalk_fig} |

{characterization_footer}

### **{section_2_analysis_for_Characterization_title}**

{section_2_C_Incoherent_Statistical_analysis_section}

{section_2_C_Coherent_Error_Components_analysis_section}

{section_2_C_Z_Crosstalk_analysis_section}

{section_2_C_Higher_Order_Characterization_section}

{section_2_C_conclusion_section}

## **{section_3_Visualized_Figures_title}**



"""


                    )


with open("example.md", "w", encoding="utf-8") as f:
    f.write(markdown_content)
