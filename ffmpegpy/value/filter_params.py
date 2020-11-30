"""
FFmpeg Filter parameters


Notes: check possible value before add.

Implementor: tindangai-97
"""


from typing import Union, TypeVar, Mapping, List, Tuple
from .params import Params
from ..util import check_type

SEPARATOR = ":"
SETTER = "="

ArgType = TypeVar('ArgType', str, int, float)
ArgsType = Union[List[ArgType], Tuple[ArgType]]
ParamsType = Mapping[str, ArgType]
KeyType = Union[str]


class Args(list):
    def __init__(self, args: Union[str, ArgsType, ArgType] = ()):
        super().__init__()
        if isinstance(args, str):
            args = args.split(SEPARATOR)

        if isinstance(args, (list, tuple)):
            self.extend(args)
        else:
            self.add(args)

    def __repr__(self) -> str:
        return self.get_args()

    def __setitem__(self, index, value):
        if isinstance(value, str):
            value = value.strip()
        super(Args, self).__setitem__(index, check_type(value, ArgType.__constraints__))

    def __iadd__(self, other: Union[str, ArgsType] = ()):
        self.concatenate(other)
        return self

    def concatenate(self, other: Union[str, ArgsType] = ()):
        if isinstance(other, str):
            other = other.split(SEPARATOR)
        self.extend(other)

    def extend(self, args: ArgsType):
        for arg in args:
            self.append(arg)

    def add(self, value: ArgType):
        self.append(value)

    def append(self, value: ArgType) -> None:
        return super(Args, self).append(check_type(value.strip(), ArgType.__constraints__))

    def get_args(self) -> str:
        return SEPARATOR.join(map(str, self))


class FilterParam:
    """

    FFmpeg Filter Params (filter=value:value2:kwarg=value3, filter2=value)

    Examples:
        Params access setup:
            - (str) params converted
            - (list, tuple) list of value
            - (dict) configs
    """

    def __init__(self, key: KeyType, setup: Union[str, ArgsType, ParamsType]):
        self.__key = key
        self.__args = Args()
        self.__config = Params()

        if isinstance(setup, (list, tuple)):
            self.__args.extend(setup)
        elif isinstance(setup, dict):
            self.__config.update(setup)
        else:
            self.concatenate(setup)

    def __repr__(self):
        return self.get_param()

    def __iadd__(self, other: Union['Params', str]):
        self.concatenate(other)

    @property
    def key(self) -> str:
        return self.__key

    @key.setter
    def key(self, _key: KeyType):
        if not isinstance(_key, str):
            raise TypeError("Key must be str.")
        self.__key = _key

    @property
    def args(self) -> Args:
        return self.__args

    @args.setter
    def args(self, _value: Union[str, ArgsType]):
        if isinstance(_value, Args):
            self.__args = _value
        else:
            self.__args = Args(_value)

    @args.deleter
    def args(self):
        self.__args = Args()

    @property
    def config(self) -> Params:
        return self.__config

    @config.setter
    def config(self, _config: Union[str, ArgsType]):
        if isinstance(_config, Params):
            self.__config = _config
        else:
            self.__config = Params(_config)

    @config.deleter
    def config(self):
        self.__config.clear()

    def add(self, setting, value: Union[ArgType, None] = None):
        """Add setting, `value`==None mean config not have any value."""
        if value is None:
            self.__args.add(setting)
        else:
            self.__config.add(setting, value)

    def get_param(self):
        if not self.__args and not self.__config:
            raise ValueError("Parameters configs empty error")

        if not self.__config:
            return f"{self.__key}={self.args}"

        if not self.args:
            return f"{self.__key}={self.config}"
        return f"{self.__key}={self.args}:{self.config}"

    def concatenate(self, other: Union['FilterParam', str]):
        if isinstance(other, str):
            for opt in other.split(SEPARATOR):
                if SETTER in opt:
                    self.__config.update(opt)
                else:
                    self.__args.add(opt)

        elif isinstance(other, FilterParam) and other.key == self.key:
            self.__args.extend(other.__args)
            self.__config.update(other.__config)
        else:
            raise TypeError(f"Type `{type(other)}` not support concatenate.")
