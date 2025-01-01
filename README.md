## Language

- English｜[简体中文](https://github.com/ChaiXD0137/ErrorGnoMark/blob/master/README_CN.md)

---

# ErrorGnoMark: Quantum Chip Error Diagnosis & Benchmark

## Overview

ErrorGnoMark (Error Diagnose & Benchmark) is a comprehensive tool developed by the Quantum Operating System and Software Development Team at the Beijing Institute of Quantum Information Science. It aims to provide a complete and thorough benchmark and diagnostic information for quantum chip errors, covering different layers of the quantum operating system: Physical Layer, Quantum Gate (Circuit) Layer, and Application Layer. It evaluates key dimensions such as Scalability, Quality, and Speed[^1]. 



### Potential Applications

<p align="center">
  <img src="./figs/f1.jpg" alt="text" width="580px">
</p>



ErrorGnoMark will be invaluable at every step toward realizing a functional quantum computer. Below are the potential applications of our ErrorGnoMark tool:


- **Hardware Control**: Quantum chip calibration process, building more reliable simulators, optimal quantum control, etc. For example, the benchmarking mode can create a gate-level database[^2], while the pulse-level mode can characterize control parameters like dephasing.

- **Compiler Optimization**: Improving compiler optimization performance with error information like crosstalk. 

- **Cloud & Direct User Access**: Real-time monitoring of chip performance (errors), QEC experiments, etc. 


## Version Information

**ErrorGnoMark 0.1.0**  
Note: This is the initial version. Future updates will follow the progress in relevant research fields and application requirements.

## Installation

### Via pip

We recommend installing ErrorGnoMark using pip:

\`\`\`sh
pip install ErrorGnoMark
\`\`\`


### Via GitHub

Alternatively, you can download all files from GitHub and install locally:

### Download and install via GitHub
You can also download all the files and install Errorgnomark locally 

\`\`\`sh
git clone https://github.com/BAQIS-Quantum/ErrorGnoMark
cd errorgnomark
pip install -e .
\`\`\`

## Running Example Programs

To verify the installation, you can run example programs:

\`\`\`sh
cd Example
1-example-CSB-q2.py
\`\`\`

## Getting Started and Development

### Overview

Before using ErrorGnoMark for quantum error diagnosis, we recommend users start by reading the introduction to understand the platform. The Quick Start Guide will walk you through using the quantum error diagnosis service and building your first program. Next, we encourage users to explore more application cases provided in the tutorials. Finally, users can apply ErrorGnoMark to solve research and engineering problems. For detailed API documentation, refer to our API documentation page.

### Tutorials

ErrorGnoMark provides detailed tutorials from basic to advanced topics, available on our website. We recommend downloading and using Jupyter Notebooks for those interested in research or development.

**Table of Contents**:
- Overview of Quantum Chip Errors (Technical adjustments, issues, and solutions)
- Quantum Benchmarking
  - Hardware Layer Characterization
  - Quantum Gate (Circuit) Benchmarking[^3]
  - Quantum Chip Application Performance Testing

- Databases for Benchmarking Score and Characterization in Hardware Control
In the context of calibration, our goal is to focus on the {characterization + benchmarking} data. This can be used to build two kinds of databases.

  - Characterization Data: 
  This pertains to pulse-level control parameters, such as T1 and T2 times, among other control metrics. These parameters are crucial for understanding the performance and limitations of quantum hardware at a fundamental level.
  - Benchmarking Data: This involves various benchmark scores at the gate level, providing a quantitative measure of the performance of quantum gates and overall system reliability

These databases are structured to provide a clear distinction between pulse-level and gate-level data. For gate-level compilation, the system directly utilizes the benchmarking data. However, for pulse-level compilation, the focus shifts towards quantum optimal control, leveraging the characterization data for fine-tuning and enhancing quantum operations.


## A User Guide for Local QC Measurement & Control System

Assuming you are a user of a local quantum chip (QC) measurement & control system, you have full access to the entire chip information online, including topology and connectivity.






## Feedback

We encourage users to provide feedback, report issues, and suggest improvements via GitHub Issues or email us at chaixd@baqis.ac.cn. Collaboration with the community will help make ErrorGnoMark better!


## License

ErrorGnoMark is licensed under the GPL-3.0 license.

## References

<a name="ref1"></a> Author Name, "Title of the Paper," Journal Name, vol. XX, no. XX, pp. XX-XX, Year.


[^1]: **Quality, Speed, and Scale: Three key attributes to measure the performance of near-term quantum computers**, Andrew Wack, Hanhee Paik, Ali Javadi-Abhari, Petar Jurcevic, Ismael Faro, Jay M. Gambetta, Blake R. Johnson, 2021, arXiv:2110.14108 [quant-ph].

[^2]: **Optimizing quantum gates towards the scale of logical qubits**, Klimov, P.V., Bengtsson, A., Quintana, C. et al. . Nat Commun 15, 2442 (2024). https://doi.org/10.1038/s41467-024-46623-y.

[^3]: **Gu, Y., Zhuang, WF., Chai, X. et al. Benchmarking universal quantum gates via channel spectrum**. Nat Commun 14, 5880 (2023). https://doi.org/10.1038/s41467-023-41598-8



## About

A project to perform benchmarking and error diagnosis for a quantum chip.

---

<!-- ### Resources

- **Readme**
- **License**: GPL-3.0 license -->

<!-- ### Activity

- **Stars**: 0 stars
- **Watchers**: 1 watching
- **Forks**: 0 forks -->

### Releases

No releases published.

<!-- ### Packages

No packages published. -->

---

**Languages**:  
Python 100.0%
---
