import sys
from typing import Dict, List, Any, Optional, Tuple

from boa3.analyser.analyser import Analyser
from boa3.constants import ONE_BYTE_MAX_VALUE, TWO_BYTES_MAX_VALUE
from boa3.model.builtin.builtin import Builtin
from boa3.model.builtin.method.builtinmethod import IBuiltinMethod
from boa3.model.method import Method
from boa3.model.operation.operation import IOperation
from boa3.model.symbol import ISymbol
from boa3.model.type.type import Type
from boa3.model.variable import Variable
from boa3.neo.vm.VMCode import VMCode
from boa3.neo.vm.opcode.Opcode import Opcode
from boa3.neo.vm.opcode.OpcodeInfo import OpcodeInfo
from boa3.neo.vm.opcode.OpcodeInformation import OpcodeInformation
from boa3.neo.vm.type.Integer import Integer
from boa3.neo.vm.type.StackItemType import StackItemType


class CodeGenerator:
    """
    This class is responsible for generating the Neo VM bytecode

    :ivar symbol_table: a dictionary that maps the global symbols.
    """

    @staticmethod
    def generate_code(analyser: Analyser) -> bytes:
        """
        Generates the Neo VM bytecode using of the analysed Python code

        :param analyser: semantic analyser it tge Python code
        :return: the Neo VM bytecode
        """
        from boa3.compiler.codegeneratorvisitor import VisitorCodeGenerator

        generator = CodeGenerator(analyser.symbol_table)
        visitor = VisitorCodeGenerator(generator)
        visitor.visit(analyser.ast_tree)
        return generator.bytecode

    def __init__(self, symbol_table: Dict[str, ISymbol]):
        self.symbol_table: Dict[str, ISymbol] = symbol_table
        self.__vm_codes_without_order: List[VMCode] = []

        self.__current_method: Method = None
        self.__function_calls: List[Tuple[VMCode, Method]] = []  # calls of functions that haven't been converted yet
        self.__is_entry_point_converted: bool = False

    @property
    def bytecode(self) -> bytes:
        """
        Gets the bytecode of the translated code

        :return: the generated bytecode
        """
        bytecode = bytearray()
        for code in self.__vm_codes:
            bytecode += code.opcode
            if code.data is not None:
                bytecode += code.data
        return bytes(bytecode)

    @property
    def __vm_codes(self) -> List[VMCode]:
        """
        Gets an ordered list of the vm codes

        :return: a list of vm codes ordered by the code address
        """
        return sorted(self.__vm_codes_without_order, key=lambda code: code.start_address)

    @property
    def __vm_codes_map(self) -> Dict[int, VMCode]:
        """
        Gets a map of the vm codes

        :return: a dictionary that maps each code to its start address
        """
        code_dict = {}
        for code in self.__vm_codes:
            code_dict[code.start_address] = code
        return code_dict

    @property
    def last_code(self) -> Optional[VMCode]:
        """
        Gets the last code in the bytecode

        :return: the last code. If the bytecode is empty, returns None
        :rtype: VMCode or None
        """
        if len(self.__vm_codes) > 0:
            return self.__vm_codes[-1]
        else:
            return None

    @property
    def address(self) -> int:
        if self.last_code is not None:
            return self.last_code.end_address + 1
        else:
            return 0

    @property
    def __args(self) -> List[str]:
        """
        Gets a list with the arguments names of the current method

        :return: A list with the arguments names
        """
        if self.__current_method is not None:
            return list(self.__current_method.args.keys())
        else:
            return []

    @property
    def __locals(self) -> List[str]:
        """
        Gets a list with the variables names in the scope of the current method

        :return: A list with the variables names
        """
        if self.__current_method is not None:
            return list(self.__current_method.locals.keys())
        else:
            return []

    @property
    def __globals(self) -> List[str]:
        """
        Gets a list with the variables name in the global scope

        :return: A list with the variables names
        """
        # TODO: Global scope not implemented yet
        return []

    def get_symbol(self, identifier: str) -> ISymbol:
        """
        Gets a symbol in the symbol table by its id

        :param identifier: id of the symbol
        :return: the symbol if exists. Symbol None otherwise
        """
        if self.__current_method is not None and identifier in self.__current_method.symbols:
            return self.__current_method.symbols[identifier]
        elif identifier in self.symbol_table:
            return self.symbol_table[identifier]

        # the symbol may be a built in. If not, returns None
        symbol = Builtin.get_symbol(identifier)
        return symbol if symbol is not None else Type.none

    def convert_begin_method(self, method: Method):
        """
        Converts the signature of the method

        :param method: method that is being converted
        """
        num_args: int = len(method.args)
        num_vars: int = len(method.locals)

        init_data = bytearray([num_vars, num_args])
        self.__insert1(OpcodeInfo.INITSLOT, init_data)
        method.init_bytecode = self.last_code
        self.__current_method = method

        # updates each call to this method with its address
        if self.__is_entry_point_converted:
            for address, method in [call for call in self.__function_calls if call[1] is method]:
                self.__update_call(address, method)

    def convert_end_method(self):
        """
        Converts the end of the method
        """
        self.__insert1(OpcodeInfo.RET)

        if self.__current_method.is_main_method:
            self.__move_entry_point_to_beginning()
        self.__current_method = None

    def __move_entry_point_to_beginning(self):
        """
        Move the vm codes of the smart contract entry point to the beginning of the bytecode
        """
        method = self.__current_method
        if method is not None and method.is_main_method:
            main_first_code = self.__vm_codes_map[method.bytecode_address]
            main_last_code = self.last_code
            first_code = self.__vm_codes[0]

            if first_code.start_address != main_first_code.start_address:
                main_first_code._last_code = None
                first_code._last_code = main_last_code

                for vmcode, function in self.__function_calls:
                    if function.bytecode_address is not None:
                        self.__update_call(vmcode, function)

            self.__is_entry_point_converted = True

    def convert_begin_while(self) -> int:
        """
        Converts the beginning of the while statement

        :return: the address of the while first opcode
        """
        # it will be updated when the while ends
        self.__insert_jump(OpcodeInfo.JMP, 0)
        return self.last_code.start_address

    def convert_end_while(self, start_address: int, test_address: int):
        """
        Converts the end of the while statement

        :param start_address: the address of the while first opcode
        :param test_address: the address of the while test fist opcode
        """
        # updates the begin jmp with the target address
        begin_jmp_to: int = test_address - start_address
        self.__update_jump(start_address, begin_jmp_to)

        # inserts end jmp
        while_begin: VMCode = self.__vm_codes_map[start_address]
        while_body: int = while_begin.end_address + 1
        end_jmp_to: int = while_body - self.address
        self.__insert_jump(OpcodeInfo.JMPIF, end_jmp_to)

    def convert_begin_if(self) -> int:
        """
        Converts the beginning of the if statement

        :return: the address of the if first opcode
        """
        # it will be updated when the if ends
        self.__insert_jump(OpcodeInfo.JMPIFNOT, 0)
        return self.last_code.start_address

    def convert_begin_else(self, start_address: int) -> int:
        """
        Converts the beginning of the if else statement

        :param start_address: the address of the if first opcode
        :return: the address of the if else first opcode
        """
        # it will be updated when the if ends
        self.__insert_jump(OpcodeInfo.JMP, 0)

        # updates the begin jmp with the target address
        begin_jmp_to: int = self.address - start_address
        self.__update_jump(start_address, begin_jmp_to)

        return self.last_code.start_address

    def convert_end_if(self, start_address: int):
        """
        Converts the end of the if statement

        :param start_address: the address of the if first opcode
        """
        # updates the begin jmp with the target address
        jmp_to: int = self.address - start_address
        self.__update_jump(start_address, jmp_to)

    def convert_literal(self, value: Any):
        """
        Converts a literal value

        :param value: the value to be converted
        """
        if isinstance(value, bool):
            self.convert_bool_literal(value)
        elif isinstance(value, int):
            self.convert_integer_literal(value)
        elif isinstance(value, str):
            self.convert_string_literal(value)
        else:
            # TODO: convert other python literals as they are implemented
            raise NotImplementedError

    def convert_integer_literal(self, value: int):
        """
        Converts an integer literal value

        :param value: the value to be converted
        """
        if -1 <= value <= 16:
            opcode = Opcode.get_literal_push(value)
            if opcode is not None:
                op_info: OpcodeInformation = OpcodeInfo.get_info(opcode)
                self.__insert1(op_info)
        else:
            array = Integer(value).to_byte_array()
            self.convert_byte_array(array)
            # cast the value to integer
            self.__insert1(OpcodeInfo.CONVERT, StackItemType.Integer)

    def convert_string_literal(self, value: str):
        """
        Converts an string literal value

        :param value: the value to be converted
        """
        array = bytes(value, sys.getdefaultencoding())
        self.convert_byte_array(array)

    def convert_bool_literal(self, value: bool):
        """
        Converts an boolean literal value

        :param value: the value to be converted
        """
        if value:
            self.__insert1(OpcodeInfo.PUSH1)
        else:
            self.__insert1(OpcodeInfo.PUSH0)

    def convert_byte_array(self, array: bytes):
        """
        Converts a byte value

        :param array: the value to be converted
        """
        data_len: int = len(array)
        if data_len <= ONE_BYTE_MAX_VALUE:
            op_info = OpcodeInfo.PUSHDATA1
        elif data_len <= TWO_BYTES_MAX_VALUE:
            op_info = OpcodeInfo.PUSHDATA2
        else:
            op_info = OpcodeInfo.PUSHDATA4

        data = Integer(data_len).to_byte_array(min_length=op_info.data_len) + array
        self.__insert1(op_info, data)

    def convert_new_empty_array(self, length: int):
        """
        Converts the creation of a new empty array

        :param length: the size of the new array
        """
        if length <= 0:
            self.__insert1(OpcodeInfo.NEWARRAY0)
        else:
            self.convert_literal(length)
            self.__insert1(OpcodeInfo.NEWARRAY)

    def convert_new_array(self, length: int):
        """
        Converts the creation of a new array

        :param length: the size of the new array
        """
        if length <= 0:
            self.convert_new_empty_array(length)
        else:
            self.__insert1(OpcodeInfo.PACK)

    def convert_set_new_array_item_at(self, index: int):
        """
        Converts the beginning of setting af a value in an array

        :param index: the index of the array that will be set
        """
        self.__insert1(OpcodeInfo.DUP)
        self.convert_literal(index)

    def convert_set_array_item(self):
        """
        Converts the end of setting af a value in an array
        """
        self.__insert1(OpcodeInfo.SETITEM)

    def convert_get_array_item(self):
        """
        Converts the end of get a value in an array
        """
        self.__insert1(OpcodeInfo.PICKITEM)

    def convert_load_symbol(self, symbol_id: str):
        """
        Converts the load of a symbol

        :param symbol_id: the symbol identifier
        """
        symbol = self.get_symbol(symbol_id)
        if symbol is not Type.none:
            if isinstance(symbol, Variable):
                self.convert_load_variable(symbol_id)
            elif isinstance(symbol, IBuiltinMethod) and symbol.opcode is not None:
                self.convert_builtin_method_call(symbol)
            else:
                self.convert_method_call(symbol)

    def convert_load_variable(self, var_id: str):
        """
        Converts the assignment of a variable

        :param var_id: the value to be converted
        """
        is_arg = False
        local = var_id in self.__current_method.symbols
        if local:
            is_arg = var_id in self.__args
            if is_arg:
                scope = self.__args
            else:
                scope = self.__locals
        else:
            scope = self.__globals

        index: int = scope.index(var_id)
        opcode = Opcode.get_load(index, local, is_arg)
        op_info = OpcodeInfo.get_info(opcode)

        if op_info.data_len > 0:
            self.__insert1(op_info, Integer(index).to_byte_array())
        else:
            self.__insert1(op_info)

    def convert_store_variable(self, var_id: str):
        """
        Converts the assignment of a variable

        :param var_id: the value to be converted
        """
        is_arg = False
        local = var_id in self.__current_method.symbols
        if local:
            is_arg = var_id in self.__args
            if is_arg:
                scope = self.__args
            else:
                scope = self.__locals
        else:
            scope = self.__globals

        index: int = scope.index(var_id)
        opcode = Opcode.get_store(index, local, is_arg)
        op_info = OpcodeInfo.get_info(opcode)

        if op_info.data_len > 0:
            self.__insert1(op_info, Integer(index).to_byte_array())
        else:
            self.__insert1(op_info)

    def convert_builtin_method_call(self, function: IBuiltinMethod):
        """
        Converts a builtin method function call

        :param function: the function to be converted
        """
        if function.opcode is not None:
            op_info = OpcodeInfo.get_info(function.opcode)
            self.__insert1(op_info)

    def convert_method_call(self, function: Method):
        """
        Converts a builtin method function call

        :param function: the function to be converted
        """
        if not self.__is_entry_point_converted or function.init_bytecode is None:
            self.__insert1(OpcodeInfo.CALL)
            self.__function_calls.append((self.last_code, function))
        else:
            function_address = Integer(function.bytecode_address - self.address)
            op_info = OpcodeInfo.CALL
            if len(function_address.to_byte_array(signed=True)) > op_info.max_data_len:
                op_info = OpcodeInfo.CALL_L

            data: bytes = function_address.to_byte_array(min_length=op_info.data_len, signed=True)
            self.__insert1(op_info, data)

    def __update_call(self, vmcode: VMCode, method: Method):
        """
        Updates the data of a jump code in the bytecode

        :param vmcode: call code
        :param method: new data of the code
        """
        relative_address = Integer(method.bytecode_address - vmcode.start_address)
        op_info = vmcode.info
        if len(relative_address.to_byte_array(signed=True)) > op_info.max_data_len:
            op_info = OpcodeInfo.CALL_L

        vmcode.update(op_info, relative_address.to_byte_array(min_length=op_info.data_len, signed=True))
        self.__function_calls.remove((vmcode, method))

    def convert_operation(self, operation: IOperation):
        """
        Converts an operation

        :param operation: the operation that will be converted
        """
        opcode: Opcode = operation.opcode

        if opcode is not None:
            op_info: OpcodeInformation = OpcodeInfo.get_info(opcode)
            self.__insert1(op_info)

    def __insert1(self, op_info: OpcodeInformation, data: bytes = bytes()):
        """
        Inserts one opcode into the bytecode

        :param op_info: info of the opcode  that will be inserted
        :param data: data of the opcode, if needed
        """
        last_code = self.last_code
        vm_code = VMCode(op_info, last_code, data)

        self.__vm_codes_without_order.append(vm_code)

    def __insert_jump(self, op_info: OpcodeInformation, jump_to: int):
        """
        Inserts a jump opcode into the bytecode

        :param op_info: info of the opcode  that will be inserted
        :param jump_to: data of the opcode
        """
        op_info, data = self.__get_jump_data(op_info, jump_to)    # type:OpcodeInformation, bytes
        self.__insert1(op_info, data)

    def __update_jump(self, jump_address: int, updated_jump_to: int):
        """
        Updates the data of a jump code in the bytecode

        :param jump_address: jump code start address
        :param updated_jump_to: new data of the code
        """
        vmcode: VMCode = self.__vm_codes_map[jump_address]
        if vmcode is not None:
            op_info, data = self.__get_jump_data(vmcode.info, updated_jump_to)  # type:OpcodeInformation, bytes
            vmcode.update(op_info, data)

    def __get_jump_data(self, op_info: OpcodeInformation, jump_to: int) -> Tuple[OpcodeInformation, bytes]:
        data: bytes = bytes()
        jmp_data: Integer = Integer(jump_to)

        if len(jmp_data.to_byte_array()) > op_info.max_data_len:
            opcode: Opcode = op_info.opcode.get_large_jump()
            if opcode is None:
                return op_info, data

            op_info = OpcodeInfo.get_info(opcode)
        data = jmp_data.to_byte_array(min_length=op_info.data_len, signed=True)

        return op_info, data
