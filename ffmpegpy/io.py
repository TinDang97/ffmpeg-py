import re
import sys

from .util import check_type, convert_kwargs_to_cmd_line_args
from .util.pyopt import Options, option, in_list_filter, is_not_params_filter, \
    min_value_filter, type_filter, InterruptedSetOption
from util.constant import ConstantClass

from .codecs import Codec, EncodeVideo, DecodeVideo
from library.ffmpeg.formats.format import Muxer, V4L2, Demuxer
from .hwaccel import HWAccel, HWAccelType

REGEX_TIME_FMT = re.compile(r"(\d{1,2})[:](\d{1,2})[:](\d{1,2})")
LINUX_DEVICE = "/dev/video"


__all__ = [
    'PixelFormat', 'RTSPTransport', 'LogLevel', 'VSync',
    'InputStream', 'OutputStream', 'InputOptionsBase'
]


class RTSPTransport(ConstantClass):
    TCP = "tcp"
    UDP = "udp"


class LogLevel(ConstantClass):
    INFO = "info"
    ERROR = "error"
    QUIET = "quiet"


class VSync(ConstantClass):
    PASSTHROUGH = 'passthrough'
    CRF = 'cfr'
    VFR = 'vfr'
    DROP = 'drop'
    AUTO = 'auto'


class InputOptionsBase(Options):
    rtsp_transport = option("rtsp_transport", in_list_filter(RTSPTransport))


class StreamOptions(Options):
    @staticmethod
    def convert_time(times):
        if isinstance(times, str):
            if len(times) > 8:
                raise ValueError("Time format: %H:%M:%s. Ex: 09:35:12")

            times = REGEX_TIME_FMT.search(times)
            if not bool(times):
                raise ValueError("Time format: %H:%M:%s. Ex: 09:35:12")
            hours, minutes, seconds = times.groups()
        else:
            hours, minutes, seconds = times

        hours = int(hours)
        if hours > 23:
            raise ValueError(f"Hour must in 24-hour military time. Got {hours}")

        minutes = int(minutes)
        if minutes > 60:
            raise ValueError(f"Minute must be standard. Got {minutes}")

        seconds = int(seconds)
        if seconds > 60:
            raise ValueError(f"Seconds must be standard. Got {seconds}")

        return f"{hours:02}:{minutes:02}:{seconds:02}"

    an = option("an", is_not_params_filter)
    dn = option("dn", is_not_params_filter)
    sn = option("sn", is_not_params_filter)
    vn = option("vn", is_not_params_filter)
    re = option('re', is_not_params_filter)
    video_sync = option('vsync', in_list_filter(VSync))
    audio_sync = option('async', min_value_filter(1))
    seek = option("ss", convert_time)
    to = option("to", convert_time)
    duration = option("t", min_value_filter(0))
    pix_fmt = option("pix_fmt", in_list_filter(PixelFormat))


class InputOptions(InputOptionsBase, StreamOptions):
    @staticmethod
    def format_video_size(size):
        check_type(size, tuple)
        width, height = size
        return f"{width}x{height}"

    video_size = option('video_size', format_video_size)
    frame_rate = option('r', min_value_filter(0))


class OutputOptions(StreamOptions):
    @staticmethod
    def __convert_overwrite(overwrite):
        if isinstance(overwrite, bool) and not overwrite:
            raise InterruptedSetOption
        return overwrite

    @staticmethod
    def __video_filter(_filter: str):
        check_type(_filter, str)
        if _filter.endswith(","):
            _filter = _filter[:-1]
        return _filter

    def add_video_filter(self, _filter):
        check_type(_filter, str)

        if self.is_set(OutputOptions.video_filter):
            self.video_filter += f",{_filter}"
        else:
            self.video_filter = _filter

    video_filter = option("vf", type_filter(str))
    audio_filter = option("af", type_filter(str))
    frame_rate = option("r", type_filter((float, int)))
    overwrite = option("y", __convert_overwrite)


