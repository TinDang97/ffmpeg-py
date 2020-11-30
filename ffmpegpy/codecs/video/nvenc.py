from ffmpegpy.util import number_of_gpus
from ffmpegpy.util.constant import ConstantClass
from ffmpegpy.util.pyopt import option, in_list_filter, max_value_filter, in_range_filter, type_filter

from .libx import LibX
from ..vcodec import VideoCodec

"""
ffmpegpy -hide_banner -h encoder=nvenc
"""


__all__ = [
    'NvencH264', 'NvencH265', 'Nvenc', 'NvencCodec',
    'Preset', 'RateControl',
    'ProfileAVC', 'ProfileH264', 'ProfileHEVC', 'ProfileH265',
]


class Preset(ConstantClass):
    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"
    HIGH_PERFORMANCE = "hp"
    HIGH_QUALITY = "hq"
    BLURAY_DISK = "bd"
    LOW_LATENCY = "ll"
    LOW_LATENCY_HIGH_QUALITY = "llhq"
    LOW_LATENCY_HIGH_PERFORMANCE = "llhp"
    LOSSLESS = "lossless"
    LOSSLESS_HIGH_PERFORMANCE = "losslesshp"


class ProfileHEVC(ConstantClass):
    MAIN = "main"
    MAIN_10 = "main10"
    REXT = "rext"


class ProfileH265(ProfileHEVC):
    """Alias of HEVC profile"""


class ProfileAVC(ConstantClass):
    BASELINE = "baseline"
    MAIN = "main"
    HIGH = "high"
    HIGH444P = "high444p"


class ProfileH264(ProfileAVC):
    """Alias of AVC profile"""


class RateControl(ConstantClass):
    CONSTQP = 'constqp'
    VBR = 'vbr'
    CBR = 'cbr'
    VBR_MINQP = 'vbr_minqp'
    LL_2PASS_QUALITY = 'll_2pass_quality'
    LL_2PASS_SIZE = 'll_2pass_size'
    CBR_LD_HQ = 'cbr_ld_hq'
    CBR_HIGH_QUALITY = 'cbr_hq'
    VBR_HIGH_QUALITY = 'vbr_hq'


class NvencCodec(VideoCodec):
    H264 = "nvenc_h264"
    H265 = "nvenc_h265"
    AVC = "nvenc_h264"
    HEVC = "nvenc_h265"


class Nvenc(LibX):
    codec = option(
        LibX.codec,
        set_filter=in_list_filter(NvencCodec)
    )

    rc = option(
        "rc",
        set_filter=in_list_filter(RateControl),
        doc="Override the preset rate-control (from -1 to INT_MAX) (default -1)"
    )

    preset = option(
        "preset",
        set_filter=in_list_filter(Preset),
        doc="Set the encoding level restriction."
    )

    gpu = option("gpu", max_value_filter(number_of_gpus()))
    constant_quality = option("cq", in_range_filter(0, 51))
    strict_gop = option("strict_gop", type_filter(bool))
    zerolatency = option("zerolatency", type_filter(bool))
    cbr = option("cbr", type_filter(bool))
    two_pass = option("2pass", type_filter(bool))


class NvencH264(Nvenc):
    codec = option(Nvenc.codec, in_list_filter(NvencCodec.H264,), NvencCodec.H264)
    profile = option(Nvenc.profile, in_list_filter(ProfileAVC))


class NvencH265(Nvenc):
    codec = option(Nvenc.codec, in_list_filter(NvencCodec.H265,), NvencCodec.H265)
    profile = option(Nvenc.profile, in_list_filter(ProfileHEVC))
