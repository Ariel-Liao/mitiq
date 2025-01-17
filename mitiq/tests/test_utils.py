"""Tests for utility functions."""
from copy import deepcopy
import pytest
import numpy as np
import cirq
from cirq import LineQubit, Circuit, ControlledGate, X, Y, Z, H, CNOT, S, T, MeasurementGate, ops, depolarize
from mitiq.utils import _append_measurements, _are_close_dict, _equal, _is_measurement, _simplify_gate_exponent, _simplify_circuit_exponents, _max_ent_state_circuit, _circuit_to_choi, _operation_to_choi, _pop_measurements

@pytest.mark.parametrize('require_qubit_equality', [True, False])
def test_circuit_equality_identical_qubits(require_qubit_equality):
    qreg = cirq.NamedQubit.range(5, prefix='q_')
    circA = cirq.Circuit(cirq.ops.H.on_each(*qreg))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qreg))
    assert circA is not circB
    assert _equal(circA, circB, require_qubit_equality=require_qubit_equality)

@pytest.mark.parametrize('require_qubit_equality', [True, False])
def test_circuit_equality_nonidentical_but_equal_qubits(require_qubit_equality):
    n = 5
    qregA = cirq.NamedQubit.range(n, prefix='q_')
    qregB = cirq.NamedQubit.range(n, prefix='q_')
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert circA is not circB
    assert _equal(circA, circB, require_qubit_equality=require_qubit_equality)

@pytest.mark.order(0)
def test_circuit_equality_linequbit_gridqubit_equal_indices():
    n = 10
    qregA = cirq.LineQubit.range(n)
    qregB = [cirq.GridQubit(x, 0) for x in range(n)]
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert _equal(circA, circB, require_qubit_equality=False)
    assert not _equal(circA, circB, require_qubit_equality=True)

@pytest.mark.order(0)
def test_circuit_equality_linequbit_gridqubit_unequal_indices():
    n = 10
    qregA = cirq.LineQubit.range(n)
    qregB = [cirq.GridQubit(x + 3, 0) for x in range(n)]
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert _equal(circA, circB, require_qubit_equality=False)
    assert not _equal(circA, circB, require_qubit_equality=True)

@pytest.mark.order(0)
def test_circuit_equality_linequbit_namedqubit_equal_indices():
    n = 8
    qregA = cirq.LineQubit.range(n)
    qregB = cirq.NamedQubit.range(n, prefix='q_')
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert _equal(circA, circB, require_qubit_equality=False)
    assert not _equal(circA, circB, require_qubit_equality=True)

@pytest.mark.order(0)
def test_circuit_equality_linequbit_namedqubit_unequal_indices():
    n = 11
    qregA = cirq.LineQubit.range(n)
    qregB = [cirq.NamedQubit(str(x + 10)) for x in range(n)]
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert _equal(circA, circB, require_qubit_equality=False)
    assert not _equal(circA, circB, require_qubit_equality=True)

@pytest.mark.order(0)
def test_circuit_equality_gridqubit_namedqubit_equal_indices():
    n = 8
    qregA = [cirq.GridQubit(0, x) for x in range(n)]
    qregB = cirq.NamedQubit.range(n, prefix='q_')
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert _equal(circA, circB, require_qubit_equality=False)
    assert not _equal(circA, circB, require_qubit_equality=True)

@pytest.mark.order(0)
def test_circuit_equality_gridqubit_namedqubit_unequal_indices():
    n = 5
    qregA = [cirq.GridQubit(x + 2, 0) for x in range(n)]
    qregB = [cirq.NamedQubit(str(x + 10)) for x in range(n)]
    circA = cirq.Circuit(cirq.ops.H.on_each(*qregA))
    circB = cirq.Circuit(cirq.ops.H.on_each(*qregB))
    assert _equal(circA, circB, require_qubit_equality=False)
    assert not _equal(circA, circB, require_qubit_equality=True)

@pytest.mark.order(0)
def test_circuit_equality_unequal_measurement_keys_terminal_measurements():
    base_circuit = cirq.testing.random_circuit(qubits=5, n_moments=10, op_density=0.99, random_state=1)
    qreg = list(base_circuit.all_qubits())
    circ1 = deepcopy(base_circuit)
    circ1.append((cirq.measure(q, key='one') for q in qreg))
    circ2 = deepcopy(base_circuit)
    circ2.append((cirq.measure(q, key='two') for q in qreg))
    assert _equal(circ1, circ2, require_measurement_equality=False)
    assert not _equal(circ1, circ2, require_measurement_equality=True)

