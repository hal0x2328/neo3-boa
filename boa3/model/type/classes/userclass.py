from typing import Any, Dict, Optional

from boa3.model.callable import Callable
from boa3.model.method import Method
from boa3.model.property import Property
from boa3.model.symbol import ISymbol
from boa3.model.type.classes.classarraytype import ClassArrayType
from boa3.model.type.classes.classscope import ClassScope
from boa3.model.type.itype import IType
from boa3.model.variable import Variable


class UserClass(ClassArrayType):
    def __init__(self, identifier: str):
        super(ClassArrayType, self).__init__(identifier)

        self._static_methods: Dict[str, Method] = {}

        self._class_variables: Dict[str, Variable] = {}
        self._class_methods: Dict[str, Method] = {}

        self._instance_variables: Dict[str, Variable] = {}
        self._instance_methods: Dict[str, Method] = {}
        self._properties: Dict[str, Property] = {}

        self.imported_symbols = {}

    @property
    def shadowing_name(self) -> str:
        return 'class'

    @property
    def class_variables(self) -> Dict[str, Variable]:
        return self._class_variables.copy()

    @property
    def instance_variables(self) -> Dict[str, Variable]:
        return self._instance_variables.copy()

    @property
    def properties(self) -> Dict[str, Property]:
        return self._properties.copy()

    @property
    def static_methods(self) -> Dict[str, Method]:
        return self._static_methods.copy()

    @property
    def class_methods(self) -> Dict[str, Method]:
        return self._class_methods.copy()

    @property
    def instance_methods(self) -> Dict[str, Method]:
        return self._instance_methods.copy()

    def include_variable(self, var_id: str, var: Variable, is_instance: bool):
        """
        Includes a variable into the list of class variables

        :param var_id: variable identifier
        :param var: variable to be included
        :param is_instance: whether is a instance variable or a class variable
        """
        # TODO: change when user class variables are implemented
        pass

    def include_callable(self, method_id: str, method: Callable, scope: ClassScope):
        """
        Includes a method into the scope of the class

        :param method_id: method identifier
        :param method: method to be included
        :param scope: which class scope this method should be included
        """
        # TODO: change when user class methods are implemented
        pass

    def include_symbol(self, symbol_id: str, symbol: ISymbol, scope: ClassScope = ClassScope.INSTANCE):
        """
        Includes a method into the scope of the module

        :param symbol_id: method identifier
        :param symbol: method to be included
        :param scope: which class scope this symbol should be included
        """
        if symbol_id not in self.symbols:
            if isinstance(symbol, Variable):
                self.include_variable(symbol_id, symbol, scope == ClassScope.INSTANCE)
            elif isinstance(symbol, Callable):
                self.include_callable(symbol_id, symbol, scope)
            else:
                self.imported_symbols[symbol_id] = symbol

    def constructor_method(self) -> Optional[Method]:
        # TODO: change when user class init is implemented
        return None

    @classmethod
    def _is_type_of(cls, value: Any) -> bool:
        return False

    @classmethod
    def build(cls, value: Any) -> IType:
        return cls()
