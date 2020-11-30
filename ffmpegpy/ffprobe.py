import json

from util import convert_kwargs_to_cmd_line_args
from util.io import Subprocess
from util.option import Options, option
from .io import InputOptionsBase, RTSPTransport

FFPROBE_CMD = "ffprobe"

__all__ = [
    "ProbeInfo", "FFprobe"
]


class ProbeOptions(InputOptionsBase):
    def __init__(self, options=None):
        super().__init__(options)

    def build(self):
        return convert_kwargs_to_cmd_line_args(super(ProbeOptions, self).build())


class ProbeInfo(Options):
    @property
    def size(self):
        return self.width, self.height

    height = option("height", lambda _value: int(_value))
    width = option("width", lambda _value: int(_value))
    r_frame_rate = option("r_frame_rate", lambda _value: float(eval(_value)))
    codec_name = option("codec_name")
    pix_fmt = option("pix_fmt")
    tag = option("tag")
    others = option("others")


class FFprobe(ProbeOptions):
    def __init__(self, src):
        super().__init__()
        self.path = src
        self.__probe_info = ProbeInfo()

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, src):
        if type(src) == int:
            src = f"/dev/video{src}"
        elif src.startswith("rtsp"):
            self.rtsp_transport = RTSPTransport.TCP
        self.__path = src

    @property
    def info(self) -> ProbeInfo:
        # read info unless any info.
        if not self.__probe_info:
            self.refresh()
        return self.__probe_info

    @info.setter
    def info(self, probe_info: ProbeInfo):
        if not isinstance(probe_info, ProbeInfo):
            raise TypeError("probe_info must be ProbeInfo")
        self.__probe_info.from_options(probe_info)

    def build(self):
        cmd = [FFPROBE_CMD]
        cmd += super().build()
        cmd += ['-show_format', '-show_streams', '-of', 'json']
        cmd.append(self.path)
        return cmd

    def refresh(self):
        self.__probe_info = self.__read(self.build())

    @staticmethod
    def __read(cmd) -> ProbeInfo:
        # TODO: work with audio stream.

        probe = Subprocess(cmd, stdout=Subprocess.PIPE, stderr=Subprocess.PIPE)
        out, err = probe.communicate()
        if probe.returncode != 0:
            raise RuntimeError(f'(FFprobe error {probe.returncode}) {err.decode().strip()}')

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
