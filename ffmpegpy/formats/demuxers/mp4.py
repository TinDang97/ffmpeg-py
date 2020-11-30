from ..format import Demuxer, FormatDemuxer
from ...util.pyopt import option, in_list_filter


class MP4Demuxer(Demuxer):
    format = option(
        Demuxer.format,
        in_list_filter(FormatDemuxer.MP4,),
        FormatDemuxer.MP4,
        doc='MP4 demuxer'
    )
