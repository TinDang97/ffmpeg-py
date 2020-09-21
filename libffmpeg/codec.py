import subprocess

from util.options import Options, option, value_in_list, check_min_value, check_max_value, check_in_range, \
    check_type
from util import number_of_gpus
from util import get_attr_values

__all__ = [
    'get_decoders', 'get_encoders', 'find_decoders', 'find_encoders', 'CodecName',
    'EncodeVideo', 'EncodeAudio', 'EncodeVideoLIB', 'NVENCLIB',
    'DecodeVideo', 'DecodeAudio', 'DecodeVideoLIB', 'NVDECLIB',
    'NVENCRateControl', 'NVENCPreset', 'NVENCProfile',
    'CodecNVENC', 'NVDEC', 'NVENCH264', 'NVENCHEVC',
    'PixelFormat', 'Codec', 'CodecLIB', 'CodecCopy',
    'Tune', 'Preset', 'Profile', 'XH264', 'XHEVC', ''
]


def get_encoders():
    encoders_raw = subprocess.getoutput("ffmpeg -loglevel quiet -encoders").strip().split("\n")[10:]
    encoders = []
    for encoder in encoders_raw:
        encoders.append(encoder.strip().split(" ")[1])
    return encoders


def find_encoders(encoder_regex):
    encoders = get_encoders()
    return [encoder for encoder in encoders if encoder_regex in encoder]


def get_decoders():
    decoders_raw = subprocess.getoutput("ffmpeg -loglevel quiet -decoders").strip().split("\n")[10:]
    decoders = []
    for decoder in decoders_raw:
        decoders.append(decoder.strip().split(" ")[1])
    return decoders


def find_decoders(decoder_regex):
    decoders = get_decoders()
    return [decoder for decoder in decoders if decoder_regex in decoder]


class CodecName:
    H264 = "h264"
    HEVC = "hevc"
    RAW_VIDEO = "rawvideo"
    COPY = "copy"


class CodecLIB:
    COPY = "copy"


class EncodeVideoLIB(CodecLIB):
    H264 = "libx264"
    HEVC = "libx265"


class DecodeVideoLIB(CodecLIB):
    H264 = "h264"
    HEVC = "hevc"


class NVDECLIB:
    H264 = "h264_cuvid"
    HEVC = "hevc_cuvid"


class NVENCLIB:
    H264 = "h264_nvenc"
    HEVC = "hevc_nvenc"


class Profile:
    H264_BASELINE = "baseline"
    H264_MAIN = "main"
    H264_HIGH = "high"
    HEVC_MAIN = "main"
    HEVC_MAIN10 = "main10"
    HEVC_MAIN12 = "main12"


class NVENCProfile:
    NVENC_H264_BASELINE = "baseline"
    NVENC_H264_MAIN = "main"
    NVENC_H264_HIGH = "high"
    NVENC_H264_HIGH444P = "high444p"
    NVENC_HEVC_BASELINE = "main"


class Preset:
    """
    libffmpeg -hide_banner -h encoder=$(codec)
    -> codec: libffmpeg -hide_banner -encoders
    """
    SLOWER = 'slower'
    SLOW = 'slow'
    MEDIUM = 'medium'
    FAST = 'fast'
    FASTER = 'faster'
    VERYFAST = 'veryfast'
    ULTRAFAST = 'ultrafast'


class NVENCPreset:
    NVENC_SLOW = "slow"
    NVENC_MEDIUM = "medium"
    NVENC_FAST = "fast"
    NVENC_HIGH_PERFORMANCE = "hp"
    NVENC_HIGH_QUALITY = "hq"
    NVENC_BLURAY_DISK = "bd"
    NVENC_LOW_LATENCY = "ll"
    NVENC_LOW_LATENCY_HIGH_QUALITY = "llhq"
    NVENC_LOW_LATENCY_HIGH_PERFORMANCE = "llhp"
    NVENC_LOSSLESS = "lossless"
    NVENC_LOSSLESS_HIGH_PERFORMANCE = "losslesshp"


