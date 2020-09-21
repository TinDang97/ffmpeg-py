import subprocess

from util.options import Options, option, value_in_list, check_min_value, check_type, InterruptedSetOption
from util import get_attr_values
import re


def get_formats():
    re_spaces = re.compile(r"\s+")
    formats_raw = subprocess.getoutput("ffmpeg -loglevel quiet -formats").strip().split("\n")[4:]
    formats = []
    for fmt in formats_raw:
        formats.append(re_spaces.sub(" ", fmt).strip().split(" ")[1])
    return sorted(formats)


def find_formats(format_regex):
    formats = get_formats()
    return [fmt for fmt in formats if format_regex in fmt]


class FormatDevices:
    # Linux
    V4L2 = 'v4l2'

    # Windows
    DSHOW = "dshow"

    # OSX
    AVFOUNDATION = "avfoundation"


class FormatType:
    RAW = 'rawvideo'
    MP4 = 'mp4'
    SEGMENT = 'segment'
    MPEGTS = 'mpegts'
    H264 = 'h264'
    H265 = 'hevc'
    MOV = 'mov'


class FormatDemux(FormatDevices, FormatType):
    pass


class MOVFlags:
    FRAG_KEYFRAME = "frag_keyframe"
    EMPTY_MOOV = "empty_moov"
    SEPARATE_MOOF = "separate_moof"
    SKIP_SIDX = "skip_sidx"
    FASTSTART = "faststart"
    RTPHINT = "rtphint"
    DISABLE_CHPL = "disable_chpl"
    OMIT_TFHD_OFFSET = "omit_tfhd_offset"
    DEFAULT_BASE_MOOF = "default_base_moof"
    NEGATIVE_CTS_OFFSETS = "negative_cts_offsets"


class Muxer(Options):
    def __init__(self, _format=None):
        super().__init__()

        if not _format:
            return

        if not isinstance(_format, (str, Muxer)):
            raise ValueError("Must be Muxer or string.")

        if isinstance(_format, str):
            self.format = _format
        else:
            self.from_options(_format)

    format = option("f", value_in_list(get_attr_values(FormatType)))


class Demuxer(Muxer):
    format = option("f", value_in_list(get_attr_values(FormatDemux)))


class MP4Demuxer(Demuxer):
    def __init__(self):
        super().__init__(FormatType.MP4)


class MP4Muxer(Muxer):
    def add_movflags(self, flags):
        movflags_name = MP4Muxer.movflags.name

        if not flags:
            return

        if isinstance(flags, str):
            flags = flags.split("+")

        if self.is_existed(movflags_name):
            new_movflags = self.get(MP4Muxer.movflags.name)
            lst_movflags = self.get(MP4Muxer.movflags.name).split("+")
        else:
            new_movflags = ""
            lst_movflags = []

        for flag in flags:
            if not flag or flag in lst_movflags:
                continue
            if flag not in MP4Muxer.__flags_base:
                raise ValueError(f"Flag must in {MP4Muxer.__flags_base}. Got \"{flag}\"")
            new_movflags += f"+{flag}"

        self.set(MP4Muxer.movflags.name,  new_movflags)

    @staticmethod
    def __filter_movflags(flags):
        if not isinstance(flags, (list, str)):
            raise ValueError(f"Value's type must be {(list, str)}. But got \"{type(flags)}\"")

        if not flags:
            raise InterruptedSetOption

        if isinstance(flags, str):
            flags = flags.split("+")

        flags_options = ""
        for flag in flags:
            if not flag:
                continue
            if flag not in MP4Muxer.__flags_base:
                raise ValueError(f"Flag must in {MP4Muxer.__flags_base}. Got \"{flag}\"")
            flags_options += f"+{flag}"

        if not flags_options:
            raise InterruptedSetOption
        return flags_options

    def __init__(self):
        super().__init__(FormatType.MP4)

    __flags_base = get_attr_values(MOVFlags)
    movflags = option("movflags", __filter_movflags)
    moov_size = option("moov_size", check_min_value(0))
    frag_duration = option("frag_duration", check_min_value(0))
    frag_size = option("frag_size", check_min_value(0))
    min_frag_duration = option("min_frag_duration", check_min_value(0))
    write_tmcd = option("write_tmcd")
    write_prft = option("write_prft")


class SegmentMuxer(Muxer):
    def __init__(self):
        super().__init__(FormatType.SEGMENT)

    segment_time = option("segment_time", check_min_value(0))
    segment_format_options = option("segment_format_options", check_type(str))
    segment_format = option("segment_format", value_in_list(FormatType.MP4))
    strftime = option("strftime", value_in_list([1, 0, '1', '0']))
    reset_timestamps = option("reset_timestamps", check_type(type(None)))


class MOV(MP4Muxer):
    def __init__(self):
        super().__init__()
        self.format = FormatType.MOV


class MpegTSMuxer(MP4Muxer):
    pass


class H264Muxer(Muxer):
    def __init__(self):
        super().__init__(FormatType.H264)


class H265Muxer(Muxer):
    def __init__(self):
        super().__init__(FormatType.H265)


class V4L2Demuxer(Demuxer):
    def __init__(self):
        super().__init__(FormatDemux.V4L2)


class RawMuxer(Muxer):
    def __init__(self):
        super().__init__(FormatType.RAW)


class RawDemuxer(Demuxer):
    def __init__(self):
        super().__init__(FormatDemux.RAW)
