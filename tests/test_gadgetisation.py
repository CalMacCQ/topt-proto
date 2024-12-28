import pytest

from pytket._tket.circuit import Circuit
from pytket.passes import DecomposeBoxes, ComposePhasePolyBoxes

from topt_proto.gadgetisation import (
    REPLACE_HADAMARDS,
    get_n_internal_hadamards,
)
from topt_proto.utils import get_n_conditional_paulis


# After ComposePhasePolyBoxes is applied, this circuit has no external Hadamards
# Four internal hadamards between the first and last non-Clifford.
circ0 = (
    Circuit(4)
    .T(0)
    .CX(0, 3)
    .CX(2, 1)
    .CX(3, 1)
    .T(3)
    .H(0)
    .H(1)
    .CZ(0, 3)
    .H(2)
    .CRy(0.25, 0, 3)
)

# After ComposePhasePolyBoxes is applied this circuit has two
# External Hadamards, one before and one after the boundary
# It also has two internal Hadamards.
circ1 = Circuit(4).CCX(0, 1, 2).T(2).CX(2, 1).T(1).CCX(0, 1, 2)

# After ComposePhasePolyBoxes is applied this circuit has one
# External Hadamard before the boundary and eight internal Hadamards.
circ2 = Circuit(4).CX(0, 3).T(3).H(0).T(2).H(1).CZ(0, 3).H(2).CRy(0.25, 0, 3)

# Very simple test case. One internal Hadamard, zero external.
circ3 = Circuit(2).CX(0, 1).T(1).CX(0, 1).H(0).CX(0, 1).T(1).CX(0, 1)

# Two internal Hadamards after ComposePhasePolyBoxes, zero external.
circ4 = Circuit(2).CX(0, 1).T(1).CX(0, 1).H(0).CX(0, 1).T(1).CX(0, 1)

circuits = [circ0, circ1, circ2, circ3, circ4]


@pytest.mark.parametrize("circ", circuits)
def test_h_gadgetisation(circ: Circuit) -> None:
    n_qubits_without_ancillas = circ.n_qubits
    DecomposeBoxes().apply(circ)
    ComposePhasePolyBoxes().apply(circ)
    n_internal_h_gates = get_n_internal_hadamards(circ)
    REPLACE_HADAMARDS.apply(circ)
    assert get_n_conditional_paulis(circ) == n_internal_h_gates
    assert circ.n_qubits == n_qubits_without_ancillas + n_internal_h_gates


# QFT circuit builder function, used in testing.
def build_qft_circuit(n_qubits: int) -> Circuit:
    circ = Circuit(n_qubits, name="$$QFT$$")
    for i in range(n_qubits):
        circ.H(i)
        for j in range(i + 1, n_qubits):
            circ.CU1(1 / 2 ** (j - i), j, i)
    for k in range(0, n_qubits // 2):
        circ.SWAP(k, n_qubits - k - 1)
    return circ


# Test the QFT circuits for varying number of qubits.
n_qubit_cases = [2, 3, 7, 10]


# The QFT has a regular structure, 1 external Hadamard
# (After ComposePhasePolyBoxes) and (n-1) internal.
@pytest.mark.parametrize("n_qubits", n_qubit_cases)
def test_gadgetisation_qft(n_qubits: int) -> None:
    qft_circ: Circuit = build_qft_circuit(n_qubits)
    ComposePhasePolyBoxes().apply(qft_circ)
    n_internal_h_gates = get_n_internal_hadamards(qft_circ)
    assert n_internal_h_gates == n_qubits - 1
    REPLACE_HADAMARDS.apply(qft_circ)
    assert get_n_conditional_paulis(qft_circ) == n_internal_h_gates
    assert qft_circ.n_qubits == n_qubits + n_internal_h_gates
