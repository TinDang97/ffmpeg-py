import json
import re
import sys

from libffmpeg.codec import Codec, PixelFormat, CodecName, EncodeVideo, DecodeVideo, NVDEC, NVDECLIB, DecodeVideoLIB
from libffmpeg.format import Muxer, V4L2Demuxer, Demuxer
from libffmpeg.hwaccel import HWAccel, HWAccelType
from util import get_attr_values, check_type_instance, convert_kwargs_to_cmd_line_args
from util.io import Subprocess
from util.options import Options, option, value_in_list, is_not_params, check_in_range, check_min_value, check_type, \
    InterruptedSetOption

__all__ = ["FFmpeg", "FFprobe", "InputStream", "OutputStream", "PIPE_LINE", "FPS_DEFAULT"]

LINUX_DEVICE = "/dev/video"
PIPE_LINE = 'pipe:'
FFMPEG_CMD = "ffmpeg"
FFPROBE_CMD = "ffprobe"
SUBPROCESS_PIPE = Subprocess.PIPE

FPS_DEFAULT = 15
regex_time_fmt = re.compile(r"(\d{1,2})[:](\d{1,2})[:](\d{1,2})")


class RTSPTransport:
    TCP = "tcp"
    UDP = "udp"


class LogLevel:
    INFO = "info"
    ERROR = "error"
    QUIET = "quiet"


class VSync:
    PASSTHROUGH = 'passthrough'
    CRF = 'cfr'
    VFR = 'vfr'
    DROP = 'drop'
    AUTO = 'auto'


class InputOptionsBase(Options):
    def __init__(self, options=None):
        super().__init__(options)
        # Default setting
        self.hide_banner = None
        self.loglevel = LogLevel.ERROR

    probesize = option('probesize', check_in_range(32, 5000000))
    analyzeduration = option('analyzeduration', check_in_range(0, 5000000))
    rtsp_transport = option("rtsp_transport", value_in_list(get_attr_values(RTSPTransport)))
    hide_banner = option("hide_banner", is_not_params)
    loglevel = option("loglevel", value_in_list(get_attr_values(LogLevel)))


class ProbeOptions(InputOptionsBase):
    def __init__(self, options=None):
        super().__init__(options)

    def build(self):
        return convert_kwargs_to_cmd_line_args(self.dict())


class ProbeInfo(Options):
    @property
    def size(self):
        return self.height, self.width

    height = option("height", lambda _value: int(_value))
    width = option("width", lambda _value: int(_value))
    r_frame_rate = option("r_frame_rate", lambda _value: float(eval(_value)))
    codec_name = option("codec_name", value_in_list(get_attr_values(CodecName)))
    pix_fmt = option("pix_fmt", value_in_list(get_attr_values(PixelFormat)))
    tag = option("tag")
    others = option("others")


class FFprobe(ProbeOptions):
    def __init__(self, src):
        super().__init__()
        self.path = src

        if type(self.path) == int:
            self.path = f"/dev/video{self.path}"
        elif self.path.startswith("rtsp"):
            self.rtsp_transport = RTSPTransport.TCP

        self.__probe_info = None

    @property
    def source(self):
        return self.path

    def build(self):
        cmd = [FFPROBE_CMD]
        cmd += super().build()
        cmd += ['-show_format', '-show_streams', '-of', 'json']
        cmd.append(self.path)
        return cmd

    def _fetch_info(self) -> ProbeInfo:
        # TODO: work with audio stream.

        probe = Subprocess(self.build(), stdout=SUBPROCESS_PIPE, stderr=Subprocess.PIPE)
        out, err = probe.communicate()
        if probe.returncode != 0:
            raise RuntimeError(f'FFprobe error {probe.returncode}:', out, err)

        info = json.loads(out.decode('utf-8'))

        try:
            info = next(stream for stream in info['streams'] if stream['codec_type'] == "video")
        except StopIteration:
            raise RuntimeError("No video stream from source!")

        probe_info = ProbeInfo()

        for k, v in info.copy().items():
            if probe_info.__contains__(k):
                probe_info.__setattr__(k, v)
                info.__delitem__(k)

        probe_info.others = info
        return probe_info

    def refresh(self):
        self.__probe_info = self._fetch_info()
        return self.__probe_info

    def read(self):
        return self.info

    @property
    def info(self) -> ProbeInfo:
        if not self.__probe_info:
            self.refresh()
        return self.__probe_info


class StreamOptions(Options):
    @staticmethod
    def convert_time(times):
        if isinstance(times, str):
            if len(times) > 8:
                raise ValueError("Time format: %H:%M:%s. Ex: 09:35:12")

            times = regex_time_fmt.search(times)
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

    an = option("an", is_not_params)
    dn = option("dn", is_not_params)
    sn = option("sn", is_not_params)
    vn = option("vn", is_not_params)
    fflags = option("fflags", value_in_list(('nobuffer',)))
    re = option('re', is_not_params)
    vsync = option('vsync', value_in_list((0, 1, 2, -1, *get_attr_values(VSync))))
    seek = option("ss", convert_time)
    to = option("to", convert_time)
    duration = option("t", check_min_value(0))


