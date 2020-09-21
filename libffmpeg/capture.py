import os
import time
from datetime import datetime

import cv2
import numpy
from dpsutil.media import ENCODE_JPEG, DEFAULT_QUALITY
from dpsutil.media.image import imencode, imdecode, imwrite

from libffmpeg.codec import PixelFormat, EncodeVideo
from libffmpeg.ffmpeg import FFmpeg, FFprobe, InputStream, OutputStream, PIPE_LINE, FPS_DEFAULT
from libffmpeg.format import RawMuxer
from util.compression import compress_ndarray, decompress_ndarray, compress, decompress

__all__ = ["VideoCapture", "Frame", "FrameReader", "ProcessHandler"]

from util.io import Subprocess

CHUNK_DEFAULT = 0x1000


class Frame(object):
    """
    Frame Data

    work with vectors, image's frame and numpy.ndarray like.

    Support multi-type frame: buffer, numpy.ndarray
    Auto compress and decompress with binary data. Encode, decode image if data is image's bytearray.
    """

    @property
    def size(self):
        if isinstance(self.frame, numpy.ndarray):
            return self.frame.shape
        return len(self.frame)

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
        if isinstance(self.frame, numpy.ndarray):
            if self.frame.dtype == numpy.uint8:
                return imencode(self.frame)
            return compress_ndarray(self.frame)
        return compress(self.frame)

    def encode(self, compress_type=ENCODE_JPEG, quality=DEFAULT_QUALITY):
        """
        Like `tobytes` function but require frame's data is image bytearray.
        :return:
        """
        if not isinstance(self.frame, numpy.ndarray) or self.frame.dtype != numpy.uint8:
            raise TypeError("Only support image bytearray")
        return imencode(self.frame, compress_type, quality)

    @classmethod
    def decode(cls, data):
        """
        Like `from_buffer` function but only support if data is image buffer.
        :param data:
        :return:
        """
        return imdecode(data)

    def save(self, file_path, compress_type=ENCODE_JPEG, quality=DEFAULT_QUALITY, over_write=False):
        if isinstance(self.frame, numpy.ndarray) and self.frame.dtype == numpy.uint8:
            return imwrite(self.frame, file_path, encode_type=compress_type, quality=quality, over_write=over_write)

        with open(file_path, "wb") as f:
            f.write(self.tobytes())

    @classmethod
    def open(cls, file_path):
        if not os.path.isfile(file_path):
            raise FileNotFoundError

        with open(file_path, "rb") as f:
            frame = cls.from_buffer(f.read())
        return frame

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

        if isinstance(frame, numpy.ndarray):
            self.frame = frame.copy()
        else:
            self.frame = frame

    def __repr__(self):
        if isinstance(self.frame, numpy.ndarray):
            return f"Frame\nShape: {self.frame.shape}\nRaw size: {self.frame.itemsize * self.frame.size} bytes."
        return f"Raw size: {str(self.frame.__len__())}"

    def __eq__(self, other):
        if not isinstance(other, types := (type(self), numpy.ndarray)):
            raise TypeError(f"Require: {types}")
        if isinstance(other, numpy.ndarray):
            return numpy.all(self.frame == other)
        return numpy.all(self.frame == other.frame)

    def __bytes__(self):
        return self.tobytes()


class ProcessHandler(object):
    def is_alive(self):
        return self._process.is_alive()

    def read(self, chunk_size=-1):
        if chunk_size < 0:
            chunk_size = self.chunk_size
        return self._process.read(chunk_size)

    def write(self, data):
        self._process.write(data)
        self._process.stdout.flush()

    def stop(self):
        _, errs = self._process.communicate("q".encode())

        if errs:
            raise RuntimeError(errs)

    def kill(self):
        return self._process.kill()

    def __init__(self, process, chunk_size=CHUNK_DEFAULT):
        if not isinstance(process, Subprocess):
            raise TypeError("Process must be Subprocess")
        self._process = process
        self.chunk_size = chunk_size

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


class DataHandler(ProcessHandler):
    def read(self, chunk_size=-1):
        return Frame(super().read(chunk_size))


