from .stream import Video, Audio
from .coding import Encoding, Decoding
from ..util.pyopt import readonly_option

__all__ = [
    "CopyCoding"
]


class CopyCoding(Video, Audio, Encoding, Decoding):
    """
    FFmpeg copy codecs is special codecs. It do nothing - decode or encode video. Just copy.

    This codecs usually used in change muxers task.
    """
    def __init__(self):
        super().__init__()

        for attr, opt in self.options():
            setattr(self.__class__, attr, readonly_option(opt))
