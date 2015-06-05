import numpy as np
import struct
from .utils import get_low_bits, get_high_bits, ega_palette

class View(object):
    def __init__(self, data):
        self.data = data

class SCI0View(View):
    def __init__(self, data):
        # http://sci.sierrahelp.com/Documentation/SCISpecifications/14-SCI0%20View%20Resource.html
        super(SCI0View, self).__init__(data)
        # Now we parse
        sdata = data.tostring()
        self.n_groups, self.bitmask, _ = struct.unpack("<HHI", sdata[:8])
        self.cell_indices = struct.unpack("<%sH" % self.n_groups,
            sdata[8:8+2*self.n_groups])
        # These are composed of cells, each of which has image cells in it.
        # So, let's split up the strings.
        self.cells = []
        # This next little bit is because sometimes start indices are
        # duplicated, particularly when things are reversed.
        end_indices = list(set(self.cell_indices + (len(sdata),)))
        end_indices.sort()
        for start_index in self.cell_indices:
            ei = end_indices.index(start_index) + 1
            cell = SCI0CellList(sdata[start_index:end_indices[ei]],
                                    start_index)
            self.cells.append(cell)

    def __repr__(self):
        return "%s - %s - %s" % (self.n_groups, self.bitmask, self.cell_indices)

class SCI0CellList(object):
    def __init__(self, data, offset):
        # Alright!  Parse the cell!
        n_cells, _ = struct.unpack("<HH", data[:4])
        pointers = [i - offset for i in struct.unpack("<%sH" % n_cells,
                     data[4:4+2*n_cells])]
        pointers.append(len(data))
        self.image_cells = []
        for si, ei in zip(pointers[:-1], pointers[1:]):
            self.image_cells.append(SCI0ImageCell(data[si:ei]))

class SCI0ImageCell(object):
    def __init__(self, data):
        nx, ny, x_off, y_off, c_key = struct.unpack("<HHbbB", data[:7])
        draw_info = np.fromstring(data[7:], "<i1")
        repeats = (draw_info & get_high_bits(4, 8)) >> 4
        colors = (draw_info & get_low_bits(4))
        im_r = np.zeros(nx*ny, dtype="uint8")
        im_g = np.zeros(nx*ny, dtype="uint8")
        im_b = np.zeros(nx*ny, dtype="uint8")
        im_a = np.zeros(nx*ny, dtype="uint8")
        cur_pos = 0
        for c, r in zip(colors, repeats):
            if c == c_key:
                im_a[cur_pos:cur_pos + r] = 0
            else:
                im_r[cur_pos:cur_pos + r] = ega_palette[c][0]
                im_g[cur_pos:cur_pos + r] = ega_palette[c][1]
                im_b[cur_pos:cur_pos + r] = ega_palette[c][2]
                im_a[cur_pos:cur_pos + r] = 255
            cur_pos += r
        self.im = np.array(
            [im.reshape((nx, ny), order="F")
             for im in (im_r, im_g, im_b, im_a)]).transpose()
