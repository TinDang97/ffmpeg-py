from .util.pyopt import Options, option, in_list_filter, type_filter
from .util.constant import ConstantClass

__all__ = ['HWAccelType', 'HWAccel']


class HWAccelType(ConstantClass):
    AUTO = "auto"
    CUVID = "cuvid"
    CUDA = "cuda"
    VAAPI = "vaapi"
    DXVA2 = "dxva2"
    DRM = "drm"


class HWAccel(Options):
    hwaccel = option("hwaccel", in_list_filter(HWAccelType))
    hwaccel_device = option("hwaccel_device", in_list_filter(HWAccelType))
    hwaccel_output_format = option("hwaccel_output_format", type_filter(str))
