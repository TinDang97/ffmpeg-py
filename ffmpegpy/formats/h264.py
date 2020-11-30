from .format import Muxer, Demuxer, FormatMuxer, FormatDemuxer
from ffmpegpy.util.pyopt import option, in_list_filter

__all__ = [
    'H264', 'H264Demuxer'
]


class H264Demuxer(Demuxer):
    format = option(
        Demuxer.format,
        in_list_filter(FormatDemuxer.H264, ),
        FormatMuxer.H264
    )


class H264(Muxer):
    format = option(
        Muxer.format,
        in_list_filter(FormatMuxer.H264, ),
        FormatMuxer.H264
    )
