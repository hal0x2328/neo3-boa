import ast

from boa3.analyser.typeanalyser import TypeAnalyser
from boa3.model.type.listtype import ListType
from boa3.model.type.tupletype import TupleType
from boa3.model.type.type import Type
from boa3_test.tests.boa_test import BoaTest


class TestTypes(BoaTest):

    def test_small_integer_constant(self):
        input = 42
        node = ast.parse(str(input)).body[0].value
        expected_output = Type.int

        typeanalyser = TypeAnalyser(node, {})
        output = typeanalyser.get_type(input)

        self.assertEqual(expected_output, output)

    def test_negative_integer_constant(self):
        input = -10
        node = ast.parse(str(input)).body[0].value
        expected_output = Type.int

        typeanalyser = TypeAnalyser(node, {})
        output = typeanalyser.get_type(input)

        self.assertEqual(expected_output, output)

    def test_boolean_constant(self):
        input = True
        node = ast.parse(str(input)).body[0].value
        expected_output = Type.bool

        typeanalyser = TypeAnalyser(node, {})
        output = typeanalyser.get_type(input)

        self.assertEqual(expected_output, output)

    def test_string_constant(self):
        input = 'unit_test'
        node = ast.parse(str(input)).body[0].value
        expected_output = Type.str

        typeanalyser = TypeAnalyser(node, {})
        output = typeanalyser.get_type(input)

        self.assertEqual(expected_output, output)

    def test_integer_tuple_constant(self):
        input = (1, 2, 3)
        node = ast.parse(str(input)).body[0].value
        expected_output = TupleType(Type.int)

        typeanalyser = TypeAnalyser(node, {})
        output = typeanalyser.get_type(input)

        self.assertEqual(expected_output, output)

    def test_boolean_tuple_constant(self):
        input = (True, False)
        node = ast.parse(str(input)).body[0].value
        expected_output = TupleType(Type.bool)

        typeanalyser = TypeAnalyser(node, {})
        output = typeanalyser.get_type(input)

        self.assertEqual(expected_output, output)

    def test_string_tuple_constant(self):
        input = (1, 2, 3)
        node = ast.parse(str(input)).body[0].value
        expected_output = TupleType(Type.int)

        typeanalyser = TypeAnalyser(node, {})
        output = typeanalyser.get_type(input)

        self.assertEqual(expected_output, output)

    def test_any_tuple_constant(self):
        input = (1, '2', False)
        node = ast.parse(str(input)).body[0].value
        expected_output = TupleType(Type.none)  # TODO: change to any when implemented

        typeanalyser = TypeAnalyser(node, {})
        output = typeanalyser.get_type(input)

        self.assertEqual(expected_output, output)

    def test_integer_list_constant(self):
        input = [1, 2, 3]
        node = ast.parse(str(input)).body[0].value
        expected_output = ListType(Type.int)

        typeanalyser = TypeAnalyser(node, {})
        output = typeanalyser.get_type(input)

        self.assertEqual(expected_output, output)

    def test_boolean_list_constant(self):
        input = [True, False]
        node = ast.parse(str(input)).body[0].value
        expected_output = ListType(Type.bool)

        typeanalyser = TypeAnalyser(node, {})
        output = typeanalyser.get_type(input)

        self.assertEqual(expected_output, output)

    def test_string_list_constant(self):
        input = [1, 2, 3]
        node = ast.parse(str(input)).body[0].value
        expected_output = ListType(Type.int)

        typeanalyser = TypeAnalyser(node, {})
        output = typeanalyser.get_type(input)

        self.assertEqual(expected_output, output)

    def test_any_list_constant(self):
        input = [1, '2', False]
        node = ast.parse(str(input)).body[0].value
        expected_output = ListType(Type.none)  # TODO: change to any when implemented

        typeanalyser = TypeAnalyser(node, {})
        output = typeanalyser.get_type(input)

        self.assertEqual(expected_output, output)

    def test_sequence_any_is_type_of_str(self):
        sequence_type = Type.sequence
        str_type = Type.str
        self.assertTrue(sequence_type.is_type_of(str_type))

    def test_sequence_any_is_type_of_tuple_any(self):
        sequence_type = Type.sequence
        tuple_type = Type.tuple
        self.assertTrue(sequence_type.is_type_of(tuple_type))

    def test_sequence_int_is_type_of_tuple_any(self):
        sequence_type = Type.sequence.build_sequence(Type.int)
        tuple_type = Type.tuple
        self.assertFalse(sequence_type.is_type_of(tuple_type))

    def test_sequence_any_is_type_of_tuple_int(self):
        sequence_type = Type.sequence
        tuple_type = Type.tuple.build_sequence(Type.int)
        self.assertTrue(sequence_type.is_type_of(tuple_type))

    def test_sequence_any_is_type_of_list_any(self):
        sequence_type = Type.sequence
        list_type = Type.list
        self.assertTrue(sequence_type.is_type_of(list_type))

    def test_sequence_int_is_type_of_list_any(self):
        sequence_type = Type.sequence.build_sequence(Type.int)
        list_type = Type.list
        self.assertFalse(sequence_type.is_type_of(list_type))

    def test_sequence_any_is_type_of_list_int(self):
        sequence_type = Type.sequence
        list_type = Type.list.build_sequence(Type.int)
        self.assertTrue(sequence_type.is_type_of(list_type))

    def test_tuple_any_is_type_of_sequence(self):
        sequence_type = Type.sequence
        tuple_type = Type.tuple
        self.assertFalse(tuple_type.is_type_of(sequence_type))

    def test_tuple_any_is_type_of_tuple_int(self):
        tuple_type = Type.tuple
        tuple_int_type = Type.tuple.build_sequence(Type.int)
        self.assertTrue(tuple_type.is_type_of(tuple_int_type))

    def test_tuple_int_is_type_of_tuple_any(self):
        tuple_type = Type.tuple.build_sequence(Type.int)
        tuple_any_type = Type.tuple
        self.assertFalse(tuple_type.is_type_of(tuple_any_type))

    def test_list_any_is_type_of_sequence(self):
        list_type = Type.list
        sequence_type = Type.sequence
        self.assertFalse(list_type.is_type_of(sequence_type))

    def test_list_any_is_type_of_list_int(self):
        list_type = Type.list
        list_int_type = Type.list.build_sequence(Type.int)
        self.assertTrue(list_type.is_type_of(list_int_type))

    def test_list_int_is_type_of_list_any(self):
        list_type = Type.list.build_sequence(Type.int)
        list_any_type = Type.list
        self.assertFalse(list_type.is_type_of(list_any_type))

    def test_str_any_is_type_of_sequence(self):
        sequence_type = Type.sequence
        str_type = Type.str
        self.assertFalse(str_type.is_type_of(sequence_type))

    def test_str_any_is_type_of_sequence_str(self):
        sequence_type = Type.sequence.build_sequence(Type.str)
        str_type = Type.str
        self.assertFalse(str_type.is_type_of(sequence_type))
