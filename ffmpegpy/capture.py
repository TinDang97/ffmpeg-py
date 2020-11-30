import os
import time

import cv2
import numpy

from datetime import datetime

from util.compression import compress_ndarray, decompress_ndarray, compress, decompress
from util.media import ENCODE_JPEG, DEFAULT_QUALITY
from util.media.image import imencode, imdecode, imwrite

from ._ffmpeg import FFmpeg, InputStream, OutputStream, PIPE_LINE, FPS_DEFAULT, LogLevel
from .codecs import PixelFormat, EncodeVideo, EncodeVideoLIB
from .ffprobe import FFprobe
from library.ffmpeg.formats.format import RawVideo, FormatDemux

__all__ = ["VideoCapture", "VideoWriter", "Capture", "Frame", "FrameReader", "ProcessHandler"]

from util.io import Subprocess

CHUNK_DEFAULT = 0x1000


class Frame(object):
    """
    Frame Data

    work with vectors, image's frame and numpy.ndarray like.

    Support multi-type frame: buffer, numpy.ndarray
    Auto compress and decompress with binary data. Encode, decode image if data is image's bytearray.
    """

    def __init__(self, frame, frame_size=None, dtype=None):
        if not isinstance(frame, (numpy.ndarray, bytes)):
            raise TypeError("Only support frame's type are `bytes` or `numpy.ndarray`")

        if frame_size:
            if not isinstance(frame_size, (tuple, list)):
                raise TypeError("Require frame_size is tuple or list")

            if len(frame_size) != 2:
                raise ValueError("Require frame_size is (width, height)!")

            if not isinstance(frame, numpy.ndarray):
                if dtype is None:
                    raise ValueError("Require dtype.")
                frame = numpy.frombuffer(frame, dtype=dtype)

            frame = frame.reshape((*frame_size, -1))
            if frame.shape[2] not in [3, 4]:
                raise ValueError(f"Number channels of frame must be 3 (RGB, BGR) or 4 (ARGB, ABGR). "
                                 f"Got {frame.shape[2]}")
        elif isinstance(frame, numpy.ndarray):
            frame = frame.copy()
        self.data_frame = frame

    def __repr__(self):
        if isinstance(self.data_frame, numpy.ndarray):
            return f"Frame\nShape: {self.data_frame.shape}\n" \
                   f"Raw size: {self.data_frame.itemsize * self.data_frame.size} bytes."
        return f"Raw size: {str(self.data_frame.__len__())}"

    def __eq__(self, other):
        if not isinstance(other, types := (type(self), numpy.ndarray)):
            raise TypeError(f"Require: {types}")
        if isinstance(other, numpy.ndarray):
            return numpy.all(self.data_frame == other)
        return numpy.all(self.data_frame == other.data_frame)

    def __bytes__(self):
        return self.tobytes()

    @property
    def size(self):
        if isinstance(self.data_frame, numpy.ndarray):
            return self.data_frame.shape
        return len(self.data_frame)

    @classmethod
    def from_buffer(cls, data):
        try:
            return cls(imdecode(data))
        except ValueError:
            pass

        try:
            return cls(decompress_ndarray(data))
        except ValueError:
            pass

        try:
            return cls(decompress(data))
        except ValueError:
            pass

        raise ValueError("Can't decompress data.")

    def tobytes(self):
        if isinstance(self.data_frame, numpy.ndarray):
            if self.data_frame.dtype == numpy.uint8:
                return imencode(self.data_frame)
            return compress_ndarray(self.data_frame)
        return compress(self.data_frame)

    def encode(self, compress_type=ENCODE_JPEG, quality=DEFAULT_QUALITY):
        """
        Like `tobytes` function but require frame's data is image bytearray.
        :return:
        """
        if not isinstance(self.data_frame, numpy.ndarray) or self.data_frame.dtype != numpy.uint8:
            raise TypeError("Only support image bytearray")
        return imencode(self.data_frame, compress_type, quality)

    @classmethod
    def decode(cls, data):
        """
        Like `from_buffer` function but only support if data is image buffer.
        :param data:
        :return:
        """
        return imdecode(data)

    def save(self, file_path, compress_type=ENCODE_JPEG, quality=DEFAULT_QUALITY, over_write=False):
        if isinstance(self.data_frame, numpy.ndarray) and self.data_frame.dtype == numpy.uint8:
            return imwrite(self.data_frame, file_path,
                           encode_type=compress_type, quality=quality, over_write=over_write)

        with open(file_path, "wb") as f:
            f.write(self.tobytes())

    @classmethod
    def open(cls, file_path):
        if not os.path.isfile(file_path):
            raise FileNotFoundError

        with open(file_path, "rb") as f:
            frame = cls.from_buffer(f.read())
        return frame


class ProcessHandler(object):
    def __init__(self, process, chunk_size=CHUNK_DEFAULT):
        if not isinstance(process, Subprocess):
            raise TypeError("Process must be Subprocess")

        if chunk_size <= 0:
            raise ValueError("Chunk size must be > 0.")

        self._process = process
        self.chunk_size = chunk_size

    def __repr__(self):
        return self._process.__repr__()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __iter__(self):
        return self

    def __next__(self):
        try:
            data = self.read()
            if data is None:
                raise StopIteration
            return data
        except RuntimeError:
            raise StopIteration

    def __bool__(self):
        return True

    def is_alive(self):
        return self._process.is_alive()

    def read(self, chunk_size=-1):
        if chunk_size < 0:
            chunk_size = self.chunk_size
        return self._process.read(chunk_size)

    def write(self, data):
        self._process.write(data)

    def stop(self):
        _, errs = self._process.communicate("q".encode())

        if errs:
            raise RuntimeError(errs)

    def kill(self):
        return self._process.kill()


