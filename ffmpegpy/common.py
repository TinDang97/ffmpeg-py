from typing import Union
import re


def set_video_size(video_size: Union[str, tuple]):
    video_size_exception = ValueError("Video size wrong format [w]x[h] or tuple of (w, h) "
                                      "and both w, h must non negative. "
                                      "Ex: 1920x1080 | (1920, 1080)")
    if not isinstance(video_size, (str, tuple)):
        raise video_size_exception

    if isinstance(video_size, str):
        if not re.match(r"[^D]x[^D]", video_size):
            raise video_size_exception
        w, h = map(int, video_size.split("x"))
    else:
        if video_size.__len__() != 2:
            raise video_size_exception

        w, h = video_size
        if w <= 0 or h <= 0:
            raise video_size_exception
    return f'{w}x{h}'
