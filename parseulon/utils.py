# Some utilities for parsing SCI0 resources

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
    return data

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

def decompress_huffman(data, final_size):
    raise NotImplementedError

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
