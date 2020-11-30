import os
import subprocess
from multiprocessing.queues import Queue
from threading import Thread


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

    def __repr__(self):
        return " ".join(self.args)


class NonBlockSubprocess(object):
    CHUNK_SIZE_DEFAULT = 4096
    STOP_THREAD = b"STOP_THREAD_SYNTAX"

    """
    NonBlockSubprocess support read, write data via Queue.

    Parameters
    ----------
    process: Subprocess
        Sub process still alive

    chunk_size: int
        Size of chunk of reader process. (Default) CHUNK_SIZE_DEFAULT=4096

    Raises
    ---------
    ValueError:
        chunk size <= 0. Because read process will blocking if chunk_size <= 0.

    TypeError:
        process wrong type.

    RuntimeError:
        Process haven't any IO.
    """

    def __init__(self, process: Subprocess, chunk_size=CHUNK_SIZE_DEFAULT):
        if not isinstance(process, Subprocess):
            raise TypeError("process must be Subprocess")

        if not process.is_alive():
            raise ValueError("Process wasn't working.")

        if chunk_size <= 0:
            raise ValueError("Chunk size must be > 0.")

        if self.process.stdout is None and self.process.stdin is None:
            raise RuntimeError("Process IO are unavailable.")

        self.process = process
        self.chunk_size = chunk_size
        self.read_buffer_cache = b""

        if self.process.stdin is not None:
            self.queue_write = Queue()
            self.thread_write = Thread(target=self._write)
            self.thread_write.start()
        else:
            self.queue_write = None
            self.thread_write = None

        if self.process.stdout is not None:
            self.queue_read = Queue()
            self.thread_read = Thread(target=self._read)
            self.thread_read.start()
        else:
            self.queue_read = None
            self.thread_read = None

    def _write(self):
        if self.queue_write is None:
            return

        while 1:
            data = self.queue_write.get()
            if data == self.STOP_THREAD:
                break

            self.process.write(data)

    def write(self, data):
        if self.queue_write is None:
            raise AttributeError("Write data unavailable!")

        self.queue_write.put(data)

    def _read(self):
        if self.queue_read is None:
            return

        while 1:
            data = self.process.read(self.chunk_size)
            self.queue_read.put(data)

    def read(self, chunk_size=-1, timeout=None):
        """
        Read
        :param chunk_size:
        :param timeout:
        :return:
        """
        if self.queue_read is None:
            raise AttributeError("Read data unavailable!")

        chunk = self.read_buffer_cache
        while chunk.__len__() < chunk_size:
            chunk += self.queue_read.get(timeout=timeout)

        if chunk.__len__() > chunk_size:
            self.read_buffer_cache = chunk[chunk_size:]
            chunk = chunk_size[:chunk_size]
        return chunk

    def stop(self):
        """
        Stop read/write via queue. Not handle process.
        :return:
        """
        if self.queue_read is not None:
            self.queue_read.put(self.STOP_THREAD)

        if self.queue_write is not None:
            self.queue_read.put(self.STOP_THREAD)

        self.process.terminate()


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
