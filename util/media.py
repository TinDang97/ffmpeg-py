import os
import subprocess
import time
from datetime import datetime

import ffmpeg
from dpsutil.attrdict import AttrDict
from dpsutil.log import write_info

from util.attrdict import ReadOnlyDict
from util.io import FileWritable

RESOLUTION_TERM = ReadOnlyDict({
    360: '360p',
    480: '480p',
    720: '720p',
    960: '960p',
    1080: '1080p',
    1440: '1440p',
    2160: '2160p'
})

BITRATE = ReadOnlyDict({
    '360p': 0x0400,
    '480p': 0x0600,
    '720p': 0x0d00,
    '960p': 0x0f00,
    '1080p': 0x1000,
    '1440p': 0x1400,
    '2160p': 0x1800
})

FPS_DEFAULT = 15

CHUNK_SIZE_DEFAULT = 0x0200

MIN_RESOLUTION = 360
MAX_RESOLUTION = 2160

COPY_CODEC = "copy"
H264_CODEC = "h264"
H265_CODEC = "hevc"

H264_CODEC_LIB = "libx264"
H265_CODEC_LIB = "libx265"

H264_PROFILE = "main"
PRESET_CODEC = "veryfast"

MP4_EXT = 'mp4'
PIPELINE = "pipe:"
FFMPEG_CMD = "libffmpeg"


def resolution_parser(resolution):
    _, height = resolution
    start_range = MIN_RESOLUTION

    if height < start_range:
        return RESOLUTION_TERM[start_range]

    for res in RESOLUTION_TERM.keys():
        if height in range(start_range, res):
            return RESOLUTION_TERM[start_range]
        start_range = res
    return RESOLUTION_TERM[MAX_RESOLUTION]


class CaptureError(Exception):
    pass


class Options(ReadOnlyDict):
    """
    Options baseline.
    Can't change options without callable first.

    Examples
    --------
    >>> a = Options(a=1)
    >>> a.a = 4
    AttributeError: Read only!

    >>> b = a()
    >>> b.a = 4
    >>> b.a
    4
    """

    def __call__(self, *args, **kwargs):
        return AttrDict(self)


probe_opts = Options(
    hide_banner=None,
    probesize=32,
    analyzeduration=0,
    rtsp_transport='tcp'
)

input_options = Options(
    hide_banner=None,
    an=None,
    probesize=32,
    analyzeduration=0,
    # fflags='nobuffer',
    # strict='experimental',
    re=None,
    loglevel='quiet'
)

codec_options = Options({
    'pix_fmt': '+',
})

muxer_options = Options({
    'an': None,
    'sn': None,
    'dn': None,
    'f': 'mp4',
    'movflags': '+dash+negative_cts_offsets+faststart',
    "blocksize": 128,
    "frag_duration": 2000,
    "min_frag_duration": 2000
})


class OutputNode(AttrDict):
    def add(self, node_name, node):
        return self.__setitem__(node_name, node)

    def get(self, node_name):
        return self.__getitem__(node_name)


