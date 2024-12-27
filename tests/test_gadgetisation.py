import pytest

from pytket._tket.circuit import Circuit
from pytket.passes import DecomposeBoxes, ComposePhasePolyBoxes

from topt_proto.gadgetisation import REPLACE_HADAMARDS, get_n_internal_hadamards
from topt_proto.utils import get_n_conditional_paulis


def test_h_gadgetisation() -> None:
    circ = (
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
    n_qubits_without_ancillas = circ.n_qubits
    DecomposeBoxes().apply(circ)
    ComposePhasePolyBoxes().apply(circ)
    n_internal_h_gates = get_n_internal_hadamards(circ)
    REPLACE_HADAMARDS.apply(circ)
    assert get_n_conditional_paulis(circ) == n_internal_h_gates
    assert circ.n_qubits == n_qubits_without_ancillas + n_internal_h_gates


def build_qft_circuit(n_qubits: int) -> Circuit:
    circ = Circuit(n_qubits, name="$$QFT$$")
    for i in range(n_qubits):
        circ.H(i)
        for j in range(i + 1, n_qubits):
            circ.CU1(1 / 2 ** (j - i), j, i)
    for k in range(0, n_qubits // 2):
        circ.SWAP(k, n_qubits - k - 1)
    return circ


n_qubit_cases = [2, 3, 7, 10]


@pytest.mark.parametrize("n_qubits", n_qubit_cases)
def test_gadgetisation_qft(n_qubits: int) -> None:
    qft_circ: Circuit = build_qft_circuit(n_qubits)
    ComposePhasePolyBoxes().apply(qft_circ)
    n_internal_h_gates = get_n_internal_hadamards(qft_circ)
    assert n_internal_h_gates == n_qubits - 1
    REPLACE_HADAMARDS.apply(qft_circ)
    assert get_n_conditional_paulis(qft_circ) == n_internal_h_gates
    assert qft_circ.n_qubits == n_qubits + n_internal_h_gates