@pytest.mark.parametrize('require_measurement_equality', [True, False])
def test_circuit_equality_equal_measurement_keys_terminal_measurements(require_measurement_equality):
    base_circuit = cirq.testing.random_circuit(qubits=5, n_moments=10, op_density=0.99, random_state=1)
    qreg = list(base_circuit.all_qubits())
    circ1 = deepcopy(base_circuit)
    circ1.append((cirq.measure(q, key='z') for q in qreg))
    circ2 = deepcopy(base_circuit)
    circ2.append((cirq.measure(q, key='z') for q in qreg))
    assert _equal(circ1, circ2, require_measurement_equality=require_measurement_equality)

@pytest.mark.order(0)
def test_circuit_equality_unequal_measurement_keys_nonterminal_measurements():
    base_circuit = cirq.testing.random_circuit(qubits=5, n_moments=10, op_density=0.99, random_state=1)
    end_circuit = cirq.testing.random_circuit(qubits=5, n_moments=5, op_density=0.99, random_state=2)
    qreg = list(base_circuit.all_qubits())
    circ1 = deepcopy(base_circuit)
    circ1.append((cirq.measure(q, key='one') for q in qreg))
    circ1 += end_circuit
    circ2 = deepcopy(base_circuit)
    circ2.append((cirq.measure(q, key='two') for q in qreg))
    circ2 += end_circuit
    assert _equal(circ1, circ2, require_measurement_equality=False)
    assert not _equal(circ1, circ2, require_measurement_equality=True)

@pytest.mark.parametrize('require_measurement_equality', [True, False])
def test_circuit_equality_equal_measurement_keys_nonterminal_measurements(require_measurement_equality):
    base_circuit = cirq.testing.random_circuit(qubits=5, n_moments=10, op_density=0.99, random_state=1)
    end_circuit = cirq.testing.random_circuit(qubits=5, n_moments=5, op_density=0.99, random_state=2)
    qreg = list(base_circuit.all_qubits())
    circ1 = deepcopy(base_circuit)
    circ1.append((cirq.measure(q, key='z') for q in qreg))
    circ1 += end_circuit
    circ2 = deepcopy(base_circuit)
    circ2.append((cirq.measure(q, key='z') for q in qreg))
    circ2 += end_circuit
    assert _equal(circ1, circ2, require_measurement_equality=require_measurement_equality)

@pytest.mark.order(0)
def test_is_measurement():
    """Tests for checking if operations are measurements."""
    qbit = LineQubit(0)
    circ = Circuit([ops.H.on(qbit), ops.X.on(qbit), ops.Z.on(qbit), ops.measure(qbit)])
    for i, op in enumerate(circ.all_operations()):
        if i == 3:
            assert _is_measurement(op)
        else:
            assert not _is_measurement(op)

@pytest.mark.order(0)
def test_pop_measurements_and_add_measurements():
    """Tests popping measurements from a circuit.."""
    qreg = LineQubit.range(3)
    circ = Circuit([ops.H.on_each(qreg)], [ops.T.on(qreg[0])], [ops.measure(qreg[1])], [ops.CNOT.on(qreg[0], qreg[2])], [ops.measure(qreg[0], qreg[2])])
    copy = deepcopy(circ)
    measurements = _pop_measurements(copy)
    correct = Circuit([ops.H.on_each(qreg)], [ops.T.on(qreg[0])], [ops.CNOT.on(qreg[0], qreg[2])])
    assert _equal(copy, correct)
    _append_measurements(copy, measurements)
    assert _equal(copy, circ)

@pytest.mark.parametrize('gate', [X ** 3, Y ** (-3), Z ** (-1), H ** (-1)])
def test_simplify_gate_exponent(gate):
    assert _simplify_gate_exponent(gate).exponent == 1
    assert _simplify_gate_exponent(gate) == gate

@pytest.mark.parametrize('gate', [T ** (-1), S ** (-1), MeasurementGate(1)])
def test_simplify_gate_exponent_with_gates_that_cannot_be_simplified(gate):
    assert _simplify_gate_exponent(gate).__repr__() == gate.__repr__()

@pytest.mark.order(0)
def test_simplify_circuit_exponents_controlled_gate():
    circuit = Circuit(ControlledGate(CNOT, num_controls=1).on(*LineQubit.range(3)))
    copy = circuit.copy()
    _simplify_circuit_exponents(circuit)
    assert _equal(circuit, copy)

