# Some utilities for parsing SCI0 resources

import struct
import numpy as np
import cStringIO
from yt.utilities.lib.bitarray import bitarray

def get_low_bits(nbits):
    v = 0
    for i in range(nbits):
        v = v << 1
        v |= 1
    return v

def get_high_bits(nbits, ntotal):
    v = get_low_bits(nbits)
    v = v << (ntotal - nbits)
    return v

def bits_to_int(bits):
    # Note that this assumes little endian (I think?)
    ret = 0    
    for i, b in enumerate(bits):
        if not b: continue
        ret |= (1 << i)
    return ret

resource_types = {
    0: "view",
    1: "picture",
    2: "script",
    3: "text",
    4: "sound",
    5: "unused",
    6: "vocab",
    7: "font",
    8: "cursor",
    9: "patch",
}

r_dtype = np.dtype([("rtype", "i4"),
                    ("rnum", "i4"),
                    ("rfile", "i4"),
                    ("roff", "i4")])

def decompress_uncompressed(data, final_size):
    return np.fromstring(data, dtype="c")

def decompress_lzw(data, final_size):
    # Python port of the ScummVM system, which is GPLv2+
    ba = bitarray(size = len(data)*8)
    ba.ibuf.view("c")[:] = np.fromstring(data, dtype="c")
    dest = np.zeros(final_size, dtype="<i1")
    bits = ba.as_bool_array()
    numbits = 9
    c = d = 0
    curtoken = 0x0102
    endtoken = 0x1ff
    tokenlist = {}
    tokenlastlength = 0
    tokenlengthlist = {}
    while not (c == bits.size and d == dest.size):
        token = bits_to_int(bits[c:c+numbits])
        c += numbits
        if token == 0x101:
            return dest
        if token == 0x100:
            numbits = 9
            endtoken = 0x1ff
            curtoken = 0x0102
        else:
            if token > 0xff:
                if token >= curtoken:
                    print "ERROR!  Bad token", token
                    break
                tokenlastlength = tokenlengthlist[token] + 1
                dest[d:d+tokenlastlength] = dest[tokenlist[token]:tokenlist[token]+tokenlastlength]
                d += tokenlastlength
            else:
                tokenlastlength = 1
                dest[d:d+1] = token
                d += 1
            if curtoken > endtoken and numbits < 12:
                numbits += 1
                endtoken = (endtoken << 1) + 1
            if curtoken <= endtoken:
                tokenlist[curtoken] = d - tokenlastlength
                tokenlengthlist[curtoken] = tokenlastlength
                curtoken += 1
    assert(d==dest.size)
    if c != bits.size: print c, bits.size, bits.size - c
    return dest

# http://sci.sierrahelp.com/Documentation/SCISpecifications/10-DecompressionAlgorithms.html#AEN990
class HuffmanBitstream(object):
    def __init__(self, data, final_size):
        n_nodes, self.terminator = struct.unpack("<BB", data[:2])
        dt = np.dtype([ ("value", "c"), ("siblings", "<u1") ])
        info = np.fromstring(data[2:2+n_nodes*2], dtype=dt)
        self.nodes = np.empty(n_nodes, dtype = np.dtype([
          ("value", "c"), ("left", "u1"), ("right", "u1")]))
        self.nodes["value"] = info["value"]
        self.nodes["left"] = (info["siblings"] & get_high_bits(4, 8)) >> 4
        self.nodes["right"] = (info["siblings"] & get_low_bits(4))
        self.data = np.fromstring(data[2+n_nodes*2:], dtype='uint8')
        self.old_position = self.position = 0
        self.bitstream = np.unpackbits(self.data)
        self.output = np.zeros(final_size, dtype='uint8')
    
    def get_next_bit(self):
        tr = self.bitstream[self.position]
        self.old_position = self.position
        self.position += 1
        return tr

    def get_next_byte(self):
        tr = self.bitstream[self.position:self.position+8]
        self.old_position = self.position
        self.position += 8
        tr = np.packbits(tr)
        return tr[0]

    def get_next_char(self):
        index = 0
        node = self.nodes[index]
        while 1:
            if node['left'] == node['right'] == 0:
                break
            if self.get_next_bit():
                next = node['right']
                if next == 0:
                    return self.get_next_byte()
            else:
                next = node['left']
            index += next
            node = self.nodes[index]
        return node['value']

    def decode(self):
        o = self.output.view('c')
        i = 0
        while 1:
            tr = self.get_next_char()
            if tr == self.terminator: break
            # I'm not totally sure how to make this all work together nicely,
            # what with the bitstream and all that.  So, lots of views, I
            # guess.
            o[i] = tr.view('c')
            i += 1
        assert(i == o.size)
        assert(self.bitstream.size - self.position < 8)
        #import pdb;pdb.set_trace()
        return self.output.view('c')

def decompress_huffman(data, final_size):
    # Get the number of nodes and the terminator signal
    hbs = HuffmanBitstream(data, final_size)
    return hbs.decode()

decomp_funcs = {0:decompress_uncompressed, 1:decompress_lzw, 2:decompress_huffman}

ega_palette = {
    0:  (0x00, 0x00, 0x00),
    1:  (0x00, 0x00, 0xAA),
    2:  (0x00, 0xAA, 0x00),
    3:  (0x00, 0xAA, 0xAA),
    4:  (0xAA, 0x00, 0x00),
    5:  (0xAA, 0x00, 0xAA),
    6:  (0xAA, 0x55, 0x00),
    7:  (0xAA, 0xAA, 0xAA),
    8:  (0x55, 0x55, 0x55),
    9:  (0x55, 0x55, 0xFF),
    10: (0x55, 0xFF, 0x55),
    11: (0x55, 0xFF, 0xFF),
    12: (0xFF, 0x55, 0x55),
    13: (0xFF, 0x55, 0xFF),
    14: (0xFF, 0xFF, 0x55),
    15: (0xFF, 0xFF, 0xFF),
}
