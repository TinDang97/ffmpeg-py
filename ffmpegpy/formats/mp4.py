from ffmpegpy.util.constant import ConstantClass
from ffmpegpy.util.pyopt import option, in_list_filter, min_value_filter
from ffmpegpy.value.flags import Flags
from ffmpegpy.util import set_flags
from .format import Muxer, FormatMuxer, Demuxer, FormatDemuxer

__all__ = [
    'MOVFlags', 'MP4', 'MP4Demuxer'
]


class MOVFlags(ConstantClass):
    """
    ffmpegpy -hide_banner -h full > movflags
    """
    RTPHINT = "rtphint"
    empty_moov = "empty_moov"
    FRAG_KEYFRAME = "frag_keyframe"
    FRAG_EVERY_FRAME = "frag_every_frame"
    SEPARATE_MOOF = "separate_moof"
    ISML = "isml"
    FASTSTART = "faststart"
    OMIT_TFHD_OFFSET = "omit_tfhd_offset"
    DISABLE_CHPL = "disable_chpl"
    DASH = "dash"
    CMAF = "cmaf"
    FRAG_DISCONT = "frag_discont"
    DELAY_MOOV = "delay_moov"
    GLOBAL_SIDX = "global_sidx"
    SKIP_SIDX = "skip_sidx"
    WRITE_COLR = "write_colr"
    PREFER_ICC = "prefer_icc"
    WRITE_GAMA = "write_gama"
    USE_METADATA_TAGS = "use_metadata_tags"
    SKIP_TRAILER = "skip_trailer"
    NEGATIVE_CTS_OFFSETS = "negative_cts_offsets"


class MP4Demuxer(Demuxer):
    format = option(
        Demuxer.format,
        in_list_filter(FormatDemuxer.MP4,),
        FormatDemuxer.MP4,
        doc='MP4 demuxer'
    )


class MP4(Muxer):
    format = option(
        Muxer.format,
        in_list_filter([FormatMuxer.MOV, FormatMuxer.MP4, FormatMuxer.MPEGTS]),
        FormatMuxer.MP4,
        doc='MP4 muxers'
    )
    movflags = option("movflags", set_flags(MOVFlags), Flags(limit_list=MOVFlags), doc="MOV muxers flags")
    moov_size = option("moov_size", min_value_filter(0))
    frag_duration = option("frag_duration", min_value_filter(0))
    frag_size = option("frag_size", min_value_filter(0))
    min_frag_duration = option("min_frag_duration", min_value_filter(0))
    write_tmcd = option("write_tmcd")
    write_prft = option("write_prft")
