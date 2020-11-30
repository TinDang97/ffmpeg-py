from typing import Callable, Any, Iterable, Type, Union


def stacks_filter(funcs: Iterable[Callable[[Any], Any]]) -> Callable[[Any], Any]:
    """
    Stack multi-filter function

    Args:
        funcs:
            list of filter function

    Returns:
        Callable of all filter.
    """
    def _func(_value: Any):
        for func in funcs:
            _value = func(_value)
        return _value
    return _func


def min_value_filter(_min: Union[int, float]) -> Callable[[Union[int, float]], Union[int, float]]:
    """
    Create check minimum value of option when set.

    Args:
        _min: Minimum accessible value
    Returns:
        As input value if larger or equal minimum value.

    Raises:
        TypeError: if value is any values other than integer.
        ValueError: Value smaller than minimum value.
    """
    def _func(_value: int) -> int:
        if not isinstance(_value, (float, int)):
            raise TypeError("Value must be int.")

        if _value < _min:
            raise ValueError(f"Value must >= {_min}. MIN: {_min}")
        return _value

    return _func


def max_value_filter(_max: Union[int, float]) -> Callable[[Union[int, float]], Union[int, float]]:
    """
    Create check maximum value of option when set.

    Args:
        _max: Maximum accessible value
    Returns:
        As input value if larger or equal maximum value.

    Raises:
        TypeError: if value is any values other than integer.
        ValueError: if value larger than maximum value.
    """
    def _func(_value: Union[int, float]) -> Union[int, float]:
        if not isinstance(_value, (float, int)):
            raise TypeError("Value must be int.")

        if _value > _max:
            raise ValueError(f"Value must <= {_max}. MAX: {_max}")
        return _value
    return _func


def in_range_filter(_min: Union[int, float], _max: Union[int, float]) \
        -> Callable[[Union[int, float]], Union[int, float]]:
    """
    Combine min_value_filter and max_value_filter

    Args:
        _min: Minimum accessible value
        _max: Maximum accessible value

    Returns:
        As input value in range [_min, _max].
    """
    def _func(_value: Union[int, float]) -> Union[int, float]:
        if not isinstance(_value, (float, int)):
            raise TypeError("Value must be int or float.")

        if _value not in range(_min, _max + 1):
            raise ValueError(f"Value must in [{_min}, {_max}].")
        return _value
    return _func


def is_not_params_filter(_value: None):
    """
    Not access any value except None - active this params.

    Args:
        _value: None
    Returns:
        None
    """
    if _value is not None:
        raise ValueError("No require parameters. Set value is `None` to active option.")
    return _value


def in_list_filter(_list: Iterable) -> Callable[[Any], Any]:
    """
    Deny any set value not in access list.

    Args:
        _list: accessible values.
    """
    def _func(_value: Any):
        if _value not in _list:
            raise ValueError(f'Value must in {_list}. But got "{_value}"')
        return _value

    return _func


def type_filter(_type: [Iterable[Type], Type]) -> Callable[[Any], Any]:
    """
    Deny any set value, unless value's type not in access list.

    Args:
        _type: accessible types
    """
    if not isinstance(_type, Iterable):
        _type = (_type, )

    def _func(_value: Any):
        if not isinstance(_value, tuple(_type)):
            raise ValueError(f"Value's type must be {_type}. But got \"{type(_value)}\"")
        return _value
    return _func
