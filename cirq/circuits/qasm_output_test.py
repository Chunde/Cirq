# Copyright 2018 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import pytest

import cirq
from cirq.circuits.qasm_output import QasmUGate, QasmTwoQubitGate


def _make_qubits(n):
    return [cirq.NamedQubit('q{}'.format(i)) for i in range(n)]


def test_u_gate_repr():
    gate = QasmUGate(0.1, 0.2, 0.3)
    assert repr(gate) == 'cirq.QasmUGate(0.1, 0.2, 0.3)'


def test_qasm_two_qubit_gate_repr():
    gate = QasmTwoQubitGate(QasmUGate(0.1, 0.2, 0.3),
                            QasmUGate(0.4, 0.5, 0.6),
                            0.7, 0.8, 0.9,
                            QasmUGate(1.0, 1.1, 1.2),
                            QasmUGate(1.3, 1.4, 1.5))
    assert repr(gate) == ('cirq.QasmTwoQubitGate('
                          'cirq.QasmUGate(0.1, 0.2, 0.3), '
                          'cirq.QasmUGate(0.4, 0.5, 0.6), '
                          '0.7, 0.8, 0.9, '
                          'cirq.QasmUGate(1.0, 1.1, 1.2), '
                          'cirq.QasmUGate(1.3, 1.4, 1.5))')


def test_empty_circuit():
    q0, = _make_qubits(1)
    output = cirq.QasmOutput((), (q0,))
    assert (str(output) ==
            """OPENQASM 2.0;
include "qelib1.inc";


// Qubits: [q0]
qreg q[1];
""")


def test_header():
    q0, = _make_qubits(1)
    output = cirq.QasmOutput((), (q0,), header="""My test circuit
Device: Bristlecone""")
    assert (str(output) ==
            """// My test circuit
// Device: Bristlecone

OPENQASM 2.0;
include "qelib1.inc";


// Qubits: [q0]
qreg q[1];
""")

    output = cirq.QasmOutput((), (q0,), header="""
My test circuit
Device: Bristlecone
""")
    assert (str(output) ==
            """//
// My test circuit
// Device: Bristlecone
//

OPENQASM 2.0;
include "qelib1.inc";


// Qubits: [q0]
qreg q[1];
""")


def test_single_gate_no_parameter():
    q0, = _make_qubits(1)
    output = cirq.QasmOutput((cirq.X(q0),), (q0,))
    assert (str(output) ==
            """OPENQASM 2.0;
include "qelib1.inc";


// Qubits: [q0]
qreg q[1];


x q[0];
""")


def test_single_gate_with_parameter():
    q0, = _make_qubits(1)
    output = cirq.QasmOutput((cirq.X(q0) ** 0.25,), (q0,))
    assert (str(output) ==
            """OPENQASM 2.0;
include "qelib1.inc";


// Qubits: [q0]
qreg q[1];


rx(pi*0.25) q[0];
""")


def test_h_gate_with_parameter():
    q0, = _make_qubits(1)
    output = cirq.QasmOutput((cirq.H(q0) ** 0.25,), (q0,))
    assert (str(output) ==
            """OPENQASM 2.0;
include "qelib1.inc";


// Qubits: [q0]
qreg q[1];


ry(pi*0.25) q[0];
rx(pi*0.25) q[0];
ry(pi*-0.25) q[0];
""")


def test_precision():
    q0, = _make_qubits(1)
    output = cirq.QasmOutput((cirq.X(q0) ** 0.1234567,), (q0,), precision=3)
    assert (str(output) ==
            """OPENQASM 2.0;
include "qelib1.inc";


// Qubits: [q0]
qreg q[1];


rx(pi*0.123) q[0];
""")


def test_version():
    q0, = _make_qubits(1)
    with pytest.raises(ValueError):
        output = cirq.QasmOutput((), (q0,), version='3.0')
        _ = str(output)


def test_save_to_file():
    q0, = _make_qubits(1)
    output = cirq.QasmOutput((), (q0,))
    with cirq.testing.TempFilePath() as file_path:
        output.save(file_path)
        with open(file_path, 'r') as f:
            file_content = f.read()
    assert (file_content ==
            """OPENQASM 2.0;
include "qelib1.inc";


// Qubits: [q0]
qreg q[1];
""")


def test_unsupported_operation():
    q0, = _make_qubits(1)

    class UnsupportedOperation(cirq.Operation):
        qubits = (q0,)
        with_qubits = NotImplemented

    output = cirq.QasmOutput((UnsupportedOperation(),), (q0,))
    with pytest.raises(ValueError):
        _ = str(output)


