# This parses a resource map file

import os
import numpy as np
from .utils import resource_types, r_dtype, get_high_bits, get_low_bits

class ResourceMap:
    offset = 0
    _dtype_def = None
    def __init__(self, filename):
        if self._dtype_def is None:
            raise RuntimeError("This class should not be instantiated
                directly.")
        self.dtype = np.dtype(self._dtype_def)
        if filename.lower().endswith("resource.map"):
            self.filename = filename
        else:
            filename = os.path.join(filename, "resource.map")
        if not os.path.isfile(self.filename):
            raise IOError(filename)
        self.resources = {}

        for rtype, rname in resource_types.items():
            self.resources[rtype] = self.resources[rname] = {}
            setattr(self, rname, self.resources[rname])

    def parse(self):
        with open(self.filename, "rb") as f:
            f.seek(self.offset)
            arr = np.fromfile(f, dtype=self.dtype)
        return arr

class ResourceMapSCI0(ResourceMap):
    _dtype_def = (("rinfo", "<i2"), ("rindex", "<i4"))

    def parse(self):
        arr = super(ResourceMapSCI0, self).parse()
        self.info = np.empty(arr.size, dtype=r_dtype)
        self.info["rtype"][:] = (arr['rinfo'] & get_high_bits(5, 16) ) >> 11
        self.info["rnum"][:] = arr['rinfo'] & get_low_bits(11)
        self.info["rfile"][:] = (arr['rindex'] & get_high_bits(6, 32)) >> 26
        self.info["roff"][:] = arr['rindex'] & get_low_bits(26)
