from pytket.circuit import Circuit, OpType
from pytket.passes import ComposePhasePolyBoxes
from topt_proto.gadgetisation import REPLACE_HADAMARDS, get_n_internal_hadamards
from topt_proto.utils import get_n_conditional_xpaulis


def test_simple_circuit() -> None:
    circ = Circuit(3)
    circ.CX(0, 1).T(1).CX(0, 1).H(0).CX(0, 2).T(2).CX(0, 2).CX(0, 1).T(1).H(0).CX(0, 1)
    # draw(circ)
    ComposePhasePolyBoxes().apply(circ)
    assert circ.n_gates_of_type(OpType.H) == 2
    n_internal_h_gates = get_n_internal_hadamards(circ)
    assert n_internal_h_gates == 2
    # draw(circ)
    REPLACE_HADAMARDS.apply(circ)
    assert circ.n_qubits == 5
    assert get_n_conditional_xpaulis(circ) == n_internal_h_gates
    # draw(circ)
    assert get_n_conditional_xpaulis(circ) == 2
    # PROPAGATE_TERMINAL_PAULI.apply(circ)
    # assert get_n_conditional_xpaulis(circ) == 1
    # draw(circ)
    # PROPAGATE_TERMINAL_PAULI.apply(circ)
    # draw(circ)

    # circ = Circuit(3)
    # circ.CX(0, 1).T(1).CX(0, 1).H(0).CX(0, 2).T(2).CX(0, 2).CX(0, 1).T(1).H(0).CX(0, 1)
    # ComposePhasePolyBoxes().apply(circ)