class DataHandler(ProcessHandler):
    def read(self, chunk_size=-1):
        return Frame(super().read(chunk_size))


class FrameReader(ProcessHandler):
    def __init__(self, process, frame_size):
        super().__init__(process, frame_size[0] * frame_size[1] * 3)

        # if pixel_fmt in (PixelFormat.RGB24, PixelFormat.RGB24):
        # TODO: work with ARGB, RGBA, ABGR, BGRA (4 channels)
        self.frame_size = frame_size

    def get_frame(self):
        frame_bytes = super().read()
        if frame_bytes:
            return Frame(frame_bytes, self.frame_size, dtype=numpy.uint8)

    def write(self, data):
        raise AttributeError


class Capture(object):
    """
    Capture handler

    Parameters
    ----------
    src: str | int
        Source URI. (int=Capture local device, str=URI)

    output: None | str | -1
        Output destination (None=Not set, str=URI, '-1'=PIPE_LINE)
    """

    def __init__(self, src, output=None):
        self.probe = FFprobe(src)
        input_stream = InputStream(src)

        if output:
            self.mpeg = FFmpeg(input_stream, OutputStream(output))
        else:
            self.mpeg = FFmpeg(input_stream)
        self.__process_handler = None

    def __iter__(self):
        if self.process is None:
            self.start()
        return self.process.__iter__()

    def read_probe(self):
        return self.probe.info

    def read(self, chunk_size=-1):
        if self.process is None:
            raise RuntimeError("No process still working. Start process before read buffer.")
        return self.process.read(chunk_size)

    @property
    def process(self):
        return self.__process_handler

    @process.setter
    def process(self, new_process):
        if self.__process_handler is not None:
            raise AttributeError("Process's already existed.")

        if not isinstance(new_process, (ProcessHandler, type(None))):
            raise TypeError(f"Require `ProcessHandler`. Got `{type(new_process)}`")
        self.__process_handler = new_process

    @property
    def src(self):
        return self.probe.path

    @src.setter
    def src(self, source):
        self.mpeg.source = source
        self.probe.path = source

    def start(self):
        self.process = ProcessHandler(self.mpeg.run())

    def release(self):
        if self.process is None:
            return

        self.process.stop()
        self.__process_handler = None


class VideoCapture(Capture):
    def __init__(self, src, fps=FPS_DEFAULT, pix_fmt=PixelFormat.BGR24):
        super().__init__(src, PIPE_LINE)
        self.read_probe()

        self.mpeg.input_stream.re = None
        self.mpeg.output_stream.muxer = RawVideo()
        self.mpeg.output_stream.codec = EncodeVideo()
        self.mpeg.output_stream.codec.pix_fmt = pix_fmt

        self.loglevel = LogLevel.ERROR

        if fps == FPS_DEFAULT:
            self.mpeg.output_stream.frame_rate = self.probe.info.r_frame_rate

    @Capture.src.setter
    def src(self, source):
        super(VideoCapture, self.__class__).src.fset(self, source)
        self.probe.refresh()

    def run(self):
        if self.process is not None:
            raise AttributeError("Process's already existed.")
        self.process = FrameReader(self.mpeg.run(), self.probe.info.size)
        return self.process

    def read(self, **kwargs):
        return self.process.get_frame()

    def preview(self, window_name=None, window_size=(800, 600), capture_frame=False, prefix="", postfix="",
                compress_type=ENCODE_JPEG, quality=DEFAULT_QUALITY, over_write=False):

        if window_name is None:
            window_name = self.mpeg.input_stream.path

        start_time = 0
        frame_count = 0
        new_size = (window_size[0], int(round(window_size[0] / self.probe.info.width * self.probe.info.height)))

        for frame in self:
            if not start_time:
                start_time = time.time()

            frame_preview = cv2.resize(frame.data_frame, new_size)
            cv2.imshow(window_name, frame_preview)
            frame_count += 1

            press_key = cv2.waitKey(1) & 0xFF
            if press_key == ord("q"):
                self.release()
                cv2.destroyWindow(window_name)
                break
            elif capture_frame and press_key == ord(" "):
                frame.save(f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%s%f')}{postfix}.jpg",
                           compress_type, quality, over_write)
                frame_preview[:, :, :] = (255, 255, 255)
                cv2.imshow(window_name, frame_preview)
                cv2.waitKey(1)
        return int(round(frame_count / (time.time() - start_time)))


class VideoWriter(Capture):
    def __init__(self, src):
        super().__init__(src)

    def write(self, *outputs, muxer=None, codec=None, overwrite=False):
        for output in outputs:
            output_stream = OutputStream(output, codec=codec, muxer=muxer)

            if overwrite:
                output_stream.overwrite = None

            if self.mpeg.input_stream.muxer.format == FormatDemux.V4L2 \
                    or not codec or codec.codeclib == EncodeVideoLIB.COPY:
                del output_stream.codec.codeclib
            self.mpeg.add_output(output_stream)


class VideoGenerator(object):
    # @TODO(tindang97-ai): video generator from images

    def __init__(self, input_frame, write_file):
        pass

    def run(self):
        pass

    def add_frame(self):
        pass
