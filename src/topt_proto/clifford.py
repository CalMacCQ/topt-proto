from __future__ import annotations

from pytket import Qubit
from pytket._tket.circuit import Circuit, OpType, PauliExpCommutingSetBox
from pytket.circuit import PhasePolyBox
from pytket.extensions.qiskit import qiskit_to_tk
from pytket.passes import DecomposeBoxes
from pytket.pauli import Pauli, QubitPauliTensor
from pytket.tableau import UnitaryTableau
from qiskit.synthesis import synth_cnot_count_full_pmh

### Background discussed here
#  -> https://quantumcomputing.stackexchange.com/questions/39930/resynthesising-a-clifford-from-a-phase-polynomial-and-a-pauli-string

PAULI_DICT = {
    Pauli.I: OpType.noop,
    Pauli.X: OpType.X,
    Pauli.Y: OpType.Y,
    Pauli.Z: OpType.Z,
}


def pauli_tensor_to_circuit(pauli_tensor: QubitPauliTensor) -> Circuit:
    """Create a Circuit comprised of single qubit Pauli ops from a QubitPauliTensor."""
    pauli_circ = Circuit(len(pauli_tensor.string.to_list()))
    for qubit, pauli_op in pauli_tensor.string.map.items():
        pauli_circ.add_gate(PAULI_DICT[pauli_op], [qubit])

    return pauli_circ


def get_cnot_circuit(pbox: PhasePolyBox) -> Circuit:
    """Generate a CNOT circuit implementing the linear reversible circuit L."""
    # cheat by synthesising the CNOT circuit with qiskit and converting
    qc = synth_cnot_count_full_pmh(pbox.linear_transformation, section_size=2)
    tkc_cnot: Circuit = qiskit_to_tk(qc)
    return tkc_cnot


def get_pauli_conjugate(
    pbox: PhasePolyBox,
    input_pauli: QubitPauliTensor,
) -> QubitPauliTensor:
    """Given a PhasePolyBox (U) and a QubitPauliTensor (P), returns P' = L P L†."""

    l_cnot_circuit: Circuit = get_cnot_circuit(pbox=pbox).dagger()

    # Get L as a Tableau
    l_tableau = UnitaryTableau(l_cnot_circuit)

    return l_tableau.get_row_product(input_pauli)


def _parities_to_pauli_tensors(pbox: PhasePolyBox) -> list[QubitPauliTensor]:
    phase_poly = pbox.phase_polynomial
    tensor_list: list[QubitPauliTensor] = []
    for parity, phase in phase_poly.items():
        assert isinstance(phase, float)
        pauli_list: list[Pauli] = []
        qubit_list: list[Qubit] = []
        for count, boolean in enumerate(parity):
            qubit_list.append(Qubit(count))
            if boolean is True:
                pauli_list.append(Pauli.Z)
            else:
                pauli_list.append(Pauli.I)

        pauli_tensor = QubitPauliTensor(
            qubits=qubit_list,
            paulis=pauli_list,
            coeff=phase,
        )
        tensor_list.append(pauli_tensor)

    return tensor_list


def get_updated_paulis(
    pauli_tensors: list[QubitPauliTensor],
    new_pauli: QubitPauliTensor,
) -> list[QubitPauliTensor]:

    new_tensors: list[QubitPauliTensor] = []

    for pauli_op in pauli_tensors:
        if not pauli_op.commutes_with(new_pauli):
            new_coeff = pauli_op.coeff * (-2)
            new_tensors.append(
                QubitPauliTensor(string=pauli_op.string, coeff=new_coeff),
            )

    return new_tensors


def _get_phase_gadget_circuit(pauli_tensors: list[QubitPauliTensor]) -> Circuit:
    pauli_ops: list[tuple[list[Pauli], float]] = []
    for tensor in pauli_tensors:
        pauli_list = list(tensor.string.map.values())
        pair: tuple[list[Pauli], float] = (pauli_list, tensor.coeff.real)
        pauli_ops.append(pair)

    pauli_gadgets_sequence = PauliExpCommutingSetBox(pauli_ops)
    n_qubits = pauli_gadgets_sequence.n_qubits

    pauli_gadget_circ = Circuit(n_qubits).add_gate(
        pauli_gadgets_sequence,
        list(range(n_qubits)),
    )

    DecomposeBoxes().apply(pauli_gadget_circ)
    return pauli_gadget_circ


def synthesise_clifford(pbox: PhasePolyBox, input_pauli: QubitPauliTensor) -> Circuit:
    """Synthesise a Circuit implementing the end of Circuit Clifford Operator C."""

    # Get P' = L * P * L†
    new_pauli: QubitPauliTensor = get_pauli_conjugate(pbox, input_pauli)

    # Create a Circuit with the Pauli tensor P'
    pauli_circ: Circuit = pauli_tensor_to_circuit(new_pauli)

    # Get a list of Pauli {Z, I} tensors for D
    d_sequence: list[QubitPauliTensor] = _parities_to_pauli_tensors(pbox)

    # Get Q sequence
    q_sequence: list[QubitPauliTensor] = get_updated_paulis(
        d_sequence,
        new_pauli,
    )

    # Get a circuit to implement the Q operator sequence
    operator_circ: Circuit = _get_phase_gadget_circuit(q_sequence)

    # Combine circuits for P' and Q
    pauli_circ.append(operator_circ)
    return pauli_circ
