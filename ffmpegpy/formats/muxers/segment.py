from ..format import Muxer
from ...util.pyopt import option, in_list_filter, type_filter, min_value_filter
from ..format import FormatMuxer

__all__ = [
    'Segment'
]


class Segment(Muxer):
    format = option(
        Muxer.format,
        in_list_filter([FormatMuxer.SEGMENT]),
        FormatMuxer.SEGMENT
    )
    segment_time = option("segment_time", min_value_filter(0))
    segment_format_options = option("segment_format_options", type_filter(str))
    segment_format = option("segment_format", in_list_filter(FormatMuxer.MP4))
    strftime = option("strftime", in_list_filter([1, 0, '1', '0']))
    reset_timestamps = option("reset_timestamps", in_list_filter((1, 0)))
    segment_atclocktime = option("segment_atclocktime", in_list_filter((1, 0)))
