from util.attrdict import ReadOnlyDict


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
    360: 0x0400,
    480: 0x0600,
    720: 0x0d00,
    960: 0x0f00,
    1080: 0x1000,
    1440: 0x1400,
    2160: 0x1800
})


FPS_DEFAULT = 15
CHUNK_SIZE_DEFAULT = 0x0200

MIN_RESOLUTION = 360
MAX_RESOLUTION = 2160




# PRESET_SUPPORT_LIST = [v for k, v in __dict__.items() if k.startswith("PRESET")]


HWACCEL_CUVID = "cuvid"
HWACCEL_CUDA = "cuda"
HWACCEL_VAAPI = "vaapi"
HWACCEL_AUTO = "auto"
# HWACCEL_SUPPORT_LIST = [v for k, v in __dict__.items() if k.startswith("HWACCEL")]

MP4_EXT = 'mp4'
PIPELINE = "pipe:"
FFMPEG_CMD = "libffmpeg"