@pytest.mark.order(0)
def test_simplify_circuit_exponents():
    qreg = LineQubit.range(2)
    circuit = Circuit([H.on(qreg[0]), CNOT.on(*qreg), Z.on(qreg[1])])
    inverse_circuit = cirq.inverse(circuit)
    inverse_repr = inverse_circuit.__repr__()
    inverse_qasm = inverse_circuit._to_qasm_output().__str__()
    expected_inv = Circuit([Z.on(qreg[1]), CNOT.on(*qreg), H.on(qreg[0])])
    expected_repr = expected_inv.__repr__()
    expected_qasm = expected_inv._to_qasm_output().__str__()
    assert inverse_circuit == expected_inv
    assert inverse_repr != expected_repr
    assert inverse_qasm != expected_qasm
    _simplify_circuit_exponents(inverse_circuit)
    simplified_repr = inverse_circuit.__repr__()
    simplified_qasm = inverse_circuit._to_qasm_output().__str__()
    assert inverse_circuit == expected_inv
    assert simplified_repr == expected_repr
    assert simplified_qasm == expected_qasm

@pytest.mark.order(0)
def test_simplify_circuit_exponents_with_non_self_inverse_gates():
    qreg = LineQubit.range(2)
    circuit = Circuit([S.on(qreg[0]), T.on(qreg[1])])
    inverse_circuit = cirq.inverse(circuit)
    inverse_repr = inverse_circuit.__repr__()
    inverse_qasm = inverse_circuit._to_qasm_output().__str__()
    _simplify_circuit_exponents(inverse_circuit)
    simplified_repr = inverse_circuit.__repr__()
    simplified_qasm = inverse_circuit._to_qasm_output().__str__()
    assert simplified_repr == inverse_repr
    assert simplified_qasm == inverse_qasm

@pytest.mark.order(0)
def test_are_close_dict():
    """Tests the _are_close_dict function."""
    dict1 = {'a': 1, 'b': 0.0}
    dict2 = {'a': 1, 'b': 0.0 + 1e-10}
    assert _are_close_dict(dict1, dict2)
    assert _are_close_dict(dict2, dict1)
    dict2 = {'b': 0.0 + 1e-10, 'a': 1}
    assert _are_close_dict(dict1, dict2)
    assert _are_close_dict(dict2, dict1)
    dict2 = {'a': 1, 'b': 1.0}
    assert not _are_close_dict(dict1, dict2)
    assert not _are_close_dict(dict2, dict1)
    dict2 = {'b': 1, 'a': 0.0}
    assert not _are_close_dict(dict1, dict2)
    assert not _are_close_dict(dict2, dict1)
    dict2 = {'a': 1, 'b': 0.0, 'c': 1}
    assert not _are_close_dict(dict1, dict2)
    assert not _are_close_dict(dict2, dict1)

@pytest.mark.order(0)
def test_max_ent_state_circuit():
    """Tests 1-qubit and 2-qubit maximally entangled states are generated."""
    two_state = np.array([1, 0, 0, 1]) / np.sqrt(2)
    four_state = np.array(3 * [1, 0, 0, 0, 0] + [1]) / 2.0
    assert np.allclose(_max_ent_state_circuit(2).final_state_vector(), two_state)
    assert np.allclose(_max_ent_state_circuit(4).final_state_vector(), four_state)

@pytest.mark.order(0)
def test_circuit_to_choi_and_operation_to_choi():
    """Tests the Choi matrix of a depolarizing channel is recovered."""
    base_noise = 0.01
    max_ent_state = np.array([1, 0, 0, 1]) / np.sqrt(2)
    identity_part = np.outer(max_ent_state, max_ent_state)
    mixed_part = np.eye(4) / 4.0
    epsilon = base_noise * 4.0 / 3.0
    choi = (1.0 - epsilon) * identity_part + epsilon * mixed_part
    choi_twice = sum([(1.0 - epsilon) ** 2 * identity_part, (2 * epsilon - epsilon ** 2) * mixed_part])
    q = LineQubit(0)
    noisy_operation = depolarize(base_noise).on(q)
    noisy_sequence = [noisy_operation, noisy_operation]
    assert np.allclose(choi, _operation_to_choi(noisy_operation))
    noisy_circuit = Circuit(noisy_operation)
    noisy_circuit_twice = Circuit(noisy_sequence)
    assert np.allclose(choi, _circuit_to_choi(noisy_circuit))
    assert np.allclose(choi_twice, _circuit_to_choi(noisy_circuit_twice))