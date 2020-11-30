"""
FFmpeg configuration (key=value)

Generate and handle config of FFmpeg params or option:
- x264opts, x264-params: https://ffmpeg.org/ffmpeg-codecs.html#libx264_002c-libx264rgb
- ...

Notes: check possible value before add.

Implementor: tindangai-97
"""

from typing import Union, TypeVar, Mapping

SEPARATOR = ":"
SETTER = "="

ArgType = TypeVar('ArgType', str, int, float)
ParamsType = Mapping[str, ArgType]
KeyType = Union[str]

__all__ = [
    'Params', 'ParamsType'
]


def check_type(value, _type):
    if not isinstance(value, _type):
        raise TypeError(f"Value must be {_type}.")
    return value


class Params(dict):
    """
    FFmpeg configuration (key=value)
    """
    def __init__(self, conf: Union[str, ParamsType, None] = None):
        super().__init__()
        if conf is not None:
            self.update(conf)

    def __repr__(self):
        return self.get_configs()

    def __setitem__(self, key: KeyType, value: ArgType):
        if isinstance(value, str):
            value = value.strip()
        super(Params, self).__setitem__(key, check_type(value, ArgType.__constraints__))

    def __iadd__(self, other):
        self.update(other)
        return self

    def delete(self, conf: str):
        self.__delitem__(conf)

    def update(self, conf: Union[str, ParamsType], **kwargs) -> None:
        if isinstance(conf, str):
            _mapping_config = conf.split(SEPARATOR)
            conf = {}
            for opt in _mapping_config:
                try:
                    k, v = opt.split(SETTER)
                    conf[k] = v
                except ValueError:
                    raise ValueError(f"Wrong format. `{opt}`") from None

        elif not isinstance(conf, dict):
            raise TypeError(f"Type of conf `{type(conf)} isn't supported.`")

        conf.update(conf, **kwargs)
        for k, v in conf.items():
            self.__setitem__(k, v)

    def add(self, conf: KeyType, value: ArgType):
        self.__setitem__(conf, value)

    def get_configs(self) -> str:
        """
        Build value of parameter ffmpegpy with value and configs

        Returns
        -------
            Sequence character of configs like key=value:key2=value2
        """
        if not self:
            return ""
        return f"{SEPARATOR.join([f'{config}{SETTER}{value}' for config, value in self.items()])}"
