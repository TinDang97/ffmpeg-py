from typing import Union

from ffmpegpy.value.params import Params, ParamsType
from ffmpegpy.util.constant import ConstantClass
from ffmpegpy.util.pyopt import option, in_list_filter, in_range_filter, type_filter

from .vcodec import VideoCodec, VideoEncoding

__all__ = [
    'Profile', 'Preset', 'Tune', 'NalHRD',
    'LibX264', 'LibX265',
    'LibX', 'LibXCodec'
]


def set_opt(opt: Union[Params, ParamsType, str, None]) -> Params:
    if isinstance(opt, Params):
        return opt
    return Params(opt)


class Profile(ConstantClass):
    H264_BASELINE = "baseline"
    H264_MAIN = "main"
    H264_HIGH = "high"
    H264_HIGH10 = "high10"
    H264_HIGH422 = "high422"
    H264_HIGH444 = "high444"

    HEVC_MAIN = "main"
    HEVC_MAIN10 = "main10"
    HEVC_MAIN12 = "main12"


class Preset(ConstantClass):
    """
    Preset of VideoLAN library like x264 (AVC) and x265 (HEVC)
    """
    PLACEBO = 'placebo'
    VERY_SLOW = 'slower'
    SLOWER = 'slower'
    SLOW = 'slow'
    MEDIUM = 'medium'
    FAST = 'fast'
    FASTER = 'faster'
    VERY_FAST = 'veryfast'
    ULTRA_FAST = 'ultrafast'


class Tune(ConstantClass):
    H264_STILLIMAGE = 'stillimage'
    H264_FILM = 'film'

    FASTDECODE = 'fastdecode'
    PSNR = 'psnr'
    SSIM = 'ssim'
    GRAIN = 'grain'
    ZEROLATENCY = 'zerolatency'
    ANIMATION = 'animation'


LEVEL = [
    # @Note(tindang97-ai): https://en.wikipedia.org/wiki/Advanced_Video_Coding#Levels to update
    "1", "1b", "1.1", "1.2", "1.3",
    "2", "2.1", "2.2",
    "3", "3.1", "3.2",
    "4", "4.1", "4.2",
    "5", "5.1", "5.2",
    "6", "6.1", "6.2"
]


class NalHRD(ConstantClass):
    NONE = None
    VBR = "vbr"
    CBR = "cbr"


class LibXCodec(VideoCodec):
    AVC = "libx264"
    HEVC = "libx265"


class LibX(VideoEncoding):
    """
    LibX of VideoLan. Only using for encoding video.
    CMD: ffmpegpy -hide_banner -h encoder=libx264

    Supported pixel formats: yuv420p yuvj420p yuv422p yuvj422p yuv444p yuvj444p nv12 nv16 nv21 yuv420p10le yuv422p10le
                             yuv444p10le nv20le gray gray10le
    """

    codec = option(
        VideoEncoding.codec,
        in_list_filter(LibXCodec)
    )

    preset = option(
        "preset",
        in_list_filter(Preset),
        doc="Use a preset to select encoding settings (default: medium)"
    )

    tune = option(
        "tune", in_list_filter(Tune),
        doc="Tune the settings for a particular type of source or situation"
    )

    profile = option(
        VideoEncoding.profile,
        in_list_filter(Profile),
        doc="Force the limits of an H.264 profile"
    )

    level = option(
        VideoEncoding.level,
        in_list_filter(LEVEL),
        doc="Specify level (as defined by Annex A)"
    )

    crf = option(
        "crf",
        in_range_filter(0, 51),
        doc="Constant Rate Factor. Select the quality for constant quality mode (0 (lossless) -> 51) (default 23)"
    )

    crf_max = option(
        "crf_max",
        in_range_filter(0, 51),
        doc="In CRF mode, prevents VBV from lowering quality beyond this point. "
            "(from 0 to 51) (default -1: not set)"
    )

    quantization_parameter = option("qp", doc="Constant quantization parameter rate control method")
    quantizer_min = option("qmin", doc="Minimum quantizer scale.")
    quantizer_max = option("qmax", doc="Maximum quantizer scale.")
    quantizer_diff = option("qdiff", doc="Maximum difference between quantizer scales.")
    quantizer_blur = option("qblur", doc="Quantizer curve blur")
    quantizer_compression = option("qcomp", doc="Quantizer curve compression factor")
    refs = option("refs", in_range_filter(1, 16))
    rc_lookahead = option("rc-lookahead", type_filter(int))


class LibX264(LibX):
    codec = option(
        LibX.codec,
        in_list_filter(LibXCodec.AVC,),
        LibXCodec.AVC
    )

    x264opts = option(
        "x264opts",
        set_filter=set_opt,
        default_value=Params(),
        doc="Set any x264 option. see x264 --fullhelp"
    )

    nal_hrd = option(
        "nal-hrd",
        in_list_filter(NalHRD),
        doc="Set signal HRD information (requires vbv-bufsize to be set)"
    )


class LibX265(LibX):
    codec = option(
        LibX.codec,
        in_list_filter(LibXCodec.HEVC,),
        LibXCodec.HEVC
    )

    x265_params = option(
        "x265-params",
        set_filter=set_opt,
        default_value=Params(),
        doc="Set x265 options. See x265 --help for a list of options."
    )
