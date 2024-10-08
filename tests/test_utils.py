from topt_proto.utils import (
    check_rz_angles,
    check_phasepolybox,
    get_n_conditional_paulis,
    REPLACE_T_WITH_RZ,
)
from pytket._tket.circuit import Circuit, PhasePolyBox, OpType
from pytket.qasm.qasm import circuit_from_qasm
from pytket._tket.unit_id import Bit, Qubit
from pytket.predicates import GateSetPredicate
from glob import glob
import pytest


def test_clifford_plus_t_checking() -> None:
    circ = (
        Circuit(2)
        .CX(0, 1)
        .Rz(1 / 4, 1)
        .CX(0, 1)
        .Rz(-1 / 4, 1)
        .CX(0, 1)
        .Rz(0.75, 1)
        .CX(0, 1)
        .T(0)
        .Rz(-0.75, 0)
        .Rz(-1.25, 1)
    )
    assert check_rz_angles(circ)
    circ.Rz(0.61, 0)
    assert not check_rz_angles(circ)


def test_phasepolybox_checking() -> None:
    circ = Circuit(2).CX(0, 1).Rz(0.5, 0).CX(0, 1)
    ppb1 = PhasePolyBox(circ)
    assert check_phasepolybox(ppb1)
    circ.Rz(0.19, 1)
    ppb2 = PhasePolyBox(circ)
    assert not check_phasepolybox(ppb2)


def test_conditional_counting() -> None:
    circ = Circuit(3).X(0).CCX(0, 1, 2)
    circ.measure_all()
    assert get_n_conditional_paulis(circ) == 0
    circ.X(
        Qubit(0),
        condition_bits=[Bit(0)],
        condition_value=1,
    )
    assert get_n_conditional_paulis(circ) == 1
    circ.Y(
        Qubit(0),
        condition_bits=[Bit(0)],
        condition_value=1,
    )
    # Y is not counted, only X
    assert get_n_conditional_paulis(circ) == 1
    circ.CZ(
        Qubit(0),
        Qubit(1),
        condition_bits=[Bit(0)],
        condition_value=1,
    )
    assert get_n_conditional_paulis(circ) == 1
    circ.X(
        Qubit(2),
        condition_bits=[Bit(1)],
        condition_value=0,
    )
    assert get_n_conditional_paulis(circ) == 2


circuit_files = glob("qasm/*.qasm")


@pytest.mark.parametrize("qasm_file", circuit_files)
def test_t_replacement(qasm_file: str) -> None:
    CNOT_RZ_PREDICATE = GateSetPredicate({OpType.CX, OpType.Rz})
    phase_poly_circ = circuit_from_qasm(qasm_file)
    REPLACE_T_WITH_RZ.apply(phase_poly_circ)
    assert CNOT_RZ_PREDICATE.verify(phase_poly_circ)