def _all_operations(q0, q1, q2, q3, q4, include_measurments=True):
    class DummyOperation(cirq.Operation, cirq.QasmConvertibleOperation,
                         cirq.CompositeOperation):
        qubits = (q0,)
        with_qubits = NotImplemented

        def known_qasm_output(self, args):
            return '// Dummy operation\n'

        def default_decompose(self):
            # Only used by test_output_unitary_same_as_qiskit
            return ()  # coverage: ignore

    class DummyCompositeOperation(cirq.Operation, cirq.CompositeOperation):
        qubits = (q0,)
        with_qubits = NotImplemented

        def default_decompose(self):
            return cirq.X(self.qubits[0])

        def __repr__(self):
            return 'DummyCompositeOperation()'

    return (
        cirq.Z(q0),
        cirq.Z(q0) ** .625,
        cirq.Y(q0),
        cirq.Y(q0) ** .375,
        cirq.X(q0),
        cirq.X(q0) ** .875,
        cirq.H(q1),
        cirq.CZ(q0, q1),
        cirq.CZ(q0, q1) ** 0.25,  # Requires 2-qubit decomposition
        cirq.CNOT(q0, q1),
        cirq.CNOT(q0, q1) ** 0.5,  # Requires 2-qubit decomposition
        cirq.SWAP(q0, q1),
        cirq.SWAP(q0, q1) ** 0.75,  # Requires 2-qubit decomposition

        cirq.CCZ(q0, q1, q2),
        cirq.CCX(q0, q1, q2),
        cirq.CCZ(q0, q1, q2)**0.5,
        cirq.CCX(q0, q1, q2)**0.5,
        cirq.CSWAP(q0, q1, q2),

        cirq.ISWAP(q2, q0),  # Requires 2-qubit decomposition

        cirq.google.ExpZGate()(q3),
        cirq.google.ExpZGate(half_turns=0.75)(q3),
        cirq.google.ExpWGate(axis_half_turns=0.125, half_turns=0.25)(q1),
        cirq.google.Exp11Gate()(q0, q1),
        # Requires 2-qubit decomposition
        cirq.google.Exp11Gate(half_turns=1.25)(q0, q1),

        (
            cirq.MeasurementGate('xX')(q0),
            cirq.MeasurementGate('x_a')(q2),
            cirq.MeasurementGate('x?')(q1),
            cirq.MeasurementGate('X')(q3),
            cirq.MeasurementGate('_x')(q4),
            cirq.MeasurementGate('x_a')(q2),
            cirq.MeasurementGate('multi', (False, True))(q1, q2, q3),
        ) if include_measurments else (),

        DummyOperation(),
        DummyCompositeOperation(),
    )


def test_output_parsable_by_qiskit():
    qubits = tuple(_make_qubits(5))
    operations = _all_operations(*qubits)
    output = cirq.QasmOutput(operations, qubits,
                             header='Generated from Cirq',
                             precision=10)
    text = str(output)

    # coverage: ignore
    try:
        # We don't want to require qiskit as a dependency but
        # if Qiskit is installed, test QASM output against it.
        import qiskit  # type: ignore
    except ImportError:
        return

    assert qiskit.qasm.Qasm(data=text).parse().qasm() is not None


def test_output_unitary_same_as_qiskit():
    qubits = tuple(_make_qubits(5))
    operations = _all_operations(*qubits, include_measurments=False)
    output = cirq.QasmOutput(operations, qubits,
                             header='Generated from Cirq',
                             precision=10)
    text = str(output)

    # coverage: ignore
    try:
        # We don't want to require qiskit as a dependency but
        # if Qiskit is installed, test QASM output against it.
        import qiskit  # type: ignore
    except ImportError:
        return

    circuit = cirq.Circuit.from_ops(operations)
    cirq_unitary = circuit.to_unitary_matrix(qubit_order=qubits[::-1])

    p = qiskit.QuantumProgram()
    p.load_qasm_text(text)
    result = p.execute(backend='local_unitary_simulator')
    qiskit_unitary = result.get_unitary()

    cirq.testing.assert_allclose_up_to_global_phase(
        cirq_unitary, qiskit_unitary, rtol=1e-8, atol=1e-8)


