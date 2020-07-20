import ast
import logging
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from boa3 import helpers
from boa3.analyser.astanalyser import IAstAnalyser
from boa3.analyser.importanalyser import ImportAnalyser
from boa3.builtin import NeoMetadata
from boa3.exception import CompilerError, CompilerWarning
from boa3.model.builtin.builtin import Builtin
from boa3.model.builtin.method.builtinmethod import IBuiltinMethod
from boa3.model.expression import IExpression
from boa3.model.importsymbol import Import
from boa3.model.method import Method
from boa3.model.module import Module
from boa3.model.symbol import ISymbol
from boa3.model.type.collection.icollection import ICollectionType as Collection
from boa3.model.type.collection.sequence.sequencetype import SequenceType
from boa3.model.type.type import IType, Type
from boa3.model.variable import Variable


class ModuleAnalyser(IAstAnalyser, ast.NodeVisitor):
    """
    This class is responsible for mapping the locals of the functions and modules

    The methods with the name starting with 'visit_' are implementations of methods from the :class:`NodeVisitor` class.
    These methods are used to walk through the Python abstract syntax tree.

    :ivar modules: a dictionary that maps each module with its name. Empty by default.
    :ivar symbols: a dictionary that maps the global symbols.
    """

    def __init__(self, analyser, symbol_table: Dict[str, ISymbol], filename: str = None, log: bool = False):
        super().__init__(analyser.ast_tree, filename, log)
        self.modules: Dict[str, Module] = {}
        self.symbols: Dict[str, ISymbol] = symbol_table

        self._builtin_functions_to_visit: Dict[str, IBuiltinMethod] = {}
        self._current_module: Module = None
        self._current_method: Method = None

        self._metadata: NeoMetadata = None
        self._metadata_node: ast.AST = ast.parse('')
        self.imported_nodes: List[ast.AST] = []
        self.visit(self._tree)

        self._validate_metadata_symbols()
        analyser.metadata = self._metadata if self._metadata is not None else NeoMetadata()

    @property
    def _current_scope(self):
        """
        Returns the scope that is currently being analysed

        :return: the current scope. Return None if it is the global scope
        :rtype: Method or Module or None
        """
        if self._current_method is not None:
            return self._current_method
        return self._current_module

    @property
    def global_symbols(self) -> Dict[str, ISymbol]:
        """
        Returns the symbols in global scope

        :return: the symbol table of the global scope
        """
        global_symbols: Dict[str, ISymbol] = {}

        global_symbols.update(self.symbols)
        for mod in self.modules.values():
            global_symbols.update(mod.symbols)

        return global_symbols

    def __include_variable(self, var_id: str, var_type_id: Union[str, IType],
                           source_node: ast.AST, var_enumerate_type: IType = Type.none):
        """
        Includes the variable in the symbol table if the id was not used

        :param var_id: variable id
        :param var_type_id: variable type id
        :type var_type_id: str or IType
        :param var_enumerate_type: variable value type id if var_type_id is a SequenceType
        """
        if var_id not in self._current_scope.symbols:
            outer_symbol = self.get_symbol(var_id)
            if outer_symbol is not None:
                self._log_warning(
                    CompilerWarning.NameShadowing(source_node.lineno, source_node.col_offset, outer_symbol, var_id)
                )

            var_type = None
            if isinstance(var_type_id, SequenceType):
                var_type = var_type_id
                var_enumerate_type = self.get_enumerate_type(var_type)
            elif isinstance(var_type_id, IType):
                var_type = var_type_id

            # when setting a None value to a variable, set the variable as any type
            if var_type is Type.none:
                var_type = Type.any

            if isinstance(var_type, IType) or var_type is None:
                # if type is None, the variable type depends on the type of a expression
                if isinstance(var_type, SequenceType):
                    var_type = var_type.build_collection(var_enumerate_type)
                var = Variable(var_type)
                self._current_scope.include_variable(var_id, var)

    def __include_method(self, method_id: str, method: Method):
        """
        Includes the method in the symbol table if the id was not used

        :param method_id: method id
        :param method: method to be included
        """
        if method_id not in self._current_module.symbols:
            self._current_module.include_method(method_id, method)

    def get_symbol(self, symbol_id: str) -> Optional[ISymbol]:
        if symbol_id in self._current_scope.symbols:
            # the symbol exists in the local scope
            return self._current_scope.symbols[symbol_id]
        elif symbol_id in self._current_module.symbols:
            # the symbol exists in the module scope
            return self._current_module.symbols[symbol_id]
        else:
            return super().get_symbol(symbol_id)

    # region Log

    def _log_import(self, import_from: str):
        if self._log:
            logging.info("Importing '{0}'".format(import_from))

    def _log_unresolved_import(self, origin_node: ast.AST, import_id: str):
        if self._log:
            self._log_error(
                CompilerError.UnresolvedReference(
                    line=origin_node.lineno,
                    col=origin_node.col_offset,
                    symbol_id=import_id
                )
            )

    # endregion

    # region Metadata

    def _read_metadata_object(self, function: ast.FunctionDef):
        """
        Gets the metadata object defined in this function

        :param function:
        """
        if self._metadata is not None:
            # metadata function has been defined already
            self._log_warning(
                CompilerWarning.RedeclaredSymbol(
                    line=function.lineno, col=function.col_offset,
                    symbol_id=Builtin.Metadata.identifier
                )
            )
        # this function must have a return and no arguments
        elif len(function.args.args) != 0:
            self._log_error(
                CompilerError.UnexpectedArgument(
                    line=function.lineno, col=function.col_offset
                )
            )
        elif not any(isinstance(stmt, ast.Return) for stmt in function.body):
            self._log_error(
                CompilerError.MissingReturnStatement(
                    line=function.lineno, col=function.col_offset,
                    symbol_id=function.name
                )
            )
        else:
            function.returns = None
            function.decorator_list = []
            module: ast.Module = ast.parse('')
            module.body = [node for node in self._tree.body
                           if isinstance(node, (ast.ImportFrom, ast.Import))]
            module.body.append(function)
            ast.copy_location(module, function)

            # executes the function
            code = compile(module, filename='<boa3>', mode='exec')
            namespace = {}
            exec(code, namespace)
            obj: Any = namespace[function.name]()

            node: ast.AST = function.body[-1] if len(function.body) > 0 else function
            # return must be a NeoMetadata object
            if not isinstance(obj, NeoMetadata):
                obj_type = self.get_type(obj).identifier if self.get_type(obj) is not Type.any else type(obj).__name__
                self._log_error(
                    CompilerError.MismatchedTypes(
                        line=node.lineno, col=node.col_offset,
                        expected_type_id=NeoMetadata.__name__,
                        actual_type_id=obj_type
                    )
                )
                return

            # validates the metadata attributes types
            attributes: Dict[str, Any] = {attr: value
                                          for attr, value in dict(obj.__dict__).items()
                                          if attr in Builtin.metadata_fields}
            if any(not isinstance(value, Builtin.metadata_fields[attr]) for attr, value in attributes.items()):
                for expected, actual in [(Builtin.metadata_fields[attr], type(v_type))
                                         for attr, v_type in attributes.items()
                                         if not isinstance(v_type, Builtin.metadata_fields[attr])]:
                    if isinstance(expected, Iterable):
                        expected_id = 'Union[{0}]'.format(', '.join([tpe.__name__ for tpe in expected]))
                    elif hasattr(expected, '__name__'):
                        expected_id = expected.__name__
                    else:
                        expected_id = str(expected)

                    self._log_error(
                        CompilerError.MismatchedTypes(
                            line=node.lineno, col=node.col_offset,
                            expected_type_id=expected_id,
                            actual_type_id=actual.__name__
                        )
                    )
            else:
                # if the function was defined correctly, sets the metadata object of the smart contract
                self._metadata = obj
                self._metadata_node = function  # for error messages only

    def _validate_metadata_symbols(self):
        """
        Validates if the symbols match the requirements from the given metadata
        """
        if self._metadata is not None:
            if self._metadata.is_payable:
                """
                Payable smart contracts requires the implementation of a 'verify' function, that must implement the
                following signature:

                ```
                @public
                def verify(*args) -> bool
                ```
                """
                verify_id: str = 'verify'
                if (verify_id not in self.global_symbols  # couldn't find verify
                    or not isinstance(self.global_symbols[verify_id], Method)  # verify is not a function
                    or self.global_symbols[verify_id].origin is None  # verify is not a user function
                    ):
                    self._log_error(
                        CompilerError.MetadataImplementationMissing(
                            line=self._metadata_node.lineno, col=self._metadata_node.col_offset,
                            symbol_id=verify_id,
                            metadata_attr_id='is_payable'
                        )
                    )
                elif (self.global_symbols[verify_id].return_type != Type.bool
                      or not self.global_symbols[verify_id].is_public
                      ):
                    actual = self.global_symbols[verify_id]
                    expected = Method(actual.args, Type.bool, True)
                    self._log_error(
                        CompilerError.MetadataIncorrectImplementation(
                            line=actual.origin.lineno, col=actual.origin.col_offset,
                            symbol_id=verify_id,
                            expected_symbol=expected,
                            actual_symbol=actual
                        )
                    )

    # endregion

    # region AST

    def visit_ImportFrom(self, import_from: ast.ImportFrom):
        """
        Includes methods and variables from other modules into the current scope

        :param import_from:
        """
        self._log_import(import_from.module)
        analyser = self._analyse_module_to_import(import_from, import_from.module)
        if analyser is not None:
            import_alias: Dict[str] = \
                {alias.name: alias.asname if alias.asname is not None else alias.name for alias in import_from.names}

            new_symbols: Dict[str, ISymbol] = analyser.export_symbols(list(import_alias.keys()))
            # includes the module to be able to generate the functions
            imported_module = Import(analyser.tree, new_symbols)
            self._current_scope.include_symbol(import_from.module, imported_module)

            for name, alias in import_alias.items():
                if name in new_symbols:
                    self._current_scope.include_symbol(alias, imported_module.symbols[name])
                else:
                    # if there's a symbol that couldn't be loaded, log a compiler error
                    self._log_unresolved_import(import_from, name)

    def _analyse_module_to_import(self, origin_node: ast.AST, target: str) -> Optional[ImportAnalyser]:
        analyser = ImportAnalyser(target)
        if analyser.can_be_imported:
            return analyser
        else:
            self._log_unresolved_import(origin_node, target)

    def visit_Import(self, import_node: ast.Import):
        """
        Includes methods and variables from other modules into the current scope

        :param import_node:
        """
        import_alias: Dict[str] = \
            {alias.name: alias.asname if alias.asname is not None else alias.name for alias in import_node.names}

        for target, alias in import_alias.items():
            self._log_import(target)
            analyser = self._analyse_module_to_import(import_node, target)
            if analyser is not None:
                new_symbols: Dict[str, ISymbol] = analyser.export_symbols()
                for symbol in [symbol for symbol in analyser.symbols if symbol not in new_symbols]:
                    # if there's a symbol that couldn't be loaded, log a compiler error
                    self._log_unresolved_import(import_node, '{0}.{1}'.format(target, symbol))

                imported_module = Import(analyser.tree, new_symbols)
                self._current_scope.include_symbol(alias, imported_module)

    def visit_Module(self, module: ast.Module):
        """
        Visitor of the module node

        Fills module symbol table

        :param module:
        """
        mod: Module = Module()
        self._current_module = mod

        # don't evaluate constant expression - for example: string for documentation
        module.body = [stmt for stmt in module.body
                       if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))]
        for stmt in module.body.copy():
            result = self.visit(stmt)
            # don't evaluate the metadata function in the following analysers
            if result is Builtin.Metadata:
                module.body.remove(stmt)

        # TODO: include the body of the builtin methods to the ast
        # TODO: get module name
        self.modules['main'] = mod
        self._current_module = None

    def visit_FunctionDef(self, function: ast.FunctionDef):
        """
        Visitor of the function node

        Includes the method in the scope of its module

        :param function:
        """
        fun_args = self.visit(function.args)
        fun_rtype_symbol = self.visit(function.returns) if function.returns is not None else Type.none

        if fun_rtype_symbol is None:
            # it is a function with None return: Main(a: int) -> None:
            raise NotImplementedError

        if isinstance(fun_rtype_symbol, str):
            symbol = self.get_symbol(function.returns.id)
            fun_rtype_symbol = self.get_type(symbol)

        fun_return: IType = self.get_type(fun_rtype_symbol)
        fun_decorators: List[Method] = self._get_function_decorators(function)

        if Builtin.Metadata in fun_decorators:
            self._read_metadata_object(function)
            return Builtin.Metadata

        method = Method(args=fun_args, return_type=fun_return, origin_node=function,
                        is_public=Builtin.Public in fun_decorators)
        self._current_method = method

        # don't evaluate constant expression - for example: string for documentation
        function.body = [stmt for stmt in function.body
                         if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))]
        for stmt in function.body:
            self.visit(stmt)

        self.__include_method(function.name, method)
        self._current_method = None

    def _get_function_decorators(self, function: ast.FunctionDef) -> List[Method]:
        """
        Gets a list of the symbols used to decorate the given function

        :param function: python ast function definition node
        :return: a list with all function decorators. Empty if none decorator is found.
        """
        return [self.get_symbol(self.visit(decorator)) for decorator in function.decorator_list]

    def visit_arguments(self, arguments: ast.arguments) -> Dict[str, Variable]:
        """
        Visitor of the function arguments node

        :param arguments:
        :return: a dictionary that maps each argument to its identifier
        """
        args: Dict[str, Variable] = {}

        for arg in arguments.args:
            var_id, var = self.visit_arg(arg)   # Tuple[str, Variable]
            args[var_id] = var
        return args

    def visit_arg(self, arg: ast.arg) -> Tuple[str, Variable]:
        """
        Visitor of a function argument node

        :param arg:
        :return: a tuple with the identifier and the argument
        """
        var_id = arg.arg
        var_type: IType = self.get_type(arg.annotation)

        if var_type is Type.none and isinstance(arg.annotation, ast.Name):
            var_symbol: ISymbol = self.get_symbol(arg.annotation.id)
            var_type = self.get_type(var_symbol)

        return var_id, Variable(var_type)

    def visit_Return(self, ret: ast.Return):
        """
        Visitor of the function return node

        If the return is a name, verifies if the symbol is defined

        :param ret: the python ast return node
        """
        if isinstance(ret.value, ast.Name):
            symbol_id = self.visit(ret.value)
            symbol = self.get_symbol(symbol_id)
            if symbol is None:
                # the symbol doesn't exists
                self._log_error(
                    CompilerError.UnresolvedReference(ret.value.lineno, ret.value.col_offset, symbol_id)
                )

    def visit_type(self, target: ast.AST) -> Optional[IType]:
        """
        Gets the type by its identifier

        :param target: ast node to be evaluated
        :return: the type of the value inside the node. None by default
        """
        target_type = self.visit(target)  # Type:str or IType
        if isinstance(target_type, str) and not isinstance(target, ast.Str):
            symbol = self.get_symbol(target_type)
            if symbol is None:
                # the symbol doesn't exists
                self._log_error(
                    CompilerError.UnresolvedReference(target.lineno, target.col_offset, target_type)
                )
            target_type = symbol

        if target_type is None and not isinstance(target, ast.NameConstant):
            # the value type is invalid
            return None

        if not isinstance(target_type, (ast.AST, IType, IExpression)) and isinstance(target_type, ISymbol):
            self._log_error(
                CompilerError.UnresolvedReference(
                    line=target.lineno, col=target.col_offset,
                    symbol_id=str(target_type)
                )
            )
        return self.get_type(target_type)

    def get_enumerate_type(self, var_type: IType) -> IType:
        return var_type.value_type if isinstance(var_type, SequenceType) else Type.none

    def visit_Assign(self, assign: ast.Assign):
        """
        Visitor of the variable assignment node

        Includes the variable in its scope if it's the first use

        :param assign:
        """
        var_id = self.visit(assign.targets[0])
        var_type = self.visit_type(assign.value)

        self.__include_variable(var_id, var_type, source_node=assign)

    def visit_AnnAssign(self, ann_assign: ast.AnnAssign):
        """
        Visitor of the annotated variable assignment node

        Includes the variable in its scope if it's the first use

        :param ann_assign:
        """
        var_id: str = self.visit(ann_assign.target)
        var_type: IType = self.visit_type(ann_assign.annotation)

        # TODO: check if the annotated type and the value type are the same
        self.__include_variable(var_id, var_type, source_node=ann_assign)

    def visit_Expr(self, expr: ast.Expr):
        """
        Visitor of the atom expression node

        :param expr:
        """
        value = self.visit(expr.value)
        if isinstance(expr.value, ast.Name):
            if (
                # it is not a symbol of the method scope
                (self._current_method is not None and value not in self._current_method.symbols)
                # nor it is a symbol of the module scope
                or (self._current_module is not None and value not in self._current_module.symbols)
                # nor it is a symbol of the global scope
                or value not in self.symbols
            ):
                self._log_error(
                    CompilerError.UnresolvedReference(expr.value.lineno, expr.value.col_offset, value)
                )

    def visit_Subscript(self, subscript: ast.Subscript):
        """
        Verifies if it is the types in the subscription are valid

        :param subscript: the python ast subscription node
        :return: if the subscript is not a symbol, returns its type. Otherwise returns the symbol id.
        :rtype: IType or str
        """
        value = self.visit(subscript.value)
        symbol = self.get_symbol(value) if isinstance(value, str) else value

        if isinstance(subscript.ctx, ast.Load):
            if isinstance(symbol, Collection):
                values_type: Iterable[IType] = self.get_values_type(subscript.slice.value)
                return symbol.build_collection(*values_type)

            symbol_type = self.get_type(symbol)
            if isinstance(symbol_type, SequenceType):
                return symbol_type.value_type

        return value

    def get_values_type(self, value: ast.AST) -> Iterable[Optional[IType]]:
        """
        Verifies if it is a multiple assignments statement

        :param value: the python ast subscription node
        """
        value_type: Optional[IType] = None

        if isinstance(value, (ast.Subscript, ast.Attribute, ast.Tuple)):
            # index is another subscription
            value_type = self.visit(value)
        elif isinstance(value, ast.Name):
            # index is an identifier
            value_type = self.get_symbol(value.id)

        types: Iterable[Optional[IType]] = value_type if isinstance(value_type, Iterable) else [value_type]
        for tpe in types:
            if not isinstance(tpe, IType):
                # type hint not using identifiers or using identifiers that are not types
                index = self.visit(value)
                self._log_error(
                    CompilerError.UnresolvedReference(value.lineno, value.col_offset, index)
                )

        return types

    def visit_Call(self, call: ast.Call) -> Optional[IType]:
        """
        Visitor of a function call node

        :param call: the python ast function call node
        :return: the result type of the called function. None if the function is not found
        """
        func_id = self.visit(call.func)
        func_symbol = self.get_symbol(func_id)

        # if func_symbol is None, the called function may be a function written after in the code
        # that's why it shouldn't log a compiler error here
        if func_symbol is None:
            return None

        if not isinstance(func_symbol, Method):
            # verifiy if it is a builtin method with its name shadowed
            func = Builtin.get_symbol(func_id)
            func_symbol = func if func is not None else func_symbol
        if not isinstance(func_symbol, Method):
            # the symbol doesn't exists
            self._log_error(
                CompilerError.UnresolvedReference(call.func.lineno, call.func.col_offset, func_id)
            )
        elif isinstance(func_symbol, IBuiltinMethod) and func_symbol.body is not None:
            self._builtin_functions_to_visit[func_id] = func_symbol

        return self.get_type(call.func)

    def visit_Attribute(self, attribute: ast.Attribute) -> Union[ISymbol, str]:
        """
        Gets the attribute inside the ast node

        :param attribute: the python ast attribute node
        :return: returns the type of the value, the attribute symbol and its id if the attribute exists.
                 Otherwise, returns None
        """
        value_id = attribute.value.id if isinstance(attribute.value, ast.Name) else None
        value: ISymbol = self.get_symbol(value_id) if value_id is not None else self.visit(attribute.value)

        if hasattr(value, 'symbols') and attribute.attr in value.symbols:
            return value.symbols[attribute.attr]
        elif Builtin.get_symbol(attribute.attr) is not None:
            return Builtin.get_symbol(attribute.attr)
        else:
            return '{0}.{1}'.format(value_id, attribute.attr)

    def visit_For(self, for_node: ast.For):
        """
        Visitor of for statement node

        :param for_node: the python ast for node
        """
        iter_type = self.get_type(for_node.iter)
        targets = self.visit(for_node.target)

        if isinstance(iter_type, SequenceType):
            if isinstance(targets, str):
                self.__include_variable(targets, iter_type.value_type, source_node=for_node.target)
            else:
                for target in targets:
                    if isinstance(target, str):
                        self.__include_variable(target, iter_type.value_type, source_node=for_node.target)

            for_iter_id = helpers.get_auxiliary_name(for_node, 'iter')
            for_index_id = helpers.get_auxiliary_name(for_node, 'index')

            self.__include_variable(for_iter_id, iter_type, source_node=for_node.iter)
            self.__include_variable(for_index_id, iter_type.valid_key, source_node=for_node)

        # continue to walk through the tree
        self.generic_visit(for_node)

    def visit_Name(self, name: ast.Name) -> str:
        """
        Visitor of a name node

        :param name:
        :return: the identifier of the name
        """
        return name.id

    def visit_NameConstant(self, constant: ast.NameConstant) -> Any:
        """
        Visitor of constant names node

        :param constant:
        :return: the value of the constant
        """
        return constant.value

    def visit_Num(self, num: ast.Num) -> int:
        """
        Visitor of literal number node

        :param num:
        :return: the value of the number
        """
        return num.n

    def visit_Str(self, str: ast.Str) -> str:
        """
        Visitor of literal string node

        :param str:
        :return: the value of the string
        """
        return str.s

    def visit_Tuple(self, tup_node: ast.Tuple) -> Tuple[Any, ...]:
        """
        Visitor of literal tuple node

        :param tup_node: the python ast string node
        :return: the value of the tuple
        """
        return tuple([self.get_type(value) for value in tup_node.elts])

    def visit_List(self, list_node: ast.List) -> List[Any]:
        """
        Visitor of literal list node

        :param list_node: the python ast list node
        :return: the value of the list
        """
        return [self.get_type(value) for value in list_node.elts]

    def visit_Dict(self, dict_node: ast.Dict) -> Dict[Any, Any]:
        """
        Visitor of literal dict node

        :param dict_node: the python ast dict node
        :return: the value of the dict
        """
        dictionary = {}
        size = min(len(dict_node.keys), len(dict_node.values))
        for index in range(size):
            key = self.get_type(dict_node.keys[index])
            value = self.get_type(dict_node.values[index])
            if key in dictionary and dictionary[key] != value:
                dictionary[key] = Type.get_generic_type(dictionary[key], value)
            else:
                dictionary[key] = value
        return dictionary

    # endregion
