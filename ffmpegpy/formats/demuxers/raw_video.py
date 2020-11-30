
from ffmpegpy.common import set_video_size
from ffmpegpy.util.pyopt import option, in_list_filter, min_value_filter
from ..format import Demuxer, FormatDemuxer
from ..pixel_format import PixelFormat


class RawVideo(Demuxer):
    """
    Raw video demuxer. Need framerate(=25), pixel_format(=yuv420p) and video_size to decode raw video data.
    """

    format = option(
        Demuxer.format,
        set_filter=in_list_filter(FormatDemuxer.RAW_VIDEO,),
        default_value=FormatDemuxer.RAW_VIDEO,
        doc='Raw video demuxer.'
    )

    framerate = option(
        "framerate",
        set_filter=min_value_filter(1),
        doc="Set input video frame rate. Default value is 25."
    )

    pixel_format = option(
        "pixel_format",
        set_filter=in_list_filter(PixelFormat),
        doc="Set the input video pixel format. Default value is `yuv420p`."
    )

    video_size = option(
        "video_size",
        set_filter=set_video_size,
        doc="Set the input video size. This value must be specified explicitly."
    )
