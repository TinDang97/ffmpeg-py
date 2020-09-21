import os
import subprocess
from binascii import unhexlify, hexlify


def convert_kwargs_to_cmd_line_args(kwargs):
    """
    Helper function to build command line arguments out of dict.
    """
    args = []
    for k in sorted(kwargs.keys()):
        v = kwargs[k]
        args.append('-{}'.format(k))
        if v is not None:
            args.append('{}'.format(v))
    return args


def number_of_gpus():
    """
    Count numbers of NVIDIA GPU
    """
    return int(subprocess.getoutput("nvidia-smi --query-gpu=name --format=csv,noheader | wc -l"))


def number_of_cores():
    """
    number_of_cores()

    Detect the number of cores in this system.
    """
    # Linux, Unix and MacOS:
    if hasattr(os, "sysconf"):
        if "SC_NPROCESSORS_ONLN" in os.sysconf_names:
            # Linux & Unix:
            ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
            if isinstance(ncpus, int) and ncpus > 0:
                return ncpus
        else:  # OSX:
            return int(os.popen2("sysctl -n hw.ncpu")[1].read())
    # Windows:
    if "NUMBER_OF_PROCESSORS" in os.environ:
        ncpus = int(os.environ["NUMBER_OF_PROCESSORS"])
        if ncpus > 0:
            return ncpus
    return 1  # Default


def get_attr_values(_object):
    """
    Return value list without built-in attribute.
    """
    attrs = []
    for k in dir(_object):
        if k.startswith("__"):
            continue

        v = getattr(_object, k)

        if hasattr(v, "__call__") or hasattr(v, "__func__"):
            continue
        attrs.append(v)
    return attrs


def check_type_instance(_instance, _types):
    if not isinstance(_instance, _types):
        raise TypeError(f'Required {_types}. Got "{type(_instance)}"')
    return True


def check_subclass(_instance, _types):
    if not issubclass(type(_instance), _types):
        raise TypeError(f'Required {_types}. Got "{type(_instance)}"')
    return True


def cvt_str2byte(string):
    check_type_instance(string, str)
    return ''.join(map(lambda x: f"{ord(x):08b}", string)).encode()


def cvt_8bit(binary):
    check_type_instance(binary, bytes)
    return ''.join(map(lambda x: f"{x:08b}", binary)).encode()


def cvt_str2hex(string):
    check_type_instance(string, str)
    return unhexlify(''.join(map(lambda x: f"{ord(x):x}", string)))


def cvt_dec2hex(number):
    output = f"{number:02x}"
    if len(output) % 2:
        output = f"0{output}"
    return unhexlify(output)


def cvt_hex2dec(binary):
    return int(hexlify(binary), 16)


def cvt_byte2str(binary):
    check_type_instance(binary, bytes)
    if len(binary) % 8:
        raise ValueError("Bytes was broken!")
    return ''.join(chr(int(binary[i:i + 8], 2)) for i in range(0, len(binary), 8))


def cvt_hex2str(binary):
    check_type_instance(binary, bytes)
    return ''.join(chr(i) for i in binary)


def cvt_bin2hex(binary):
    check_type_instance(binary, bytes)
    return unhexlify(''.join(f"{int(binary[i:i + 8], 2):x}" for i in range(0, len(binary), 8)))