class Tune:
    H264_ZEROLATENCY = 'zerolatency'
    H264_FASTDECODE = 'fastdecode'
    H264_PSNR = 'psnr'
    H264_SSIM = 'ssim'
    H264_STILLIMAGE = 'stillimage'
    H264_GRAIN = 'grain'
    H264_ANIMATION = 'animation'
    H264_FILM = 'film'

    HEVC_ZEROLATENCY = 'zerolatency'
    HEVC_FASTDECODE = 'fastdecode'
    HEVC_GRAIN = 'grain'
    HEVC_SSIM = 'ssim'
    HEVC_PSNR = 'psnr'
    HEVC_ANIMATION = 'animation'


class NVENCRateControl:
    CONSTQP = 'constqp'
    VBR = 'vbr'
    CBR = 'cbr'
    VBR_MINQP = 'vbr_minqp'
    LL_2PASS_QUALITY = 'll_2pass_quality'
    LL_2PASS_SIZE = 'll_2pass_size'
    CBR_LD_HQ = 'cbr_ld_hq'
    CBR_HQ = 'cbr_hq'
    VBR_HQ = 'vbr_hq'


class PixelFormat:
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


class Codec(Options):
    pass


class EncodeAudio(Codec):
    pass


class EncodeVideo(Codec):
    def __init__(self, codec=None):
        super().__init__()

        if not codec:
            return

        if not isinstance(codec, (str, EncodeVideo)):
            raise ValueError("Must be CodecVideo or string.")

        if isinstance(codec, str):
            codec_names = get_attr_values(CodecName)

            if codec not in codec_names:
                raise ValueError(f'Value must in {codec_names}. But got "{codec}"')

            if codec == CodecName.H264:
                self.codeclib = EncodeVideoLIB.H264
            elif codec == CodecName.HEVC:
                self.codeclib = EncodeVideoLIB.HEVC
            elif codec == CodecName.COPY:
                self.codeclib = EncodeVideoLIB.COPY
        else:
            self.from_options(codec)

    codeclib = option("c:v", value_in_list(get_attr_values(EncodeVideoLIB)))
    profile = option("profile:v", value_in_list(get_attr_values(Profile)))
    preset = option("preset", value_in_list(get_attr_values(Preset)))
    tune = option("profile:v", value_in_list(get_attr_values(Tune)))
    gop_size = option("g", check_min_value(0))
    bitrate = option("b:v", check_min_value(0))
    max_bitrate = option("max_bitrate", check_min_value(0))
    bufsize = option("bufsize", check_min_value(0))
    pix_fmt = option("pix_fmt", value_in_list(get_attr_values(PixelFormat)))
    constant_quality = option("crf", check_in_range(0, 51))


class DecodeVideo(Codec):
    codeclib = option("c:v", value_in_list(get_attr_values(DecodeVideoLIB)))


class DecodeAudio(Codec):
    pass


class NVDEC(DecodeVideo):
    codeclib = option(DecodeVideo.codeclib.name, value_in_list(get_attr_values(NVDECLIB)))


class CodecNVENC(EncodeVideo):
    def __init__(self, codec_name):
        super().__init__()
        if codec_name not in get_attr_values(CodecName):
            raise ValueError(f"Support {get_attr_values(CodecName)}. But got {codec_name}")
        if codec_name == CodecName.H264:
            self.codeclib = NVENCLIB.H264
        elif codec_name == CodecName.HEVC:
            self.codeclib = NVENCLIB.HEVC
        else:
            raise ValueError("Codec name isn't supported!")

    codeclib = option(EncodeVideo.codeclib.name, value_in_list(get_attr_values(NVENCLIB)))
    rc = option("rc", value_in_list(get_attr_values(NVENCRateControl)))
    preset = option(
        "preset",
        value_in_list(get_attr_values(NVENCPreset))
    )
    gpu = option("gpu", check_max_value(number_of_gpus()))
    constant_quality = option("cq", check_in_range(0, 51))
    strict_gop = option("strict_gop", check_type(bool))
    quantization_parameter = option("qp", check_in_range(-1, 51))


class NVENCH264(CodecNVENC):
    def __init__(self):
        super().__init__(CodecName.H264)


class NVENCHEVC(CodecNVENC):
    def __init__(self):
        super().__init__(CodecName.HEVC)


class XH264(EncodeVideo):
    def __init__(self):
        super().__init__(CodecName.H264)


class XHEVC(EncodeVideo):
    def __init__(self):
        super().__init__(CodecName.HEVC)


class CodecCopy(EncodeVideo):
    def __init__(self):
        super().__init__(EncodeVideoLIB.COPY)