class InputOptions(InputOptionsBase, StreamOptions):
    @staticmethod
    def format_video_size(size):
        check_type_instance(size, tuple)
        width, height = size
        return f"{width}x{height}"

    video_size = option('video_size', format_video_size)
    frame_rate = option('r', check_min_value(0))


class OutputOptions(StreamOptions):
    @staticmethod
    def __convert_overwrite(overwrite):
        if isinstance(overwrite, bool) and not overwrite:
            raise InterruptedSetOption
        return overwrite

    video_fmt = option("vf", check_type(str))
    frame_rate = option("r", check_type(float))
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
        for k, v in self.dict().items():
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

    @staticmethod
    def filter_codec(codec):
        if not isinstance(codec, Codec):
            raise TypeError(f"Must be Codec.")
        return codec

    @staticmethod
    def filter_muxer(muxer):
        if not isinstance(muxer, (str, Muxer)):
            raise TypeError(f"Must be string or Muxer.")

        if type(muxer) is str:
            return Muxer(muxer)
        else:
            return muxer

    codec = option("codec", filter_codec)
    muxer = option("muxer", filter_muxer)


class InputStream(Stream, InputOptions, HWAccel):
    def __init__(self, path, codec=None, demuxer=None):
        if codec is None:
            codec = DecodeVideo()

        if demuxer is None:
            demuxer = Demuxer()

        super().__init__(codec, demuxer)
        self.path = path

    def filter_decoder(self, decoder):
        if not isinstance(decoder, (DecodeVideo, str)):
            raise TypeError(f"Must be string or DecodeVideo.")

        if isinstance(decoder, str):
            old_codec = decoder
            if decoder in get_attr_values(NVDECLIB):
                decoder = NVDEC()
            elif decoder in get_attr_values(DecodeVideoLIB):
                decoder = DecodeVideo()
            else:
                raise ValueError(f"Value must in {[*get_attr_values(NVDECLIB), *get_attr_values(DecodeVideoLIB)]}")

            decoder.codeclib = old_codec
            self.hwaccel_device = HWAccelType.CUDA
            self.an = None
        elif self.is_existed(InputStream.hwaccel_device):
            del self.hwaccel_device
        return decoder

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
                self.muxer = V4L2Demuxer()

            if self.is_existed(InputStream.codec):
                del self.codec

        if path.startswith("rtsp"):
            self.rtsp_transport = RTSPTransport.TCP
        elif self.is_existed(InputStream.rtsp_transport):
            del self.rtsp_transport

        self.__path = path

    codec = option("c:v", filter_decoder)


class OutputStream(Stream, OutputOptions):
    def __init__(self, path=None, codec=None, muxer=None):
        if not codec:
            codec = EncodeVideo()

        if not muxer:
            muxer = Muxer()
        super().__init__(codec, muxer)
        self.path = path

    def set_codec(self, codec):
        check_type_instance(codec, (EncodeVideo, str))
        super(OutputStream, self).codec = codec

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


class FFmpeg(object):
    """
    FFmpeg command builder

    Parameters
    ----------
    input_stream: InputStream
        Input stream setup

    Attributes
    ----------
    input_stream: InputStream
        Input stream setup

    output_streams: list[OutputStream]

    """

    @property
    def output_stream(self):
        if self.output_streams.__len__() < 1:
            return
        return self.output_streams[0]

    @property
    def source(self):
        return self.input_stream.path

    @source.setter
    def source(self, path):
        self.input_stream.path = path

    def build(self):
        cmd = [FFMPEG_CMD]
        cmd += self.input_stream.build()
        for output_stream in self.output_streams:
            cmd += output_stream.build()
        return cmd

    def add_output(self, output_stream):
        check_type_instance(output_stream, OutputStream)

        for output in self.output_streams:
            if output_stream.path == output.path:
                raise ValueError("Stream existed!")

        self.output_streams.append(output_stream)

    def run(self):
        if self.output_streams.__len__() <= 0:
            raise RuntimeError("Not found any output stream.")

        stdout = None
        args = self.build()

        for output_stream in self.output_streams:
            if output_stream.path == PIPE_LINE:
                stdout = SUBPROCESS_PIPE

        stdin = SUBPROCESS_PIPE
        return Subprocess(args, stdout=stdout, stdin=stdin)

    def __init__(self, input_stream, *output_streams):
        if not isinstance(input_stream, InputStream):
            raise TypeError(f"Required input_stream's type is `InputStream`.")

        self.input_stream = input_stream
        self.output_streams = []
        if output_streams:
            for output_stream in output_streams:
                self.add_output(output_stream)

    def __repr__(self):
        _str = f"{self.__class__.__name__}"
        _str += f"\n{self.input_stream.__repr__()}"
        for output_stream in self.output_streams:
            _str += f"\n{output_stream.__repr__()}"
        return _str
