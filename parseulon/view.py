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
        # These are composed of cells, each of which has image cells in it.
        # So, let's split up the strings.
        self.cells = []
        # This next little bit is because sometimes start indices are
        # duplicated, particularly when things are reversed.
        end_indices = list(set(self.cell_indices + (len(sdata),)))
        end_indices.sort()
        for start_index in self.cell_indices:
            ei = end_indices.index(start_index) + 1
            self.cells.append(sdata[start_index:end_indices[ei]])

    def __repr__(self):
        return "%s - %s - %s" % (self.ngroups, self.bitmask, self.cell_indices)
