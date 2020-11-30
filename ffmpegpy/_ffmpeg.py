from util import get_attr_values, check_type, convert_kwargs_to_cmd_line_args
from util.io import Subprocess
from util.option import Options, option, in_list_filter, is_not_params_filter

from .io import InputStream, OutputStream, LogLevel, RTSPTransport, VSync

__all__ = [
    "FFmpeg", "InputStream", "OutputStream",
    "PIPE_LINE", "FPS_DEFAULT", "LogLevel", "RTSPTransport", "VSync"
]

LINUX_DEVICE = "/dev/video"
PIPE_LINE = 'pipe:'
FFMPEG_CMD = "ffmpegpy"
FPS_DEFAULT = 15


class FFmpeg(Options):
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

    output_streams: list of OutputStream
        Output stream setup
    """

    def __init__(self, input_stream, *output_streams):
        super().__init__()
        if not isinstance(input_stream, InputStream):
            raise TypeError(f"Required input_stream's type is `InputStream`.")

        self.input_stream = input_stream
        self.output_streams = []

        if output_streams:
            for output_stream in output_streams:
                self.add_output(output_stream)

        # Default setting
        self.hide_banner = None

    def __repr__(self):
        _str = f"{self.__class__.__name__}"
        _str += f"\n{self.input_stream!r}"
        for output_stream in self.output_streams:
            _str += f"\n{output_stream!r}"
        return _str

    @property
    def output_stream(self) -> OutputStream:
        if self.output_streams.__len__() < 1:
            raise ValueError("Output empty!")
        return self.output_streams[0]

    @property
    def source(self):
        return self.input_stream.path

    @source.setter
    def source(self, path):
        self.input_stream.path = path

    def build(self):
        cmd = [FFMPEG_CMD]
        cmd += convert_kwargs_to_cmd_line_args(self.dict())
        cmd += self.input_stream.build()
        for output_stream in self.output_streams:
            if hasattr(output_stream.codec, 'add_params'):
                output_stream.codec.add_params("log-level", self.loglevel)
            cmd += output_stream.build()
        return cmd

    def add_output(self, output_stream):
        check_type(output_stream, OutputStream)

        for output in self.output_streams:
            if output_stream.path == output.path:
                raise ValueError("Stream existed!")

        self.output_streams.append(output_stream)

    def run(self, stdin=None, stdout=None):
        """
        Create ffmpegpy subprocess with current settings
        call .build() to show current settings.
        """
        if self.output_streams.__len__() <= 0:
            raise RuntimeError("Not found any output stream.")

        args = self.build()

        for output_stream in self.output_streams:
            if output_stream.path == PIPE_LINE:
                stdout = Subprocess.PIPE if stdout is None else stdout

        stdin = Subprocess.PIPE if stdin is None else stdin
        return Subprocess(args, stdout=stdout, stdin=stdin)

    hide_banner = option("hide_banner", is_not_params_filter)
    loglevel = option("loglevel", in_list_filter(get_attr_values(LogLevel)))
