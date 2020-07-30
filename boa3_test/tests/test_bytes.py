from boa3.boa3 import Boa3
from boa3.exception.CompilerError import MismatchedTypes, NotSupportedOperation, UnresolvedOperation
from boa3.model.type.type import Type
from boa3.neo.vm.opcode.Opcode import Opcode
from boa3.neo.vm.type.Integer import Integer
from boa3_test.tests.boa_test import BoaTest


class TestBytes(BoaTest):

    def test_bytes_literal_value(self):
        data = b'\x01\x02\x03'
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x01'
            + b'\x00'
            + Opcode.PUSHDATA1  # a = b'\x01\x02\x03'
            + Integer(len(data)).to_byte_array(min_length=1)
            + data
            + Opcode.CONVERT
            + Type.bytes.stack_item
            + Opcode.STLOC0
            + Opcode.PUSHNULL
            + Opcode.RET        # return
        )

        path = '%s/boa3_test/example/bytes_test/BytesLiteral.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_bytes_get_value(self):
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x00'
            + b'\x01'
            + Opcode.LDARG0     # arg[0]
            + Opcode.PUSH0
                + Opcode.DUP
                + Opcode.SIGN
                + Opcode.PUSHM1
                + Opcode.JMPNE
                + Integer(5).to_byte_array(min_length=1, signed=True)
                + Opcode.OVER
                + Opcode.SIZE
                + Opcode.ADD
            + Opcode.PICKITEM
            + Opcode.RET        # return
        )

        path = '%s/boa3_test/example/bytes_test/BytesGetValue.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_bytes_get_value_negative_index(self):
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x00'
            + b'\x01'
            + Opcode.LDARG0     # arg[0]
            + Opcode.PUSH1
            + Opcode.NEGATE
                + Opcode.DUP
                + Opcode.SIGN
                + Opcode.PUSHM1
                + Opcode.JMPNE
                + Integer(5).to_byte_array(min_length=1, signed=True)
                + Opcode.OVER
                + Opcode.SIZE
                + Opcode.ADD
            + Opcode.PICKITEM
            + Opcode.RET        # return
        )

        path = '%s/boa3_test/example/bytes_test/BytesGetValueNegativeIndex.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_bytes_set_value(self):
        path = '%s/boa3_test/example/bytes_test/BytesSetValue.py' % self.dirname
        self.assertCompilerLogs(UnresolvedOperation, path)

    def test_bytes_clear(self):
        path = '%s/boa3_test/example/bytes_test/BytesClear.py' % self.dirname
        self.assertCompilerLogs(MismatchedTypes, path)

    def test_bytes_reverse(self):
        path = '%s/boa3_test/example/bytes_test/BytesReverse.py' % self.dirname
        self.assertCompilerLogs(MismatchedTypes, path)

    def test_bytes_from_byte_array(self):
        data = b'\x01\x02\x03'
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x02'
            + b'\x00'
            + Opcode.PUSHDATA1  # a = bytearray(b'\x01\x02\x03')
            + Integer(len(data)).to_byte_array(min_length=1)
            + data
            + Opcode.CONVERT
            + Type.bytes.stack_item
            + Opcode.STLOC0
            + Opcode.LDLOC0     # b = a
            + Opcode.STLOC1
            + Opcode.PUSHNULL
            + Opcode.RET        # return
        )

        path = '%s/boa3_test/example/bytes_test/BytesFromBytearray.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_byte_array_get_value(self):
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x00'
            + b'\x01'
            + Opcode.LDARG0     # arg[0]
            + Opcode.PUSH0
                + Opcode.DUP
                + Opcode.SIGN
                + Opcode.PUSHM1
                + Opcode.JMPNE
                + Integer(5).to_byte_array(min_length=1, signed=True)
                + Opcode.OVER
                + Opcode.SIZE
                + Opcode.ADD
            + Opcode.PICKITEM
            + Opcode.RET        # return
        )

        path = '%s/boa3_test/example/bytes_test/BytearrayGetValue.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_byte_array_get_value_negative_index(self):
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x00'
            + b'\x01'
            + Opcode.LDARG0     # arg[0]
            + Opcode.PUSH1
            + Opcode.NEGATE
                + Opcode.DUP
                + Opcode.SIGN
                + Opcode.PUSHM1
                + Opcode.JMPNE
                + Integer(5).to_byte_array(min_length=1, signed=True)
                + Opcode.OVER
                + Opcode.SIZE
                + Opcode.ADD
            + Opcode.PICKITEM
            + Opcode.RET        # return
        )

        path = '%s/boa3_test/example/bytes_test/BytearrayGetValueNegativeIndex.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_byte_array_set_value(self):
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x00'
            + b'\x01'
            + Opcode.LDARG0     # arg[0] = 0x01
            + Opcode.PUSH0
                + Opcode.DUP
                + Opcode.SIGN
                + Opcode.PUSHM1
                + Opcode.JMPNE
                + Integer(5).to_byte_array(min_length=1, signed=True)
                + Opcode.OVER
                + Opcode.SIZE
                + Opcode.ADD
            + Opcode.PUSH1
            + Opcode.SETITEM
            + Opcode.LDARG0
            + Opcode.RET        # return
        )

        path = '%s/boa3_test/example/bytes_test/BytearraySetValue.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_byte_array_set_value_negative_index(self):
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x00'
            + b'\x01'
            + Opcode.LDARG0     # arg[-1] = 0x01
            + Opcode.PUSH1
            + Opcode.NEGATE
                + Opcode.DUP
                + Opcode.SIGN
                + Opcode.PUSHM1
                + Opcode.JMPNE
                + Integer(5).to_byte_array(min_length=1, signed=True)
                + Opcode.OVER
                + Opcode.SIZE
                + Opcode.ADD
            + Opcode.PUSH1
            + Opcode.SETITEM
            + Opcode.LDARG0
            + Opcode.RET        # return
        )

        path = '%s/boa3_test/example/bytes_test/BytearraySetValueNegativeIndex.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_byte_array_literal_value(self):
        path = '%s/boa3_test/example/bytes_test/BytearrayLiteral.py' % self.dirname
        self.assertCompilerLogs(MismatchedTypes, path)

    def test_byte_array_from_literal_bytes(self):
        data = b'\x01\x02\x03'
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x01'
            + b'\x00'
            + Opcode.PUSHDATA1  # a = bytearray(b'\x01\x02\x03')
            + Integer(len(data)).to_byte_array(min_length=1)
            + data
            + Opcode.CONVERT
            + Type.bytes.stack_item
            + Opcode.STLOC0
            + Opcode.PUSHNULL
            + Opcode.RET        # return
        )

        path = '%s/boa3_test/example/bytes_test/BytearrayFromLiteralBytes.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_byte_array_from_variable_bytes(self):
        data = b'\x01\x02\x03'
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x02'
            + b'\x00'
            + Opcode.PUSHDATA1  # a = b'\x01\x02\x03'
            + Integer(len(data)).to_byte_array(min_length=1)
            + data
            + Opcode.CONVERT
            + Type.bytes.stack_item
            + Opcode.STLOC0
            + Opcode.LDLOC0     # b = bytearray(a)
            + Opcode.STLOC1
            + Opcode.PUSHNULL
            + Opcode.RET        # return
        )

        path = '%s/boa3_test/example/bytes_test/BytearrayFromVariableBytes.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_byte_array_string(self):
        path = '%s/boa3_test/example/bytes_test/BytearrayFromString.py' % self.dirname
        self.assertCompilerLogs(NotSupportedOperation, path)

    def test_byte_array_append(self):
        data = b'\x01\x02\x03'
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x01'
            + b'\x00'
            + Opcode.PUSHDATA1  # a = bytearray(b'\x01\x02\x03')
            + Integer(len(data)).to_byte_array(min_length=1)
            + data
            + Opcode.CONVERT
            + Type.bytes.stack_item
            + Opcode.STLOC0
            + Opcode.LDLOC0     # a.append(4)
            + Opcode.PUSH4
                + Opcode.OVER
                + Opcode.ISTYPE
                + Type.bytearray.stack_item
                + Opcode.JMPIFNOT
                + Integer(8).to_byte_array(min_length=1)
                + Opcode.CAT
                + Opcode.JMP
                + Integer(5).to_byte_array(min_length=1)
                + Opcode.APPEND
                + Opcode.JMP
                + Integer(3).to_byte_array(min_length=1)
                + Opcode.STLOC0
            + Opcode.LDLOC0
            + Opcode.RET        # return a
        )

        path = '%s/boa3_test/example/bytes_test/BytearrayAppend.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_byte_array_append_with_builtin(self):
        data = b'\x01\x02\x03'
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x01'
            + b'\x00'
            + Opcode.PUSHDATA1  # a = bytearray(b'\x01\x02\x03')
            + Integer(len(data)).to_byte_array(min_length=1)
            + data
            + Opcode.CONVERT
            + Type.bytes.stack_item
            + Opcode.STLOC0
            + Opcode.LDLOC0     # bytearray.append(a, 4)
            + Opcode.PUSH4
                + Opcode.OVER
                + Opcode.ISTYPE
                + Type.bytearray.stack_item
                + Opcode.JMPIFNOT
                + Integer(8).to_byte_array(min_length=1)
                + Opcode.CAT
                + Opcode.JMP
                + Integer(5).to_byte_array(min_length=1)
                + Opcode.APPEND
                + Opcode.JMP
                + Integer(3).to_byte_array(min_length=1)
                + Opcode.STLOC0
            + Opcode.LDLOC0
            + Opcode.RET        # return a
        )

        path = '%s/boa3_test/example/bytes_test/BytearrayAppendWithBuiltin.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_byte_array_append_mutable_sequence_with_builtin(self):
        data = b'\x01\x02\x03'
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x01'
            + b'\x00'
            + Opcode.PUSHDATA1  # a = bytearray(b'\x01\x02\x03')
            + Integer(len(data)).to_byte_array(min_length=1)
            + data
            + Opcode.CONVERT
            + Type.bytes.stack_item
            + Opcode.STLOC0
            + Opcode.LDLOC0     # MutableSequence.append(a, 4)
            + Opcode.PUSH4
                + Opcode.OVER
                + Opcode.ISTYPE
                + Type.bytearray.stack_item
                + Opcode.JMPIFNOT
                + Integer(8).to_byte_array(min_length=1)
                + Opcode.CAT
                + Opcode.JMP
                + Integer(5).to_byte_array(min_length=1)
                + Opcode.APPEND
                + Opcode.JMP
                + Integer(3).to_byte_array(min_length=1)
                + Opcode.STLOC0
            + Opcode.LDLOC0
            + Opcode.RET        # return a
        )

        path = '%s/boa3_test/example/bytes_test/BytearrayAppendWithMutableSequence.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_byte_array_clear(self):
        path = '%s/boa3_test/example/bytes_test/BytearrayClear.py' % self.dirname
        self.assertCompilerLogs(NotSupportedOperation, path)

    def test_byte_array_reverse(self):
        data = b'\x01\x02\x03'
        expected_output = (
            Opcode.INITSLOT     # function signature
            + b'\x01'
            + b'\x00'
            + Opcode.PUSHDATA1  # a = bytearray(b'\x01\x02\x03')
            + Integer(len(data)).to_byte_array(min_length=1)
            + data
            + Opcode.CONVERT
            + Type.bytes.stack_item
            + Opcode.STLOC0
            + Opcode.LDLOC0     # a.reverse()
            + Opcode.REVERSEITEMS
            + Opcode.LDLOC0
            + Opcode.RET        # return a
        )

        path = '%s/boa3_test/example/bytes_test/BytearrayReverse.py' % self.dirname
        output = Boa3.compile(path)
        self.assertEqual(expected_output, output)

    def test_byte_array_extend(self):
        path = '%s/boa3_test/example/bytes_test/BytearrayExtend.py' % self.dirname
        self.assertCompilerLogs(NotSupportedOperation, path)
