"""
Coherent Error Models for Gate Characterization

This module implements or utilizes techniques based on the coherent error models
for single- and two-qubit gates as described in the paper:
"Matrix-Element Amplification using Dynamical Decoupling".

The goal is to precisely characterize the parameters of these models, which
represent common coherent errors in quantum processors like gate angle errors,
phase errors, and crosstalk.

-------------------------------------------------------------------------------
1. Single-Qubit Gate Error Model (Arbitrary SU(2) Rotation)
-------------------------------------------------------------------------------
An imperfect single-qubit gate is modeled as a general SU(2) matrix,
parameterized by three angles:

R(μ, ζ, χ) = | exp(-iζ)cos(μ/2)    -i*exp(iχ)sin(μ/2)  |
             | -i*exp(-iχ)sin(μ/2)   exp(iζ)cos(μ/2)   |

Where the parameters correspond to:
  - μ (mu): The primary rotation angle.
            Error: Deviation from the target angle (e.g., π for an X gate).
            This is the gate angle error (over/under-rotation).

  - ζ (zeta): An error corresponding to a rotation around the Z-axis.
              Error: Non-zero values represent a phase error.

  - χ (chi): The azimuthal angle of the rotation axis in the XY-plane.
             Error: Deviation from the target axis (e.g., 0 for an X gate).
             This is a rotation axis error.

-------------------------------------------------------------------------------
2. Two-Qubit Gate Error Model (Controlled Rotation Style)
-------------------------------------------------------------------------------
An imperfect two-qubit interaction (like an iSWAP or C-Phase) is modeled
by the following unitary matrix W acting on the basis {|00>, |01>, |10>, |11>}:

W = | exp(iγ)      0                  0                   0         |
    |    0      exp(-iζ)cos(θ)    -i*exp(iχ)sin(θ)         0         |
    |    0     -i*exp(-iχ)sin(θ)    exp(iζ)cos(θ)          0         |
    |    0           0                  0              exp(-i(γ+φ)) |

Where the parameters correspond to:
  - θ (theta): The primary two-qubit interaction angle in the {|01>, |10>}
               subspace. This is the main two-qubit gate angle error.

  - ζ (zeta): A conditional single-qubit Z-rotation (phase) error that occurs
              during the two-qubit interaction.

  - χ (chi): A conditional single-qubit XY-rotation (axis) error that occurs
             during the two-qubit interaction.

  - γ (gamma): A parasitic phase accumulation (Stark shift) on spectator states,
               primarily affecting |00>. This is a form of crosstalk.

  - φ (phi): A differential phase error between the |00> and |11> states,
             corresponding to an unwanted ZZ interaction. This is another
             critical crosstalk error.
"""

# =============================================================================
# YOUR PYTHON CODE STARTS HERE
# e.g., import numpy as np
# e.g., from errorgnomark.experiments import ...
# =============================================================================

print("Python script starting...")