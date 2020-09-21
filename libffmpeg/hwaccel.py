import subprocess

from util.options import Options, option, value_in_list
from util import get_attr_values

__all__ = ['HWAccelType', 'HWAccel', 'get_devices']


class HWAccelType:
    AUTO = "auto"
    CUVID = "cuvid"
    CUDA = "cuda"
    VAAPI = "vaapi"
    DXVA2 = "dxva2"
    DRM = "drm"


class HWAccel(Options):
    hwaccel = option("hwaccel", value_in_list(get_attr_values(HWAccelType)))
    hwaccel_device = option("hwaccel_device", value_in_list(get_attr_values(HWAccelType)))
    hwupload = option("hwupload")
    hwdownload = option("hwdownload")


# query available devices
def get_devices():
    # for device in subprocess.getoutput("ffmpeg -loglevel quiet -hwaccels").strip().split("\n")[1:]:
    #     setattr(HWAccelType, device.upper(), device)
    return subprocess.getoutput("ffmpeg -loglevel quiet -hwaccels").strip().split("\n")[1:]