class MP4Container(object):
    """
    Video capture into mp4 muxer. Support H264, H265 encoding.

    Parameters
    ----------
    src: str|int
        PIPELINE | FILE | RTSP | Device

    max_fr: int
        Max frame per second. Default: FPS_DEFAULT
    """

    @property
    def height(self):
        return self.resolution[1]

    @property
    def width(self):
        return self.resolution[0]

    @property
    def bitrate(self):
        return f'{self.__bitrate}k'

    @bitrate.setter
    def bitrate(self, bitrate):
        if not isinstance(bitrate, str):
            raise ValueError("Required str: '2000k' or '2M'")

        try:
            if not int(bitrate[:-1]) or bitrate[-1] not in ['M', 'k']:
                raise ValueError("Required str: '2000k' or '2M'")
        except ValueError:
            raise ValueError("Required str: '2000k' or '2M'") from None

        _value = int(bitrate[:-1])
        _type = bitrate[-1]

        if _type == 'M':
            _value *= 1024

        self.__bitrate = _value

    @staticmethod
    def __build_muxer():
        return muxer_options()

    def __build_codec(self, codec=None):
        if codec is None or codec == self.raw_codec:
            codec = COPY_CODEC

        if codec not in [COPY_CODEC, H264_CODEC, H265_CODEC]:
            raise ValueError("Only support h264 either h265 codec!")

        codec_opts = codec_options()

        if codec == COPY_CODEC:
            codec_opts['c:v'] = COPY_CODEC
            return codec_opts

        codec_opts['r'] = self.max_fr
        codec_opts['g'] = int(self.max_fr * 2)

        if self.__bitrate:
            codec_opts.update({
                'b:v': self.bitrate,
                'maxrate': f"{int(self.__bitrate * 1.1)}k",
                'bufsize': f"{int(self.__bitrate * 2)}k"
            })
        else:
            max_bitrate = BITRATE[f'{MAX_RESOLUTION}p']
            codec_opts.update({
                'crf': 20,
                'maxrate': f"{max_bitrate}k",
                'bufsize': f"{int(max_bitrate * 2)}k"
            })

        if codec != COPY_CODEC:
            codec_opts['preset'] = PRESET_CODEC
            if codec == H264_CODEC:
                codec_opts['c:v'] = H264_CODEC_LIB
                codec_opts['profile:v'] = H264_PROFILE
            elif codec == H265_CODEC:
                codec_opts['c:v'] = H265_CODEC_LIB

                # log options in H265
                if self.write_log:
                    codec_opts["x265-params"] = "log-level=info"
                elif "x265-params" in codec_options:
                    codec_opts["x265-params"] = "log-level=quite"
        return codec_opts

    def write_pipe(self, buffer):
        if not self.__process or self.src != PIPELINE:
            raise RuntimeError("Stdin isn't existed!")
        try:
            ret = self.__process.stdin.write(buffer)
        except BrokenPipeError as e:
            write_info(self.__process.stderr.read())

        write_info(ret)

    def pipe(self, codec=None):
        """
        Add pipeline output.
        """
        codec_opts = self.__build_codec(codec=codec)
        muxer_opts = self.__build_muxer()
        output_stream = libffmpeg.output(self.__input_stream, PIPELINE, **muxer_opts, **codec_opts)
        self.__output_nodes.add(PIPELINE, output_stream)

        if self.write_log:
            write_info(f"Added pipeline:\n{muxer_opts}")

    def read(self, chunk_size=None):
        if not self.__process or self.__process.poll() is not None:
            raise CaptureError("Not pipeline output signal. Ref: .pipe()")
        return self.__process.stdout.read(int(chunk_size) if chunk_size else self.__bitrate)

    def write(self, file_path, duration=None, over_write=False, codec=None):
        """
        Add file output
        :param duration:
        :param codec:
        :param file_path:
        :param over_write:
        :return:
        """
        *name, ext = file_path.split('.')

        if name.__len__() == 0:
            file_path = f"{file_path}.{MP4_EXT}"
            ext = MP4_EXT

        if ext != MP4_EXT:
            raise CaptureError(f"Extension '{ext}' isn't supported! MP4 only!")

        codec_opts = self.__build_codec(codec=codec)
        muxer_opts = self.__build_muxer()

        if duration and duration > 0:
            muxer_opts['t'] = int(round(duration))

        output_stream = libffmpeg.output(self.__input_stream, file_path, **muxer_opts, **codec_opts)

        if os.path.isfile(file_path) and over_write:
            output_stream = libffmpeg.overwrite_output(output_stream)

        self.__output_nodes.add(file_path, output_stream)

        if self.write_log:
            write_info(f"Added write to {file_path}:\n{muxer_opts}")

    def clear_outputs(self):
        self.__output_nodes.clear()

    def remove_output(self, *_node_name):
        for node_name in _node_name:
            self.__output_nodes.clear(node_name)

    @property
    def output_nodes(self):
        return list(self.__output_nodes.keys())

    def run(self, force=False, check_success=True, timeout=5):
        """
        Start process camera video from camera
        Restart process if it's already running.
        """
        if self.__process and force:
            self.stop()

        if self.__process and self.__process is not None:
            raise CaptureError("Process is already running!")

        if self.__output_nodes.__len__() <= 0:
            raise CaptureError("Empty output node.")

        stdout = PIPELINE in self.__output_nodes or PIPELINE == self.src
        run_async = stdout

        if self.__output_nodes.__len__() > 1:
            output_stream = libffmpeg.merge_outputs(*self.__output_nodes.values())
        else:
            output_stream = list(self.__output_nodes.values())[0]

        args = libffmpeg.compile(output_stream, FFMPEG_CMD)

        if not run_async:
            self.__process = subprocess.Popen(args, close_fds=True)
        else:
            self.__process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE if PIPELINE in self.__output_nodes else None,
                stdin=subprocess.PIPE if PIPELINE == self.src else None,
                stderr=subprocess.PIPE
            )

        if check_success and PIPELINE != self.src:
            time.sleep(timeout)

            if self.__process.poll() is not None:
                self.__process = None
                raise CaptureError(f"Start failed!\n{' '.join(args)}") from None

    @property
    def is_running(self):
        return self.__process and self.__process.poll() is None

    def wait(self):
        if self.__process:
            out, err = self.__process.communicate()
            retcode = self.__process.poll()
            self.__process = None
            if retcode:
                raise CaptureError('libffmpeg', out, err)
            return out
        return 0

    def stop(self):
        if self.__process:
            if self.__process.stdin:
                self.__process.stdin.close()

            self.__process.kill()
            self.__process.poll()
            self.__process.wait()
            self.__process = None
        return 0

    def __init__(self, src, input_size=None, max_fr=FPS_DEFAULT, write_log=False):
        if isinstance(src, int):
            src = f"/dev/video{src}"

        self.src = src
        self.write_log = write_log

        """input stream"""
        self.input_opts = input_options()
        self.input_opts['loglevel'] = "info" if write_log else "error"

        if src.startswith("/dev/video"):
            self.input_opts['f'] = "v4l2"
            self.input_opts['framerate'] = max_fr

            if input_size:
                self.input_opts["video_size"] = f"{input_size[0]}x{input_size[1]}"

        if src.startswith("rtsp"):
            self.input_opts['rtsp_transport'] = "tcp"

        self.__input_stream = libffmpeg.input(src, **self.input_opts)

        self.info = None
        self.resolution = None
        self.resolution_term = None

        self.__bitrate = 0
        self.raw_codec = None

        if src != PIPELINE:
            """get source's metadata"""
            try:
                info_streams = libffmpeg.probe(self.src, **probe_opts())
                self.info = next(stream for stream in info_streams['streams'] if stream['codec_type'] == "video")
            except libffmpeg.Error as e:
                raise CaptureError(e) from None
            except StopIteration:
                raise CaptureError("No video stream from source!") from None

            """init resolution"""
            self.resolution = self.info['width'], self.info['height']

            """init codec"""
            self.raw_codec = self.info['codec_name']

            if self.raw_codec not in [H264_CODEC, H265_CODEC]:
                raise CaptureError(f"Codec {self.raw_codec} isn't be supported!")

        if self.resolution:
            """init resolution_term"""
            self.resolution_term = resolution_parser(self.resolution)

            """init bitrate"""
            self.__bitrate = BITRATE[self.resolution_term]

        """init framerate"""
        self.max_fr = max_fr

        """create stream cmd"""
        self.__output_nodes = OutputNode()
        self.__process = None

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __iter__(self):
        if PIPELINE not in self.__output_nodes:
            raise RuntimeError("Not existed pipeline output!")

        self.run(check_success=False)
        return self

    def __next__(self):
        try:
            buffer = self.read()
        except CaptureError as e:
            raise StopIteration(e) from None
        return buffer


