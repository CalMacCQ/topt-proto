from pytket import Qubit
from pytket._tket.circuit import Circuit, Conditional, OpType, PhasePolyBox, Op
from pytket.pauli import Pauli, QubitPauliTensor
from pytket.predicates import NoSymbolsPredicate, UserDefinedPredicate
from pytket.predicates import NoSymbolsPredicate
from pytket.passes import CustomPass


def _is_non_clifford(op: Op) -> bool:
    return not op.is_clifford()

def check_rz_angles(circ: Circuit) -> bool:
    """Check that all Rz gates in a Circuit can be implemented with Clifford+T gates."""
    if not NoSymbolsPredicate().verify(circ):
        symbol_msg = "Circuit contains symbolic angles."
        raise ValueError(symbol_msg)

    if circ.n_gates_of_type(OpType.Rz) == 0:
        no_rz_error = "Circuit does not contain any Rz gates."
        raise ValueError(no_rz_error)

    all_circuit_ops = [cmd.op for cmd in circ]

    all_non_clifford_ops = list(filter(_is_non_clifford, all_circuit_ops))

    all_rz_ops = circ.ops_of_type(OpType.Rz)

    all_t_ops = circ.ops_of_type(OpType.T)

    all_non_clifford_rz_ops = list(filter(_is_non_clifford, all_rz_ops))

    if len(all_non_clifford_ops) > len(all_non_clifford_rz_ops + all_t_ops):
        raise ValueError("We only check whether single qubit Z rotations are Clifford.")

    allowed_non_clifford_angles = [0.25, 0.75, 1.25, 1.75]

    return all(
        abs(op.params[0]) % 2 in allowed_non_clifford_angles
        for op in all_non_clifford_rz_ops
    )


CLIFFORD_PLUS_T_PREDICATE = UserDefinedPredicate(check_rz_angles)


def check_phasepolybox_angles(ppb: PhasePolyBox) -> bool:
    """Check that the underlying Circuit for a PhasePolyBox is Clifford + T."""
    return CLIFFORD_PLUS_T_PREDICATE.verify(ppb.get_circuit())


def _is_conditional_pauli_x(operation: Conditional) -> bool:
    return operation.op.type == OpType.X


def get_n_conditional_xpaulis(circ: Circuit) -> int:
    """Return the number of Conditonal-X gates in a Circuit."""
    conditional_ops: list[Op] = circ.ops_of_type(OpType.Conditional)
    conditional_xs: list[Op] = list(filter(_is_conditional_pauli_x, conditional_ops))
    return len(conditional_xs)


def initialise_registers(circ: Circuit) -> Circuit:
    circ_prime = Circuit()
    for qb in circ.qubits:
        circ_prime.add_qubit(qb)

    for bit in circ.bits:
        circ_prime.add_bit(bit)
    return circ_prime


def tensor_from_x_index(x_index: int, n_qubits: int) -> QubitPauliTensor:
    pauli_list = [Pauli.I] * n_qubits

    pauli_list[x_index] = Pauli.X

    qubit_list = [Qubit(n) for n in range(n_qubits)]

    return QubitPauliTensor(paulis=pauli_list, qubits=qubit_list)


def reverse_circuit(circ: Circuit) -> Circuit:
    new_circ = initialise_registers(circ)

    for cmd in reversed(circ.get_commands()):
        if cmd.op.type == OpType.Barrier:
            new_circ.add_barrier(cmd.qubits)
        else:
            new_circ.add_gate(cmd.op, cmd.args)

    return new_circ


def convert_t_to_rz(circ: Circuit) -> Circuit:
    circ_prime = Circuit(circ.n_qubits)

    for cmd in circ:
        if cmd.op.type == OpType.T:
            circ_prime.Rz(0.25, cmd.qubits[0])
        else:
            circ_prime.add_gate(cmd.op.type, cmd.op.params, cmd.qubits)

    return circ_prime


REPLACE_T_WITH_RZ = CustomPass(convert_t_to_rz)
