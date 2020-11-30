from ffmpegpy.util.constant import ConstantClass
from ffmpegpy.util.pyopt import Options, option, \
    in_list_filter, min_value_filter, type_filter, in_range_filter
from .fflags import FFlagsDemuxer, FFlagsMuxer, FFlags

__all__ = [
    'Demuxer', 'Format', 'FormatMuxer', 'FormatDemuxer', 'RawH265',
    'Muxer', 'V4L2'
]


class FormatDevices(ConstantClass):
    # Linux
    V4L2 = 'v4l2'

    # Windows
    DSHOW = "dshow"

    # OSX
    AVFOUNDATION = "avfoundation"


class FormatCommon(ConstantClass):
    RAW_VIDEO = 'rawvideo'
    MP4 = 'mp4'
    SEGMENT = 'segment'
    MPEGTS = 'mpegts'
    H264 = 'h264'
    HEVC = 'hevc'
    MOV = 'mov'


class FormatDemuxer(FormatDevices, FormatCommon):
    pass


class FormatMuxer(FormatDevices, FormatCommon):
    pass


class Format(FormatMuxer, FormatDemuxer):
    pass


class Boxer(Options):
    format = option("f", in_list_filter(FormatMuxer), doc='Muxer/demuxer base')
    fflags = option("fflags", in_list_filter(FFlags))


class Demuxer(Boxer):
    format = option(Boxer.format, in_list_filter(FormatDemuxer), doc="Demuxer base")
    probesize = option('probesize', in_range_filter(32, 5000000))
    analyzeduration = option('analyzeduration', in_range_filter(0, 5000000))
    fflags = option("fflags", in_list_filter(FFlagsDemuxer))


class Muxer(Boxer):
    format = option(Boxer.format, in_list_filter(FormatMuxer), doc='Muxer base')
    fflags = option("fflags", in_list_filter(FFlagsMuxer))


class V4L2(Muxer, Demuxer):
    format = option(
        Boxer.format,
        in_list_filter(Format.V4L2,),
        Format.V4L2
    )

