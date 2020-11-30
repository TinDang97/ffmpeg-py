from ..util.constant import ConstantClass


__all__ = [
    'FFlags', 'FFlagsMuxer', 'FFlagsDemuxer'
]


class FFlagsMuxer(ConstantClass):
    flush_packets = "flush_packets"
    latm = "latm"
    bitexact = "bitexact"
    shortest = "shortest"
    autobsf = "autobsf"


class FFlagsDemuxer(ConstantClass):
    ignidx = "ignidx"
    genpts = "genpts"
    nofillin = "nofillin"
    noparse = "noparse"
    discardcorrupt = "discardcorrupt"
    sortdts = "sortdts"
    keepside = "keepside"
    fastseek = "fastseek"
    nobuffer = "nobuffer"


class FFlags(FFlagsMuxer, FFlagsDemuxer):
    pass
