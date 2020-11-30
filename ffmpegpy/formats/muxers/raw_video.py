from ..format import Muxer, FormatMuxer
from ...util.pyopt import option, in_list_filter


class RawVideo(Muxer):
    format = option(
        Muxer.format,
        set_filter=in_list_filter(FormatMuxer.RAW_VIDEO,),
        default_value=FormatMuxer.RAW_VIDEO,
        doc="Raw video muxer"
    )
