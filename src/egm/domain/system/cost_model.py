"""
Hardware-Aware Cost Model Interface.

Transforms hardware snapshot data into cost metrics usable by
compilation and routing strategies.

This module does not perform physical error modeling. It only
maps measured performance data into optimization weights.
"""