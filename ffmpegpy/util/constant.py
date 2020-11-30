from inspect import isclass

__all__ = ["constant_class", "ConstantBase", "ConstantClass"]


def constants(cls):
    for k in sorted(dir(cls)):
        # remove protected and private attribute
        if k.startswith("_"):
            continue
        yield k


def restrict_write(*args, **kwargs):
    raise AttributeError("Read-only restricted!")


def iter_attr(cls):
    _lst = [cls[k] for k in constants(cls)]
    return _lst.__iter__()


def repr_attr(cls):
    return " | ".join(f'{k}=\"{cls[k]}\"' for k in constants(cls))


def contain_value(cls, value):
    for k in constants(cls):
        if cls[k] == value:
            return True
    return False


def get_attr(cls, attr):
    if attr not in constants(cls):
        raise KeyError
    return getattr(cls, attr)


class ConstantBase(type):
    __setattr__ = restrict_write
    __iter__ = iter_attr
    __contains__ = contain_value
    __repr__ = repr_attr
    __getitem__ = get_attr


class ConstantClass(metaclass=ConstantBase):
    __setattr__ = restrict_write
    __iter__ = iter_attr
    __contains__ = contain_value
    __repr__ = repr_attr
    __getitem__ = get_attr


def constant_class(_class: type) -> type:
    """
    Decorator, which creates a class with changing restricted variables.
    """
    if not isclass(_class):
        raise TypeError("_class isn't class type.")

    _dict = dict(_class.__dict__.copy())
    _base = tuple([ConstantClass, *_class.__bases__])
    _name = str(_class.__name__)

    _dict.pop('__dict__', ConstantClass.__dict__)
    _dict["__wrapped__"] = _class
    _dict["__metaclass__"] = ConstantBase

    _class = ConstantBase(_name, _base, _dict)
    return _class
