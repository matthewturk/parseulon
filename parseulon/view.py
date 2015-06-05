import numpy as np
import struct

class View(object):
    def __init__(self, data):
        self.data = data

class SCI0View(View):
    def __init__(self, data):
        super(SCI0View, self).__init__(data)
        # Now we parse
        sdata = data.tostring()
        self.ngroups, self.bitmask, _ = struct.unpack("<HHI", sdata[:8])
        self.cell_indices = struct.unpack("<%sH" % self.ngroups,
            sdata[8:8+2*self.ngroups])

    def __repr__(self):
        return "%s - %s - %s" % (self.ngroups, self.bitmask, self.cell_indices)
