from ..format import Muxer
from ...util.pyopt import option, in_list_filter, type_filter, min_value_filter
from ..format import FormatMuxer

__all__ = [
    'H264'
]


class H264(Muxer, Demuxer):
    format = option(
        Boxer.format,
        in_list_filter(Format.H264, ),
        Format.H264
    )
