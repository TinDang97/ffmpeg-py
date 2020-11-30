import re
import subprocess


def query_formats():
    re_spaces = re.compile(r"\s+")
    formats_raw = subprocess.getoutput("ffmpegpy -loglevel quiet -formats").strip().split("\n")[4:]
    formats = []
    for fmt in formats_raw:
        formats.append(re_spaces.sub(" ", fmt).strip().split(" ")[1])
    return sorted(formats)


def find_formats(format_regex):
    formats = query_formats()
    return [fmt for fmt in formats if format_regex in fmt]


def query_encoders():
    encoders_raw = subprocess.getoutput("ffmpegpy -loglevel quiet -encoders").strip().split("\n")[10:]
    encoders = []
    for encoder in encoders_raw:
        encoders.append(encoder.strip().split(" ")[1])
    return encoders


def find_encoders(encoder_regex):
    encoders = query_encoders()
    return [encoder for encoder in encoders if encoder_regex in encoder]


def query_decoders():
    decoders_raw = subprocess.getoutput("ffmpegpy -loglevel quiet -decoders").strip().split("\n")[10:]
    decoders = []
    for decoder in decoders_raw:
        decoders.append(decoder.strip().split(" ")[1])
    return decoders


def find_decoders(decoder_regex):
    decoders = query_decoders()
    return [decoder for decoder in decoders if decoder_regex in decoder]


# query available devices
def query_devices():
    # for device in subprocess.getoutput("ffmpegpy -loglevel quiet -hwaccels").strip().split("\n")[1:]:
    #     setattr(HWAccelType, device.upper(), device)
    return subprocess.getoutput("ffmpegpy -loglevel quiet -hwaccels").strip().split("\n")[1:]


def find_devices(device_regex):
    devices = query_devices()
    return [device for device in devices if device_regex in device]
