import subprocess

from ..value import Flags

__all__ = [
    'set_flags', 'check_type', 'number_of_gpus', 'convert_kwargs_to_cmd_line_args'
]


def set_flags(limit_list):
    def _wrap_set_flags(flags):
        if isinstance(flags, Flags):
            flags = flags.compile()
        return Flags(flags, limit_list=limit_list)
    return _wrap_set_flags


def check_type(value, _type):
    if not isinstance(value, _type):
        raise TypeError(f"Value must be {_type}.")
    return value


def number_of_gpus():
    """
    Count numbers of NVIDIA GPU
    """
    try:
        return int(subprocess.getoutput("nvidia-smi --query-gpu=name --format=csv,noheader | wc -l"))
    except ValueError:
        return 0


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
