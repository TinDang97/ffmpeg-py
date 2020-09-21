from util import cvt_str2hex, cvt_byte2str, cvt_bin2hex


class Serializer:
    def __init__(self, func_serializer=None, prefix=None):
        if func_serializer and not hasattr(func_serializer, "__call__"):
            raise ValueError("Not find callable of serializer!")
        self.func_serializer = func_serializer

        if prefix and not isinstance(prefix, (bytes, str)):
            raise ValueError("Prefix must be binary!")

        self.prefix = prefix
        if type(self.prefix) is str:
            self.prefix = cvt_str2hex(self.prefix)
        else:
            try:
                cvt_byte2str(self.prefix)
            except ValueError:
                pass
            else:
                self.prefix = cvt_bin2hex(self.prefix)

        if not self.prefix:
            self.prefix = b""

    def __call__(self, _data):
        if self.func_serializer:
            binary = self.func_serializer(_data)
        else:
            binary = _data

        return self.prefix + binary


class Deserializer:
    def __init__(self, func_deserializer=None, prefix=None):
        if func_deserializer and not hasattr(func_deserializer, "__call__"):
            raise ValueError("Not find callable of deserializer!")
        self.func_deserializer = func_deserializer

        if prefix and not isinstance(prefix, (bytes, str)):
            raise ValueError("Prefix must be binary!")

        self.prefix = prefix
        if type(self.prefix) is str:
            self.prefix = cvt_str2hex(self.prefix)
        else:
            try:
                cvt_byte2str(self.prefix)
            except ValueError:
                pass
            else:
                self.prefix = cvt_bin2hex(self.prefix)

        if not self.prefix:
            self.prefix = b""

    def __call__(self, binary):
        if self.prefix and self.prefix != binary[:self.prefix.__len__()]:
            raise ValueError("Prefix isn't correctly!")
        binary = binary[self.prefix.__len__():]

        if self.func_deserializer:
            _data = self.func_deserializer(binary)
        else:
            _data = binary
        return _data
