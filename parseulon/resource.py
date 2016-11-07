from .utils import decomp_funcs, resource_types
from .view import SCI0View
from .font import SCI0Font
from .picture import SCI0Picture
import weakref
import struct

class ResourceEntry(object):
    _data = None
    _compression_method = None
    _compressed_size = None
    _decompressed_size = None

    def __init__(self, resource_map, r_id, r_type, file_id, offset):
        # We store a proxy to the resource_map so we can both avoid cyclic
        # collection *and* use its file handles.
        self.resource_map = weakref.proxy(resource_map)
        self.r_id = r_id
        self.r_type = r_type
        self.file_id = file_id
        self.offset = offset

    @property
    def data(self):
        if self._data is None:
            self.load()
        return self._data

    @property
    def compression_method(self):
        if self._compression_method is None:
            self.load()
        return self._compression_method

    @property
    def compressed_size(self):
        if self._compressed_size is None:
            self.load()
        return self._compressed_size

    @property
    def decompressed_size(self):
        if self._decompressed_size is None:
            self.load()
        return self._decompressed_size

    def load(self):
        # Here we actually load up the data.
        f = self.resource_map.resource_files[self.file_id]
        f.seek(self.offset)
        fmt = "<4H"
        data = f.read(struct.calcsize(fmt))
        rinfo, comp_size, decomp_size, method = struct.unpack(fmt, data)
        comp_size -= 4 # 4 byte offset due to header inclusion
        self._compression_method = method
        self._compressed_size = comp_size
        self._decompressed_size = decomp_size
        data = f.read(comp_size)
        try:
            self._data = decomp_funcs[self.compression_method](data, decomp_size)
        except NotImplementedError:
            self._data = None

    @property
    def view(self):
        if resource_types[self.r_type] == "text":
            return self.data.tostring()
        elif resource_types[self.r_type] == "view":
            return SCI0View(self.data)
        elif resource_types[self.r_type] == "font":
            return SCI0Font(self.data)
        elif resource_types[self.r_type] == "picture":
            return SCI0Picture(self.data)
        else:
            raise NotImplementedError

    def __repr__(self):
        return "Resource %s: %s (%s vs %s, via %s)" % (self.r_id, resource_types[self.r_type],
                                                       self.compressed_size,
                                                       self.decompressed_size,
                                                       self.compression_method)
