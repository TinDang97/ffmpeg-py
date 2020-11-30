from ..util.pyopt import Options, option, readonly_option, type_filter, in_list_filter, min_value_filter
from ..util.constant import ConstantClass
from ..value.flags import Flags
from ..util import set_flags

__all__ = [
    "Codec", "Decoding", "Encoding",
    "GenericFlags", "GenericFlags2",
    "Strict", "MotionEstimation", "ErrDetectFlags"
]
"""
ffmpegpy -hide_banner -h encoder=$(codecs)
-> encoders: ffmpegpy -hide_banner -encoders
-> decoders: ffmpegpy -hide_banner -decoders
-> detail: ffmpegpy -hide_banner -h encoder={codec_name}
-> detail: ffmpegpy -hide_banner -h decoder={codec_name}
Ex: `ffmpegpy -hide_banner -h encoder=h264_nvenc`
"""


class Codec(ConstantClass):
    pass


class GenericFlags(ConstantClass):
    """
    See: https://ffmpeg.org/ffmpeg-codecs.html -> flags
    """
    MV4 = "mv4"
    QPEL = "qpel"
    LOOP = "loop"
    QSCALE = "qscale"
    PASS1 = "pass1"
    PASS2 = "pass2"
    GRAY = "gray"
    EMU_EDGE = "emu_edge"
    PSNR = "psnr"
    TRUNCATED = "truncated"
    DROP_CHANGED = "drop_changed"
    ILDCT = "ildct"
    LOW_DELAY = "low_delay"
    GLOBAL_HEADER = "global_header"
    BITEXACT = "bitexact"
    AIC = "aic"
    CBP = "cbp"
    QPRD = "qprd"
    ILME = "ilme"
    CGOP = "cgop"
    OUTPUT_CORRUPT = "output_corrupt"


class GenericFlags2(ConstantClass):
    """
    See: https://ffmpeg.org/ffmpeg-codecs.html -> flags2
    """
    FAST = "fast"
    NOOUT = "noout"
    IGNORECROP = "ignorecrop"
    LOCAL_HEADER = "local_header"
    CHUNKS = "chunks"
    SHOWALL = "showall"
    EXPORT_MVS = "export_mvs"
    SKIP_MANUAL = "skip_manual"
    ASS_RO_FLUSH_NOOP = "ass_ro_flush_noop"


class ErrDetectFlags(ConstantClass):
    """
    See: https://ffmpeg.org/ffmpeg-codecs.html -> err_detect
    """
    CRCCHECK = "crccheck"
    BITSTREAM = "bitstream"
    BUFFER = "buffer"
    EXPLODE = "explode"
    IGNORE_ERR = "ignore_err"
    CAREFUL = "careful"
    COMPLIANT = "compliant"
    AGGRESSIVE = "aggressive"


class MotionEstimation(ConstantClass):
    """
    See: https://ffmpeg.org/ffmpeg-codecs.html -> me_method
    """
    ZERO = "zero"
    FULL = "full"
    EPZS = "epzs"
    ESA = "esa"
    TESA = "tesa"
    DIA = "dia"
    LOG = "log"
    PHODS = "phods"
    X1 = "x1"
    HEX = "hex"
    UMH = "umh"
    ITER = "iter"


class Strict(ConstantClass):
    """
    https://ffmpeg.org/ffmpeg-codecs.html -> strict
    """
    VERY = "very"
    STRICT = "strict"
    NORMAL = "normal"
    UNOFFICIAL = "unofficial"
    EXPERIMENTAL = "experimental"


class Coding(Options):
    strict = option(
        "strict",
        in_list_filter([*Strict, *range(-2, 3)]),
        doc="Specify how strictly to follow the standards. (default normal)"
    )
    flags = option('flags', set_flags(GenericFlags), Flags(limit_list=GenericFlags), doc="Set generic flags.")
    flags2 = option('flags2', set_flags(GenericFlags2), Flags(limit_list=GenericFlags2), doc="Set generic flags2.")
    threads = option(
        'threads',
        min_value_filter(0),
        doc="Set the number of threads to be used. 0 == 'auto'"
    )


class Decoding(Coding):
    lowres = option("lowres", min_value_filter(0), doc="Decode at 1= 1/2, 2=1/4, 3=1/8 resolutions. Default: 0")
    err_detect = option(
        "err_detect",
        set_flags(ErrDetectFlags),
        Flags(limit_list=ErrDetectFlags),
        doc="Set error detection flags.")


class Encoding(Coding):
    @staticmethod
    def filter_bitrate(bitrate):
        if not isinstance(bitrate, (str, int)):
            raise TypeError("Value's type be int or str!")

        if isinstance(bitrate, str):
            try:
                bitrate = int(bitrate)
            except ValueError:
                if bitrate[-1] not in ['M', 'k']:
                    raise ValueError("Data type must be k (kbps) or M (Mbps)!")

                _type = bitrate[-1]

                try:
                    bitrate = int(bitrate[:-1])
                except ValueError:
                    raise ValueError("Wrong format. Value must like: '2000k' or '2M'") from None

                if _type == 'M':
                    bitrate *= 1024

        if bitrate <= 0:
            raise ValueError("Value must > 0")
        return f"{bitrate}k"

    codec = readonly_option("codecs", doc="Codec library.")
    bitrate = option("bitrate", filter_bitrate, doc="Average bitrate (default: 128k)")
    maxrate = option("maxrate", filter_bitrate, doc="Max bitrate. Require `bufsize` (recommend: maxrate * 2)")
    minrate = option("minrate", filter_bitrate, doc="Min bitrate")
    bufsize = option("bufsize", filter_bitrate, doc="Buffer size")
    profile = option("profile", type_filter(int), doc="Set encoder codecs profile.")
    level = option("level", type_filter(int))
    compression_level = option("compression_level", type_filter(int))

    me_method = option(
        'me_method',
        set_flags(MotionEstimation),
        Flags(limit_list=MotionEstimation),
        doc="Set motion estimation method.."
    )