class FrameReader(ProcessHandler):
    def __init__(self, process, frame_size):
        super().__init__(process)

        # if pixel_fmt in (PixelFormat.RGB24, PixelFormat.RGB24):
        # TODO: work with ARGB, RGBA, ABGR, BGRA (4 channels)
        self.chunk_size = frame_size[0] * frame_size[1] * 3
        self.frame_size = frame_size

    def read(self, *args, **kwargs):
        frame_bytes = super().read(self.chunk_size)
        if frame_bytes:
            return Frame(frame_bytes, self.frame_size, dtype=numpy.uint8)

    def write(self, data):
        raise AttributeError


class Capture(FFmpeg):
    """
    Capture handler

    Parameters
    ----------
    src: str | int
        Source URI. (int=Capture local device, str=URI)

    output: None | str | -1
        Output destination (None=Not set, str=URI, '-1'=PIPE_LINE)
    """
    def run(self):
        if self._process:
            raise RuntimeError("Process already existed.")
        self._process = ProcessHandler(super().run())

    def read_info(self):
        self.probe.read()

    def reset(self):
        if self.__process_handler is None:
            return
        self.__process_handler = None

    def read(self, chunk_size=-1):
        if self._process is None:
            self.run()
        return self._process.read(chunk_size)

    def release(self):
        if self._process is None:
            return
        return self._process.stop()

    @property
    def _process(self):
        return self.__process_handler

    @_process.setter
    def _process(self, new_process):
        if self._process is not None:
            raise AttributeError("Process's already existed.")

        if not isinstance(new_process, (ProcessHandler, type(None))):
            raise TypeError(f"Require `ProcessHandler`. Got `{type(new_process)}`")
        self.__process_handler = new_process

    def __init__(self, src, output=None):
        self.probe = FFprobe(src)

        input_stream = InputStream(src)
        if output:
            super().__init__(input_stream, OutputStream(output))
        else:
            super().__init__(input_stream)
        self.__process_handler = None

    def __iter__(self):
        if self._process is None:
            self.run()
        return self._process.__iter__()


class VideoCapture(Capture):
    def run(self):
        self._process = FrameReader(super(Capture, self).run(), self.probe.info.size)
        return self._process

    def read(self, **kwargs):
        return self._process.read()

    def preview(self, window_name=None, capture_frame=False, prefix="", postfix="",
                compress_type=ENCODE_JPEG, quality=DEFAULT_QUALITY, over_write=False):
        self.reset()
        if window_name is None:
            window_name = self.input_stream.path

        start_time = 0
        frame_count = 0
        for frame in self:
            if not start_time:
                start_time = time.time()

            cv2.imshow(window_name, frame.frame)
            frame_count += 1

            press_key = cv2.waitKey(1) & 0xFF
            if press_key == ord("q"):
                self.release()
                cv2.destroyWindow(window_name)
                break
            elif capture_frame and press_key == ord(" "):
                frame.save(f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%s%f')}{postfix}.jpg",
                           compress_type, quality, over_write)
                frame.frame[:, :, :] = (255, 255, 255)
                cv2.imshow(window_name, frame.frame)
                cv2.waitKey(1)

        return int(round(frame_count / (time.time() - start_time)))

    def __init__(self, src, fps=FPS_DEFAULT, pix_fmt=PixelFormat.BGR24):
        super().__init__(src, PIPE_LINE)
        self.read_info()

        self.input_stream.re = None
        self.output_stream.muxer = RawMuxer()
        self.output_stream.codec = EncodeVideo()
        self.output_stream.codec.pix_fmt = pix_fmt

        if fps == FPS_DEFAULT:
            self.output_stream.frame_rate = self.probe.info.r_frame_rate


class VideoWriter(Capture):
    def __init__(self, src):
        super().__init__(src)

    def write(self, *outputs, muxer=None, codec=None, overwrite=False):
        for output in outputs:
            output_stream = OutputStream(output, codec=codec, muxer=muxer)

            if overwrite:
                output_stream.overwrite = None
            super(VideoWriter, self).add_output(output_stream)