class Stream(Options):
    def __init__(self, codec=None, muxer=None):
        super().__init__()
        if codec is None:
            self.codec = Codec()
        else:
            self.codec = codec

        if muxer is None:
            self.muxer = Muxer()
        else:
            self.muxer = muxer

        self.__path = None

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, path):
        self.__path = path

    def __repr__(self):
        _str = ""
        for k, v in self.build().items():
            _str += f"\n\t\"{k}\": "

            if isinstance(v, Options):
                _str += f"{v.__class__.__name__}"
                if v:
                    _str += f"({v.__str__()})"
                else:
                    _str += "(None)"
            else:
                _str += f"{v}"
        if not _str:
            _str = "None"
        return f"{self.__class__.__name__}: \"{self.path}\"{_str}\n"

    def build(self):
        args = []
        options = self.dict()
        for k in sorted(options):
            v = options[k]
            if isinstance(v, Options):
                v = convert_kwargs_to_cmd_line_args(v.dict())
                args.extend(v)
            else:
                args.append(f'-{k}')
                if v is not None:
                    args.append(f'{v}')
        return args

    codec = option("codecs", type_filter(Codec))
    muxer = option("muxers", type_filter(Muxer))


class InputStream(Stream, InputOptions, HWAccel):
    def __init__(self, path, codec=None, demuxer=None):
        if codec is None:
            codec = DecodeVideo()

        if demuxer is None:
            demuxer = Demuxer()

        super().__init__(codec, demuxer)
        self.path = path

    def build(self):
        cmd = super().build()
        cmd.append("-i")
        cmd.append(self.path)
        return cmd

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, path):
        if isinstance(path, int) and sys.platform == "linux":
            path = f"{LINUX_DEVICE}{path}"

            if path.startswith(LINUX_DEVICE):
                self.muxer = V4L2()

            if self.is_existed(InputStream.codec):
                del self.codec
        elif isinstance(self.muxer, V4L2):
            self.muxer = Demuxer()

        if path.startswith("rtsp"):
            self.rtsp_transport = RTSPTransport.TCP
        elif self.is_existed(InputStream.rtsp_transport):
            del self.rtsp_transport

        self.__path = path

    def filter_decoder(self, decoder):
        if not isinstance(decoder, (DecodeVideo, str)):
            raise TypeError(f"Must be string or DecodeVideo.")

        if isinstance(decoder, str):
            decoder = get_decoder(decoder)
            self.hwaccel_device = HWAccelType.CUDA
            self.an = None
        elif self.is_existed(InputStream.hwaccel_device):
            del self.hwaccel_device
        return decoder

    @staticmethod
    def filter_demuxer(demuxer):
        if not isinstance(demuxer, (str, Demuxer)):
            raise TypeError(f"Must be string or Demuxer.")

        if isinstance(demuxer, str):
            demuxer = get_demuxer(demuxer)
        return demuxer

    codec = option(Stream.codec.name, filter_decoder)
    muxer = option(Stream.muxer.name, filter_demuxer)


class OutputStream(Stream, OutputOptions):
    def __init__(self, path=None, codec=None, muxer=None):
        if not codec:
            codec = EncodeVideo()

        if not muxer:
            muxer = Muxer()

        super().__init__(codec, muxer)
        self.path = path

    # self.maps = []
    # def multi_output(self, outputs):
    #     for output in outputs:
    # TODO: support multi IO stream. https://trac.ffmpeg.org/wiki/Creating%20multiple%20outputs
    # def map(self, stream, output):
    #     self.maps.append((stream, output))

    def build(self):
        cmd = super().build()
        cmd.append(self.path)
        return cmd

    @staticmethod
    def filter_encoder(encoder):
        if not isinstance(encoder, (EncodeVideo, str)):
            raise TypeError(f"Must be string or EncodeVideo.")

        if isinstance(encoder, str):
            encoder = get_encoder(encoder)
        return encoder

    @staticmethod
    def filter_muxer(muxer):
        if not isinstance(muxer, (str, Muxer)):
            raise TypeError(f"Must be string or Muxer.")

        if isinstance(muxer, str):
            muxer = get_demuxer(muxer)
        return muxer

    codec = option(Stream.codec.name, filter_encoder)
    muxer = option(Stream.muxer.name, filter_muxer)
