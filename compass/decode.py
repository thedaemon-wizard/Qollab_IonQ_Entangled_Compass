"""Counts -> mean parity of every register, by qubit position (Qiskit keys are little-endian:
qubit i is character n - 1 - i). The canary qubit 0 must read 1; if it does not, the bit order
is wrong and we stop rather than guess."""

from __future__ import annotations

import math

from compass.circuits import Layout


class BitOrderError(ValueError):
    pass


def decode(counts: dict[str, int], lay: Layout, min_canary: float = 0.9) -> dict:
    n = lay.n_qubits
    keys = {k.replace(" ", "").zfill(n): v for k, v in counts.items()}
    total = sum(keys.values())
    if total == 0:
        raise ValueError("no shots in the result")
    canary = sum(v for k, v in keys.items() if k[n - 1] == "1") / total
    if canary < min_canary:
        reversed_end = sum(v for k, v in keys.items() if k[0] == "1") / total
        raise BitOrderError(f"canary fraction {canary:.3f} (reversed-end fraction {reversed_end:.3f})")
    regs = {}
    for reg in lay.registers:
        s = 0
        for k, v in keys.items():
            ones = sum(k[n - 1 - q] == "1" for q in reg.qubits)
            s += v if ones % 2 == 0 else -v
        mean = s / total
        regs[reg.name] = {
            "mean": mean,
            "var": (1 - mean * mean) / total,
            "se": math.sqrt((1 - mean * mean) / total),
        }
    return {"shots": total, "canary": canary, "registers": regs}
