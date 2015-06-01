from .utils import decomp_funcs, resource_types
import weakref
import struct

class ResourceEntry(object):
    decomp_size = 0
    comp_size = 0
    comp_method = 0
    _data = None

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

    def load(self):
        # Here we actually load up the data.
        f = self.resource_map.resource_files[self.file_id]
        f.seek(self.offset)
        fmt = "<4H"
        data = f.read(struct.calcsize(fmt))
        rinfo, comp_size, decomp_size, method = struct.unpack(fmt, data)
        comp_size -= 4 # 4 byte offset due to header inclusion
        self.compression_method = method
        self.compressed_size = comp_size
        self.decompress_size = decomp_size
        data = f.read(comp_size)
        self._data = decomp_funcs[self.compression_method](data, decomp_size)

    def __repr__(self):
        return "Resource: %s - %s" % (resource_types[self.r_type], self.r_id)