def test_output_format():
    def filter_unpredictable_numbers(text):
        return re.sub(r'u3\(.+\)', r'u3(<not-repeatable>)', text)

    qubits = tuple(_make_qubits(5))
    operations = _all_operations(*qubits)
    output = cirq.QasmOutput(operations, qubits,
                             header='Generated from Cirq',
                             precision=5)
    assert (filter_unpredictable_numbers(str(output)) ==
            filter_unpredictable_numbers(
        """// Generated from Cirq

OPENQASM 2.0;
include "qelib1.inc";


// Qubits: [q0, q1, q2, q3, q4]
qreg q[5];
creg m_xX[1];
creg m_x_a[1];
creg m0[1];  // Measurement: x?
creg m_X[1];
creg m__x[1];
creg m_multi[3];


z q[0];
rz(pi*0.625) q[0];
y q[0];
ry(pi*0.375) q[0];
x q[0];
rx(pi*0.875) q[0];
h q[1];
cz q[0],q[1];

// Gate: CZ**0.25
u3(pi*0.5,pi*1.0,pi*0.75) q[0];
u3(pi*0.5,pi*1.0,pi*0.25) q[1];
rx(pi*0.5) q[0];
cx q[0],q[1];
rx(pi*0.375) q[0];
ry(pi*0.5) q[1];
cx q[1],q[0];
rx(pi*-0.5) q[1];
rz(pi*0.5) q[1];
cx q[0],q[1];
u3(pi*0.5,pi*0.375,0) q[0];
u3(pi*0.5,pi*0.875,0) q[1];

cx q[0],q[1];

// Gate: CNOT**0.5
ry(pi*-0.5) q[1];
u3(pi*0.5,0,pi*0.25) q[0];
u3(pi*0.5,0,pi*0.75) q[1];
rx(pi*0.5) q[0];
cx q[0],q[1];
rx(pi*0.25) q[0];
ry(pi*0.5) q[1];
cx q[1],q[0];
rx(pi*-0.5) q[1];
rz(pi*0.5) q[1];
cx q[0],q[1];
u3(pi*0.5,pi*1.0,pi*1.0) q[0];
u3(pi*0.5,pi*0.5,pi*1.0) q[1];
ry(pi*0.5) q[1];

swap q[0],q[1];

// Gate: SWAP**0.75
cx q[0],q[1];
ry(pi*-0.5) q[0];
u3(pi*0.5,0,pi*0.45919) q[1];
u3(pi*0.5,0,pi*1.95919) q[0];
rx(pi*0.5) q[1];
cx q[1],q[0];
rx(pi*0.125) q[1];
ry(pi*0.5) q[0];
cx q[0],q[1];
rx(pi*-0.5) q[0];
rz(pi*0.5) q[0];
cx q[1],q[0];
u3(pi*0.5,pi*0.91581,pi*1.0) q[1];
u3(pi*0.5,pi*1.41581,pi*1.0) q[0];
ry(pi*0.5) q[0];
cx q[0],q[1];

h q[2];
ccx q[0],q[1],q[2];
h q[2];
ccx q[0],q[1],q[2];

// Gate: CCZ**0.5
rz(pi*0.125) q[0];
rz(pi*0.125) q[1];
rz(pi*0.125) q[2];
cx q[0],q[1];
cx q[1],q[2];
rz(pi*-0.125) q[1];
rz(pi*0.125) q[2];
cx q[0],q[1];
cx q[1],q[2];
rz(pi*-0.125) q[2];
cx q[0],q[1];
cx q[1],q[2];
rz(pi*-0.125) q[2];
cx q[0],q[1];
cx q[1],q[2];

// Gate: TOFFOLI**0.5
h q[2];
rz(pi*0.125) q[0];
rz(pi*0.125) q[1];
rz(pi*0.125) q[2];
cx q[0],q[1];
cx q[1],q[2];
rz(pi*-0.125) q[1];
rz(pi*0.125) q[2];
cx q[0],q[1];
cx q[1],q[2];
rz(pi*-0.125) q[2];
cx q[0],q[1];
cx q[1],q[2];
rz(pi*-0.125) q[2];
cx q[0],q[1];
cx q[1],q[2];
h q[2];

cswap q[0],q[1],q[2];

// Gate: ISWAP
cx q[2],q[0];
h q[2];
cx q[0],q[2];
rz(pi*0.5) q[2];
cx q[0],q[2];
rz(pi*-0.5) q[2];
h q[2];
cx q[2],q[0];

z q[3];
rz(pi*0.75) q[3];

// Gate: W(0.125)^0.25
u3(pi*0.25,pi*1.625,pi*0.375) q[1];

cz q[0],q[1];

// Gate: Exp11Gate(half_turns=-0.75)
u3(pi*0.5,0,pi*1.54081) q[0];
u3(pi*0.5,pi*1.0,pi*0.04081) q[1];
rx(pi*0.5) q[0];
cx q[0],q[1];
rx(pi*0.125) q[0];
ry(pi*0.5) q[1];
cx q[1],q[0];
rx(pi*-0.5) q[1];
rz(pi*0.5) q[1];
cx q[0],q[1];
u3(pi*0.5,pi*1.08419,pi*1.0) q[0];
u3(pi*0.5,pi*0.58419,0) q[1];

measure q[0] -> m_xX[0];
measure q[2] -> m_x_a[0];
measure q[1] -> m0[0];
measure q[3] -> m_X[0];
measure q[4] -> m__x[0];
measure q[2] -> m_x_a[0];
measure q[1] -> m_multi[0];
x q[2];  // Invert the following measurement
measure q[2] -> m_multi[1];
measure q[3] -> m_multi[2];
// Dummy operation

// Operation: DummyCompositeOperation()
x q[0];
"""))
