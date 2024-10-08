import pytest
from glob import glob
from pytket.qasm.qasm import circuit_from_qasm
from pytket._tket.circuit import Circuit, PhasePolyBox
from pytket.pauli import QubitPauliTensor
from pytket.predicates import CliffordCircuitPredicate
from pytket.passes import DecomposeBoxes
from pytket.utils import compare_unitaries


from topt_proto.clifford import synthesise_clifford, pauli_tensor_to_circuit
from topt_proto.utils import tensor_from_x_index, REPLACE_T_WITH_RZ


circuit_files = glob("qasm/*.qasm")


def get_unitary_test_circuit(
    p_box: PhasePolyBox, pauli: QubitPauliTensor, decompose: bool = False
) -> Circuit:
    circ = Circuit(p_box.n_qubits)
    u_circ = p_box.get_circuit()
    u_dg_circ = u_circ.dagger()
    circ.add_gate(PhasePolyBox(u_circ), u_circ.qubits)
    pauli_circ: Circuit = pauli_tensor_to_circuit(pauli)
    circ.append(pauli_circ)
    circ.add_gate(PhasePolyBox(u_dg_circ), u_dg_circ.qubits)
    if decompose:
        DecomposeBoxes().apply(circ)
    return circ


@pytest.mark.parametrize("qasm_file", circuit_files)
def test_clifford_synthesis(qasm_file: str) -> None:
    phase_poly_circ = circuit_from_qasm(qasm_file)
    pauli_op = tensor_from_x_index(x_index=1, n_qubits=phase_poly_circ.n_qubits)
    REPLACE_T_WITH_RZ.apply(phase_poly_circ)
    phase_poly_box = PhasePolyBox(phase_poly_circ)
    clifford_circ = synthesise_clifford(pbox=phase_poly_box, input_pauli=pauli_op)
    assert CliffordCircuitPredicate().verify(clifford_circ)
    unitary_test_circuit = get_unitary_test_circuit(
        p_box=phase_poly_box, pauli=pauli_op, decompose=True
    )
    test_unitary = unitary_test_circuit.get_unitary()
    result_unitary = clifford_circ.get_unitary()
    assert compare_unitaries(test_unitary, result_unitary)
