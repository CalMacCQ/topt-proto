from __future__ import annotations

from pytket._tket.circuit import CircBox, Circuit, Command, OpType
from pytket.passes import CustomPass
from pytket.predicates import GateSetPredicate

FSWAP_CIRC = Circuit(2, name="FSWAP").CZ(0, 1).SWAP(0, 1)

FSWAP = CircBox(FSWAP_CIRC)

HADAMARD_REPLACE_PREDICATE = GateSetPredicate({OpType.H, OpType.PhasePolyBox})


def get_n_internal_hadamards(circ: Circuit) -> int:
    """Return the number of Hadamard gates between the first and last non-Clifford gate in the Circuit."""
    if not HADAMARD_REPLACE_PREDICATE.verify(circ):
        pred_msg = "Circuit must contain only OpType.H and OpType.PhasePolyBox OpTypes."
        raise ValueError(pred_msg)

    total_h_count = circ.n_gates_of_type(OpType.H)

    # Its Possible that a PhasePolyBox is Clifford. Handled in _count_hadamards.

    # Count number of Hadamards until we encounter a PhasePolyBox
    lhs_count = _count_hadamards(circ.get_commands())

    # Same but from the end of the circuit
    rhs_count = _count_hadamards(reversed(circ.get_commands()))

    return total_h_count - (lhs_count + rhs_count)


def _count_hadamards(commands: list[Command]) -> int:
    h_count = 0
    for cmd in commands:
        if cmd.op.type == OpType.H:
            h_count += 1
        # If we encounter a non-Clifford PhasePolyBox, stop counting.
        elif cmd.op.type == OpType.PhasePolyBox and not cmd.op.is_clifford():
            break
    return h_count


# This rather messy helper function tells us the bounds
#  of the non-Clifford region of our circuit. It gives us back
#  the indices of the first and last non-Clifford PhasePolyBox.
# As its possible for a PhasePolyBox to be Clifford, we handle
# this case. TODO:  maybe clean this up.
def get_clifford_boundary(circ: Circuit) -> tuple[int, int]:
    phase_poly_boxes = circ.ops_of_type(OpType.PhasePolyBox)
    first_index = next(
        count for count, box in enumerate(phase_poly_boxes) if not box.is_clifford()
    )
    assert first_index >= 0
    last_index = next(
        len(phase_poly_boxes) - 1 - count
        for count, box in enumerate(phase_poly_boxes[::-1])
        if not box.is_clifford()
    )
    assert last_index <= len(phase_poly_boxes) - 1
    return first_index, last_index


# Note that this pass assumes that we are in the {H, PhasePolyBox} gateset
#  (hence the HADAMARD_REPLACE_PREDICATE). Circuits not in this gateset can
# be converted to it by applying the ComposePhasePolyBoxes pass.
def gadgetise_hadamards(circ: Circuit) -> Circuit:
    """Replace all internal Hadamard gates with measurement gadgets."""
    internal_h_count = get_n_internal_hadamards(circ)

    circ_prime = Circuit(circ.n_qubits)
    z_ancillas = circ_prime.add_q_register("z_ancillas", internal_h_count)
    ancilla_bits = circ_prime.add_c_register("bits", internal_h_count)

    for ancilla in z_ancillas:
        circ_prime.H(ancilla)

    circ_prime.add_barrier(list(z_ancillas))

    lower, upper = get_clifford_boundary(circ)
    ancilla_index = 0
    box_counter = 0
    for cmd in circ:
        if cmd.op.type == OpType.PhasePolyBox:
            box_counter += 1
            circ_prime.add_gate(cmd.op, cmd.args)
        else:
            # Checks whether we are between the first and last non-Clifford gate.
            inside_boundary = lower < box_counter <= upper
            if inside_boundary:
                # If inside boundary, add Hadamard as a measurement gadget.
                circ_prime.add_gate(FSWAP, [cmd.qubits[0], z_ancillas[ancilla_index]])
                circ_prime.add_gate(OpType.H, [z_ancillas[ancilla_index]])
                circ_prime.Measure(
                    z_ancillas[ancilla_index], ancilla_bits[ancilla_index]
                )
                circ_prime.X(
                    cmd.qubits[0],
                    condition_bits=[ancilla_bits[ancilla_index]],
                    condition_value=1,
                )
                ancilla_index += 1
            else:
                # If outside boundary, add Hadamard as usual.
                circ_prime.add_gate(OpType.H, cmd.qubits)

    return circ_prime


REPLACE_HADAMARDS = CustomPass(gadgetise_hadamards)