class PipeContainer(MP4Container):
    def __init__(self, src, codec=COPY_CODEC, input_size=None, max_fr=FPS_DEFAULT, write_log=False):
        super().__init__(src, input_size, max_fr, write_log)
        self.pipe(codec)

    def write(self, *args, **kwargs):
        raise AttributeError


class FileContainer(MP4Container):
    def __init__(self, src, output_path, over_write=False, duration=None, codec=COPY_CODEC,
                 input_size=None, max_fr=FPS_DEFAULT, write_log=False):
        super().__init__(src, input_size, max_fr, write_log)
        self.write(output_path, codec=codec, over_write=over_write, duration=duration)

    def pipe(self, *args, **kwargs):
        raise AttributeError

    def read(self, *args, **kwargs):
        raise AttributeError


class SegmentContainer(MP4Container):
    def __init__(self, src, output_path, over_write=False, segment_time=None, codec=COPY_CODEC, input_size=None,
                 max_fr=FPS_DEFAULT, write_log=False):
        super().__init__(src, input_size, max_fr, write_log)
        self.file_path = FileWritable(
            output_path,
            postfix=lambda: datetime.now().strftime("-%Y%m%d%H%M%S")
        )

        self.over_write = over_write
        self.codec = codec
        self.time_recorded = None
        self.segment_time = segment_time

        self.write(self.file_path.path, codec=codec, over_write=over_write)

    def pipe(self, *args, **kwargs):
        raise AttributeError

    def read(self, *args, **kwargs):
        raise AttributeError

    def write_pipe(self, buffer):
        if self.time_recorded is None:
            self.time_recorded = time.time()

        if time.time() - self.time_recorded > self.segment_time:
            self.clear_outputs()
            self.write(self.file_path.path, codec=self.codec, over_write=self.over_write)
            super().run(check_success=False, force=True)
            self.time_recorded = None

        super().write_pipe(buffer)
