from .format import Muxer, Demuxer, FormatMuxer, FormatDemuxer
from ffmpegpy.util.pyopt import option, in_list_filter


__all__ = [
    'HEVC', 'HEVCDemuxer'
]


class HEVCDemuxer(Demuxer):
    format = option(
        Demuxer.format,
        in_list_filter(FormatDemuxer.HEVC, ),
        FormatMuxer.HEVC
    )


class HEVC(Muxer):
    format = option(
        Muxer.format,
        in_list_filter(FormatMuxer.HEVC, ),
        FormatMuxer.HEVC
    )
