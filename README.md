# ErrorGnoMark: Quantum Chip Error Diagnosis & Benchmark

## Overview

Benchmarking and characterization are now core services for quantum cloud platforms, enabling reliable performance evaluation, user trust, and industry standardization.

ErrorGnoMark (Error Diagnose & Benchmark) is a comprehensive tool developed by the Quantum Operating System Group at the Beijing Academy of Quantum Information Sciences.  It is designed around standardized testing workflows, highly automated execution mechanisms, and platform-level interface adaptability. It supports multi-dimensional performance assessment, including single- and two-qubit gate benchmarking[^1][^2][^3], multi-qubit entanglement, coherent and incoherent noise modeling, and gate-level crosstalk analysis. The system enables full-stack deployment and integration—from cloud user interfaces to local chip control hardware—allowing seamless, one-click test execution, automated data acquisition, and performance analysis. Standardized benchmarking reports, covering fidelity, throughput, and latency, are generated for continuous and automated online monitoring of quantum chips.



<p align="center">
  <img src="errorgnomark/bmqc.png" alt="ErrorGnoMark Illustration" width="500px">
</p>

### Potential Applications

### ErrorGnoMark: Main Application Modes

**1. Real-Time Error Feedback for End-Users**  
Provides transparent, real-time error diagnostics for quantum chips, enabling users to access clear and timely performance data.

**2. Backend Performance Engine for Quantum Compilers**  
Acts as a backend performance feedback engine for quantum compilers (e.g., Qsteed), supporting logical gate mapping optimization and circuit-level routing adjustments.

**3. Support for Local Control Systems**  
Delivers precise references for device calibration, error modeling, and optimal control within local control systems.

---

**Result Presentation**  
Based on these capabilities, the platform can periodically publish standardized benchmarking reports across various hardware platforms (e.g., ≥10 reports), offering trustworthy third-party data for user decision-making, platform management, and regulatory evaluation.  The results are available in both tabular (text-based) formats and visualized graphical displays, allowing users to select their preferred mode of presentation.**



## Version Information

**ErrorGnoMark 0.1.9**  
*Note: This is the latest version. Future updates will align with advancements in relevant research fields and evolving application requirements.*

## Installation

### Installation via pip

We recommend installing **ErrorGnoMark** using pip for simplicity and convenience:

```bash
pip install ErrorGnoMark
```

### Installation via GitHub
Alternatively, you can clone the repository from GitHub and install the package locally:

```bash
git clone https://github.com/BAQIS-Quantum/ErrorGnoMark`
```

```bash
cd errorgnomark`
```

```bash
pip install -e
```
If some dependencies are not installed automatically, you may see errors indicating that certain packages are missing when running the program. In this case, please refer to the requirements.txt file and manually install the required packages using the specified versions.

### Upgrade to the Latest Version
To ensure you are using the latest features and improvements, update ErrorGnoMark with:
```bash
pip install --upgrade ErrorGnoMark
```


## Running Example Programs

To verify the installation, you can run example programs:

```bash
cd example
```

```bash
QC-lmc.py
```

### Overview

Before using **ErrorGnoMark** for quantum error diagnosis, we recommend users begin with the introduction to familiarize themselves with the platform. The **Quick Start Guide** provides step-by-step instructions for using the quantum error diagnosis service and building your first program. Afterward, users are encouraged to explore application cases provided in the tutorials. Finally, users can apply **ErrorGnoMark** to address specific research and engineering challenges. For detailed API documentation, refer to the official API documentation page.

### Tutorials

**ErrorGnoMark** offers a range of tutorials, from beginner to advanced topics. These tutorials are available on the official website, and users interested in research or development are encouraged to download and utilize Jupyter Notebooks.



## Feedback

We encourage users to provide feedback, report issues, and suggest improvements through the following channels:

- **GitHub Issues**: Use the [GitHub Issues](https://github.com/BAQIS-Quantum/ErrorGnoMark/issues) page to report bugs, suggest new features, or share improvement ideas.
- **Email**: Contact us directly at **chaixd@baqis.ac.cn** for questions or additional support.

Collaboration with the community is vital to the continuous improvement of **ErrorGnoMark**. Your input will help us make the tool better and more impactful for the quantum computing community!



## License

ErrorGnoMark is licensed under the Apache License.

## References

[^1]: **Quality, Speed, and Scale: Three key attributes to measure the performance of near-term quantum computers**, Andrew Wack, Hanhee Paik, Ali Javadi-Abhari, Petar Jurcevic, Ismael Faro, Jay M. Gambetta, Blake R. Johnson, 2021, [arXiv:2110.14108](https://arxiv.org/abs/2110.14108) [quant-ph].

[^2]: **Optimizing quantum gates towards the scale of logical qubits**, Klimov, P.V., Bengtsson, A., Quintana, C. et al., *Nature Communications*, 15, 2442 (2024). [https://doi.org/10.1038/s41467-024-46623-y](https://doi.org/10.1038/s41467-024-46623-y).

[^3]: **Benchmarking universal quantum gates via channel spectrum**, Yanwu Gu, Wei-Feng Zhuang, Xudan Chai & Dong E. Liu , *Nature Communications*, 14, 5880 (2023). [https://doi.org/10.1038/s41467-023-41598-8](https://doi.org/10.1038/s41467-023-41598-8).



### Releases

This project follows a systematic release process to ensure users always have access to the latest stable version.

