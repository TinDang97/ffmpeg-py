from ..util.constant import ConstantClass

__all__ = [
    "PixelFormat"
]


class PixelFormat(ConstantClass):
    COPY = "+"
    GRAY = "gray"
    RGB24 = "rgb24"
    RGB8 = "rgb8"
    BGR24 = "bgr24"

    YUV410P = "yuv410p"
    YUV420P = "yuv420p"
    YUVJ420P = "yuvj420p"
    YUV422P = "yuv422p"
    YUVV422P = "yuyv422"
    YUV444P = "yuv444p"
    YUVJ444P = "yuvj444p"

    NV12 = "nv12"
    NV16 = "nv16"
    NV24 = "nv24"

