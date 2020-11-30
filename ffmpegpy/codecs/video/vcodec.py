from ffmpegpy.util.pyopt import option, Option, min_value_filter, in_range_filter, type_filter
from ..coding import Encoding, Decoding, Codec
from ..stream import Video

__all__ = [
    "VideoDecoding", "VideoEncoding", "VideoCodec"
]


def voption(opt):
    if not isinstance(opt, Option):
        raise TypeError("opt must be Option")
    return option(f"{opt.name}:v", opt.set_filter, opt.default_value, opt.doc)


class VideoCodec(Codec):
    pass


class VideoDecoding(Video, Decoding):
    pass


class VideoEncoding(Video, Encoding):
    def __init__(self):
        for name, opt in self.options():
            if not getattr(Encoding, name, False):
                continue
            if opt.name.endswith(":v"):
                continue
            setattr(self.__class__, name, voption(opt))
        super().__init__()

    gop_size = option("g", min_value_filter(0), doc="GOP size (default: 12)")
    keyint_min = option("keyint_min", type_filter(int), doc="Set minimum interval between IDR-frames.")
    refs = option("refs", type_filter(int), doc="Reference frames to consider for motion compensation")
    brd_scale = option("brd_scale", in_range_filter(0, 3), doc="Downscale frames for dynamic B-frame decision.")
    chroma_offset = option("chromaoffset", type_filter(int), doc="Set chroma qp offset from luma.")
    mv0_threshold = option("mv0_threshold", min_value_filter(0))
    b_sensitivity = option("b_sensitivity", min_value_filter(1), doc="Adjust sensitivity of b_frame_strategy 1.")
    timecode_frame_start = option(
        "timecode_frame_start",
        min_value_filter(-1),
        doc="GOP timecode frame start number, in non-drop-frame format"
    )
