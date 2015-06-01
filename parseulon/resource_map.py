# This parses a resource map file

import os
import numpy as np
from .utils import resource_types, r_dtype, get_high_bits, get_low_bits
from .resource import ResourceEntry

class ResourceMap(object):
    offset = 0
    _dtype_def = None
    def __init__(self, filename):
        if self._dtype_def is None:
            raise RuntimeError("This class should not be instantiated"
                "directly.")
        self.dtype = np.dtype(self._dtype_def)
        if filename.lower().endswith("resource.map"):
            self.filename = filename
        else:
            self.filename = os.path.join(filename, "resource.map")
        if not os.path.isfile(self.filename):
            raise IOError(self.filename)
        self.resources = {}

        self.parse()
        self.resource_files = {}
        for i in sorted(np.unique(self.info["rfile"])):
            fn, _ = self.filename.rsplit(".", 1)
            self.resource_files[i] = open(fn + ".%03i" % i, "rb")

        for rtype, rname in resource_types.items():
            self.resources[rtype] = self.resources[rname] = {}
            setattr(self, rname, self.resources[rname])
            ind = (self.info["rtype"] == rtype)
            for rec in self.info[ind]:
                self.resources[rtype][rec["rnum"]] = ResourceEntry(
                    self, rec["rnum"], rtype, rec["rfile"], rec["roff"])

    def parse(self):
        with open(self.filename, "rb") as f:
            f.seek(self.offset)
            arr = np.fromfile(f, dtype=self.dtype)
        return arr

class ResourceMapSCI0(ResourceMap):
    _dtype_def = [("rinfo", "<i2"), ("rindex", "<i4")]

    def parse(self):
        arr = super(ResourceMapSCI0, self).parse()
        # Last entry is empty, to indicate the end
        info = np.empty(arr.size, dtype=r_dtype)
        info["rtype"][:] = (arr['rinfo'] & get_high_bits(5, 16) ) >> 11
        info["rnum"][:] = arr['rinfo'] & get_low_bits(11)
        info["rfile"][:] = (arr['rindex'] & get_high_bits(6, 32)) >> 26
        info["roff"][:] = arr['rindex'] & get_low_bits(26)
        self.info = info[:-1]
