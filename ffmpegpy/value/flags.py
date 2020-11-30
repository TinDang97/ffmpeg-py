"""
FFmpeg flags
Support auto convert and handle even negative (-) flag.

Support all flags format of FFmpeg:
- Codec flag: https://ffmpeg.org/ffmpeg-codecs.html#Codec-Options
- Log level flag: https://ffmpeg.org/ffmpeg-all.html
- Format fflags: https://ffmpeg.org/ffmpeg-formats.html
- MovFlags: https://ffmpeg.org/ffmpeg-formats.html#mov_002c-mp4_002c-ismv
- ...

Notes: check possible value before add.

Implementor: tindangai-97
"""


from typing import Union, List, Iterable

__all__ = [
    'Flags', 'LimitedFlag', 'UnknownFlag'
]

FlagType = Union[str]

POS_FLAG = "+"
NEG_FLAG = "-"


class UnknownFlag(ValueError):
    def __init__(self, flag):
        super().__init__(f"`{flag}`")


class LimitedFlag(ValueError):
    def __init__(self, flag: FlagType, limit: Iterable):
        super(LimitedFlag, self).__init__(f"`{flag}` out of limited list.\n"
                                          f"{ [*limit] }.")


def check_type(value, _type):
    if not isinstance(value, _type):
        raise TypeError(f"Value must be {_type}.")
    return value


def split_flags(flag_str: str):
    flag_str = check_type(flag_str, str)
    flags = list()

    start_pos = 0
    for idx, char in enumerate(flag_str[start_pos + 1:]):
        if char in [NEG_FLAG, POS_FLAG]:
            flag = flag_str[start_pos:idx + 1]
            flags.append(flag)
            start_pos = idx + 1

    # add last element
    flag = flag_str[start_pos:]
    flags.append(flag)
    return flags


class FlagList(list):
    def __setitem__(self, index: int, value: FlagType):
        return super().__setitem__(index, check_type(value, str))

    def append(self, value: FlagType):
        return super().append(check_type(value, str))


class Flags:
    """
    FFmpeg flags
    """
    def __init__(self, setup: Union[str, 'Flags', None] = None, limit_list: Iterable = ()):
        self.__positive_lst = FlagList()
        self.__negative_lst = FlagList()

        if not isinstance(limit_list, Iterable):
            raise TypeError("limit_list must be `iterator`")

        self.limit_list = limit_list

        if isinstance(setup, Flags):
            self.__positive_lst.extend(setup.__positive_lst)
            self.__negative_lst.extend(setup.__negative_lst)
        elif isinstance(setup, str):
            if not setup:
                return
            self.add(setup)
        elif setup is not None:
            raise TypeError(f"Type of flag's setup `{type(setup)}` isn't supported.")

    def __delitem__(self, flag: FlagType):
        flag = check_type(flag, str)
        sign = POS_FLAG

        if flag.startswith(NEG_FLAG):
            sign = NEG_FLAG
            flag = flag[1:]

        elif flag.startswith(POS_FLAG):
            flag = flag[1:]

        if not flag:
            raise UnknownFlag(flag)

        try:
            if sign == POS_FLAG:
                self.__positive_lst.remove(flag)
            else:
                self.__negative_lst.remove(flag)
        except ValueError:
            raise UnknownFlag(flag) from None

    def __iadd__(self, flag: FlagType):
        self.add(flag)
        return self

    def __isub__(self, flag: FlagType):
        self.delete(flag)
        return self

    def __repr__(self):
        return self.compile()

    def __eq__(self, other: Union[str, 'Flags']):
        if not isinstance(other, Flags):
            other = Flags(other)
        return self.compile().__eq__(other.compile())

    def compile(self) -> str:
        """
        Compile flag string with reset sign, which mean remove all set flag.

        Returns
        -------
            Flag string
        """
        pos_flag = POS_FLAG.join(sorted(map(str, self.__positive_lst)))
        pos_flag = f"{f'{POS_FLAG}{pos_flag}' if pos_flag else ''}"

        neg_flag = NEG_FLAG.join(sorted(map(str, self.__negative_lst)))
        neg_flag = f"{f'{NEG_FLAG}{neg_flag}' if neg_flag else ''}"
        return pos_flag + neg_flag

    def compile_unreset(self) -> str:
        """
        FFmpeg will force remove set flag if flag string start with `+`.

        Returns
        -------
            Flag string without reset(+) sign.
        """
        _flag_compiled = self.compile()

        if _flag_compiled.startswith("+"):
            return _flag_compiled[1:]
        return _flag_compiled

    def add(self, flags: FlagType):
        """Auto split and add flag's correctly position"""
        flags = split_flags(flags)

        for flag in flags:
            sign = POS_FLAG

            if flag.startswith(NEG_FLAG):
                sign = NEG_FLAG
                flag = flag[1:]
            elif flag.startswith(POS_FLAG):
                flag = flag[1:]

            if flag in self.__positive_lst:
                self.__positive_lst.remove(flag)

            if flag in self.__negative_lst:
                self.__negative_lst.remove(flag)

            if not flag:
                raise UnknownFlag(flag)

            if self.limit_list and flag not in self.limit_list:
                raise LimitedFlag(flag, self.limit_list)

            if sign == POS_FLAG:
                self.__positive_lst.append(flag)
            else:
                self.__negative_lst.append(flag)

    def delete(self, flags: FlagType):
        for flag in split_flags(flags):
            self.__delitem__(flag)
