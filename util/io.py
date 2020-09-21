
import os
import subprocess


class Subprocess(subprocess.Popen):
    PIPE = subprocess.PIPE

    def read(self, chunk_size=-1):
        if self.poll() is not None:
            raise RuntimeError(f"Process closed - code {self.returncode}")

        output_bytes = self.stdout.read(chunk_size)

        if output_bytes.__len__() > 0:
            return output_bytes

        outputs, errs = self.communicate()
        if outputs is None and not errs:
            raise RuntimeError(f"Process closed - code {self.returncode}")

        if errs:
            raise RuntimeError(f"Read error - code {self.returncode}:", errs)
        return outputs

    def write(self, data):
        if self.stdin is None:
            raise RuntimeError(f"Stdin in't existed!")
        if self.stdin.closed:
            raise RuntimeError(f"Process closed - code {self.returncode}")
        self.stdin.write(data)

    def is_alive(self):
        ret_code = self.poll()
        return ret_code is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.kill()


class FileWritable(object):
    def __init__(self, file_name, ext=None, prefix=None, postfix=None, force_ext=False, over_write=False,
                 mode="r", buffering=None, encoding=None, errors=None, newline=None, closefd=True):
        self.__prefix = prefix
        self.__postfix = postfix

        if not ext:
            *name, ext = file_name.split(".")
            if len(name) == 0:
                if not force_ext:
                    raise ValueError("Can't found extension")
                else:
                    name = name.append(ext)
                    ext = None

            self.name = '.'.join(name)
            self.ext = ext
        else:
            self.name = file_name
            self.ext = ext

        if os.path.isfile(self.path) and not over_write:
            raise FileExistsError(self.path)

        self.mode = mode
        self.buffering = buffering
        self.encoding = encoding
        self.errors = errors
        self.newline = newline
        self.closefd = closefd
        self.file = None

    def open(self):
        if self.file is not None:
            raise RuntimeError("File already open!")
        self.file = open(self.path, self.mode, self.buffering, self.encoding, self.errors, self.newline, self.closefd)

    @property
    def prefix(self):
        if hasattr(self.__prefix, "__call__"):
            return self.__prefix()
        if self.__prefix is None:
            return ""
        return self.__prefix

    @prefix.setter
    def prefix(self, _prefix):
        self.__prefix = _prefix

    @property
    def postfix(self):
        if hasattr(self.__postfix, "__call__"):
            return self.__postfix()
        if self.__postfix is None:
            return ""
        return self.__postfix

    @postfix.setter
    def postfix(self, _postfix):
        self.__postfix = _postfix

    @property
    def path(self):
        return f"{self.prefix}{self.name}{self.postfix}{f'.{self.ext}' if self.ext else ''}"

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def write(self, s):
        self.file.write(s)

    def close(self):
        self.file.close()

    def reopen(self):
        self.close()
        self.open()
