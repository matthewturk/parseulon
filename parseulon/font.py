import numpy as np
import struct
from .utils import get_low_bits, get_high_bits
from yt.utilities.lib.bitarray import bitarray


class Font(object):
    def __init__(self, data):
        self.data = data

class SCI0Font(Font):
    def __init__(self, data):
        super(SCI0Font, self).__init__(data)
        sdata = data.tostring()
        _, self.num_char, self.height = struct.unpack("<HHH", sdata[:6])
        self.char_locations = struct.unpack("<%sH" % self.num_char,
            sdata[6:6+2*self.num_char])
        self.char_bitmaps = {}
        pointers = [cl for cl in self.char_locations] + [len(sdata)]
        for i, (si, ei) in enumerate(zip(pointers[:-1], pointers[1:])):
            self._parse_char(i, sdata[si:ei])

    def _parse_char(self, ci, data):
        height, width = struct.unpack("<BB", data[:2])
        bm_h = height
        bm_w = int(np.ceil(width / 8.0) * 8)
        ba = bitarray(size = bm_h*bm_w*8)
        ba.ibuf.view("c")[:] = data[2:2+bm_h*bm_w]
        bitmask = ba.as_bool_array().reshape((bm_w, 8*bm_h), order="F")
        self.char_bitmaps[ci] = bitmask[:width,:height][::-1,:]

    def montage(self):
        w = sum(c.shape[0] + 1 for c in self.char_bitmaps.values())
        h = max(c.shape[1] for c in self.char_bitmaps.values())
        arr = np.zeros((w, h), dtype="uint8")
        x = 0
        for ci in sorted(self.char_bitmaps):
            c = self.char_bitmaps[ci]
            arr[x:x + c.shape[0], :c.shape[1]] = c
            x += c.shape[0] + 1
        return arr
