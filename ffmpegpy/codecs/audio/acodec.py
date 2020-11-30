from ffmpegpy.util.pyopt import option, Option
from ..coding import Encoding, Decoding, Codec
from ..stream import Audio

__all__ = [
    "AudioCodec", "AudioDecoding", "AudioEncoding"
]


def aoption(opt):
    if not isinstance(opt, Option):
        raise TypeError("opt must be Option")
    return option(f"{opt.name}:a", opt.set_filter, opt.default_value, opt.doc)


class AudioCodec(Codec):
    pass


class AudioDecoding(Audio, Decoding):
    pass


class AudioEncoding(Audio, Encoding):
    def __init__(self):
        for name, opt in self.options():
            if not getattr(Encoding, name, False):
                continue
            if opt.name.endswith(":v"):
                continue
            setattr(self.__class__, name, aoption(opt))
        super().__init__()
