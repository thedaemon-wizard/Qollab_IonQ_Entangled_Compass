"""The sensor circuit: every sensor of one comparison packed into ONE circuit (one job).

Qubit 0 is a canary (X, then measure: it must read 1 on every shot) that checks the bit order
of the returned keys. Each register is a sensor: a GHZ state of m qubits (m = 1 is a single
qubit), or one qubit that passes through the field m times (multi-pass). All see the same
field step delta; X registers read cos(m delta), Y registers sin(m delta).

Layout "A" (17 qubits): no added noise; the backend's own gate noise, if any, is all there is.
Layout "B" (21 qubits): an extra ancilla per register adds independent dephasing gamma per
qubit. The ancilla starts in |+> and couples by CX.Rz(b).CX, so the register sees Rz(+b) or
Rz(-b) with equal odds; with cos b = exp(-m gamma) this is exactly independent dephasing of each
of the m qubits, seen through the GHZ coherence (Huelga et al. 1997: it decays as
exp(-gamma)^m). Ancillas are measured and ignored.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

from qiskit import QuantumCircuit

from compass import model


@dataclass(frozen=True)
class Register:
    name: str  # e.g. "G4X"
    kind: str  # "ghz" or "mp" (multi-pass single qubit)
    m: int  # qubits (ghz) or passes (mp): the phase is multiplied by m
    basis: str  # "X" or "Y"
    qubits: tuple[int, ...]
    ancilla: int | None = None


@dataclass(frozen=True)
class Layout:
    name: str
    n_qubits: int
    registers: tuple[Register, ...]

    def register(self, name: str) -> Register:
        return next(r for r in self.registers if r.name == name)


def _ghz_registers() -> list[Register]:
    regs, q = [], 1
    for m in (1, 2, 4):
        for basis in ("X", "Y"):
            regs.append(Register(f"G{m}{basis}", "ghz", m, basis, tuple(range(q, q + m))))
            q += m
    return regs


def layout(name: str) -> Layout:
    regs = _ghz_registers()  # qubits 1..14
    if name == "A":
        regs += [Register("MP4X", "mp", 4, "X", (15,)), Register("MP4Y", "mp", 4, "Y", (16,))]
        return Layout("A", 17, tuple(regs))
    if name == "B":
        with_anc = [
            Register(r.name, r.kind, r.m, r.basis, r.qubits, ancilla=15 + i) for i, r in enumerate(regs)
        ]
        return Layout("B", 21, tuple(with_anc))
    raise ValueError(f"unknown layout {name!r}")


def build(lay: Layout, delta: float, gamma: float = 0.0) -> QuantumCircuit:
    """The packed circuit for one field step `delta` (rad) and dephasing `gamma` (layout B)."""
    qc = QuantumCircuit(lay.n_qubits, lay.n_qubits, name=f"compass_{lay.name}")
    qc.x(0)
    for reg in lay.registers:
        q = reg.qubits
        qc.h(q[0])
        if reg.kind == "ghz":
            for a, b in pairwise(q):
                qc.cx(a, b)
            for qubit in q:
                qc.rz(delta, qubit)
        else:
            for _ in range(reg.m):
                qc.rz(delta, q[0])
        if reg.ancilla is not None:
            b = model.knob_angle(reg.m, gamma)
            qc.h(reg.ancilla)
            qc.cx(reg.ancilla, q[0])
            qc.rz(b, q[0])
            qc.cx(reg.ancilla, q[0])
        if reg.basis == "Y":
            qc.sdg(q[0])
        for qubit in q:
            qc.h(qubit)
    qc.measure(range(lay.n_qubits), range(lay.n_qubits))
    return qc


def model_visibility(reg: Register, gamma: float = 0.0, r1: float = 0.0, r2: float = 0.0) -> float:
    """Expected visibility of one register: gate noise (documented model) times dephasing."""
    if reg.kind == "mp":  # one qubit: H, m Rz, H
        vg = (1 - r1) ** 2 * ((1 - r2) ** 2 if reg.ancilla is not None else 1.0)
    else:
        vg = model.gate_visibility(reg.m, r1, r2, knob=reg.ancilla is not None)
    return vg * (model.dephasing_visibility(reg.m, gamma) if reg.ancilla is not None else 1.0)
