import numpy as np
import struct
from .utils import ega_palette
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Some magic numbers:
DRAW_ENABLE_VISUAL   = 1
DRAW_ENABLE_PRIORITY = 2
DRAW_ENABLE_CONTROL  = 4

PATTERN_FLAG_RECTANGLE   = 0x10
PATTERN_FLAG_USE_PATTERN = 0x20

default_palette = np.array(
     [(0x0,0x0), (0x1,0x1), (0x2,0x2), (0x3,0x3), (0x4,0x4), (0x5,0x5),
      (0x6,0x6), (0x7,0x7), (0x8,0x8), (0x9,0x9), (0xa,0xa), (0xb,0xb),
      (0xc,0xc), (0xd,0xd), (0xe,0xe), (0x8,0x8), (0x8,0x8), (0x0,0x1),
      (0x0,0x2), (0x0,0x3), (0x0,0x4), (0x0,0x5), (0x0,0x6), (0x8,0x8),
      (0x8,0x8), (0xf,0x9), (0xf,0xa), (0xf,0xb), (0xf,0xc), (0xf,0xd),
      (0xf,0xe), (0xf,0xf), (0x0,0x8), (0x9,0x1), (0x2,0xa), (0x3,0xb),
      (0x4,0xc), (0x5,0xd), (0x6,0xe), (0x8,0x8)], dtype="uint8")

opcode_names = {0xf0: 'PIC_OP_SET_COLOR',
                0xf1: 'PIC_OP_DISABLE_VISUAL',
                0xf2: 'PIC_OP_SET_PRIORITY',
                0xf3: 'PIC_OP_DISABLE_PRIORTY',
                0xf4: 'PIC_OP_RELATIVE_PATTERNS',
                0xf5: 'PIC_OP_RELATIVE_MEDIUM_LINES',
                0xf6: 'PIC_OP_RELATIVE_LONG_LINES',
                0xf7: 'PIC_OP_RELATIVE_SHORT_LINES',
                0xf8: 'PIC_OP_FILL',
                0xf9: 'PIC_OP_SET_PATTERN',
                0xfa: 'PIC_OP_ABSOLUUTE_PATTERNS',
                0xfb: 'PIC_OP_SET_CONTROL',
                0xfc: 'PIC_OP_DISABLE_CONTROL',
                0xfd: 'PIC_OP_RELATIVE_MEDIUM_PATTERNS',
                0xfe: 'PIC_OP_OPX',
                0xff: 'END_OPCODE'}

ega_opcode_names = {
    0: "PIC_OPX_EGA_SET_PALETTE_ENTRIES",
    1: "PIC_OPX_EGA_SET_PALETTE",
    2: "PIC_OPX_EGA_MONO0",
    3: "PIC_OPX_EGA_MONO1",
    4: "PIC_OPX_EGA_MONO2",
    5: "PIC_OPX_EGA_MONO3",
    6: "PIC_OPX_EGA_MONO4",
    7: "PIC_OPX_EGA_EMBEDDED_VIEW",
    8: "PIC_OPX_EGA_SET_PRIORITY_TABLE"
}

class StreamProcessor(object):
    def __init__(self, data):
        self.index = 0
        self.data = data.view("u1")

    def peek(self):
        return self.data[self.index]

    def get(self):
        d = self.data[self.index]
        self.index += 1
        return d

    def skip(self, n):
        self.index += n

class Picture(object):
    def __init__(self, data, aspect = 320.0/200):
        self.data = data
        self.aspect = aspect
        self.axes = {}
        self.figures = {}

    def get_abs_coordinates(self, stream):
        coordinate_prefix = stream.get()
        x = stream.get()
        y = stream.get()
        x |= (coordinate_prefix & 0xf0) << 4
        y |= (coordinate_prefix & 0x0f) << 8
        return (x,y)

    def get_rel_coordinates(self, x, y, stream):
        input = stream.get()
        if input & 0x80:
            x -= (input >> 4)
        else:
            x += (input >> 4)
        
        if input & 0x08:
            y -= input & 0x7
        else:
            y += input & 0x7
        return (x,y)

    def draw(self):
        # Set up a new stream
        stream = StreamProcessor(self.data)
        # Some default variables
        drawenable = DRAW_ENABLE_VISUAL | DRAW_ENABLE_PRIORITY
        priority = 0
        col1 = col2 = 0
        control = 0
        pattern_nr = 0
        pattern_code = 0
        pattern_size = 0
        fill_in_black = 0
        # Now we get our new axes
        for c in ("visual", "control", "priority", "aux"):
            self.figures[c] = plt.figure(figsize = (10.0*self.aspect, 10.0))
            self.axes[c] = self.figures[c].add_axes([0.0, 0.0, 1.0, 1.0])
            self.axes[c].set_xlim(0, 320)
            self.axes[c].set_ylim(0, 200)
        #self.axes["visual"][:] = 0xf

        # We mandate a break later on, but a string overrun will also do it via
        # an exception.
        n_unk = 0
        n_tot = 0
        opcodes = []
        bads = []
        while 1:
            n_tot += 1
            opcode = stream.get()
            opcodes.append((opcode, stream.index-1))
            #print opcode_names.get(opcode, "UNKNOWN: %s" % (hex(opcode)))
            if opcode == 0xf0:
                # PIC_OP_SET_COLOR
                code = stream.get()
                #col1, col2 = palette[default_palette[int(code/40)]][code % 40]
                drawenable |= DRAW_ENABLE_VISUAL
            elif opcode == 0xf1:
                # PIC_OP_DISABLE_VISUAL
                drawenable &= ~DRAW_ENABLE_VISUAL
            elif opcode == 0xf2:
                # PIC_OP_SET_PRIORITY
                code = stream.get()
                priority = code & 0xf
                drawenable |= DRAW_ENABLE_PRIORITY
            elif opcode == 0xf3:
                # PIC_OP_DISABLE_PRIORITY
                drawenable &= ~DRAW_ENABLE_PRIORITY
            elif opcode == 0xf4:
                # PIC_OP_RELATIVE_PATTERNS
                if pattern_code & PATTERN_FLAG_USE_PATTERN:
                    pattern_nr = (stream.get() >> 1) & 0x7f
                x, y = self.get_abs_coordinates(stream)
                self.draw_pattern(x, y, col1, col2, priority, control,
                        drawenable,
                        pattern_code & PATTERN_FLAG_USE_PATTERN,
                        pattern_size, pattern_nr,
                        pattern_code & PATTERN_FLAG_RECTANGLE)
                while stream.peek() < 0xf0:
                    if pattern_code & PATTERN_FLAG_USE_PATTERN:
                        pattern_nr = (stream.get() >> 1) & 0x7f
                    x, y = self.get_rel_coordinates(x, y, stream)
                    self.draw_pattern(x, y, col1, col2, priority, control,
                            drawenable,
                            pattern_code & PATTERN_FLAG_USE_PATTERN,
                            pattern_size, pattern_nr,
                            pattern_code & PATTERN_FLAG_RECTANGLE)
            elif opcode == 0xf5:
                # PIC_OP_RELATIVE_MEDIUM_LINES
                oldx, oldy = self.get_abs_coordinates(stream)
                while stream.peek() < 0xf0:
                    temp = stream.get()
                    if temp & 0x80:
                        y = oldy - (temp & 0x7f)
                    else:
                        y = oldy + temp
                    x = oldx + stream.get()
                    self.dither_line(oldx, oldy, x, y, col1, col2, priority,
                            control, drawenable)
                    oldx, oldy = x, y
            elif opcode == 0xf6:
                # PIC_OP_RELATIVE_LONG_LINES
                oldx, oldy  = self.get_abs_coordinates(stream)
                while stream.peek() < 0xf0:
                    x, y = self.get_abs_coordinates(stream)
                    self.dither_line(oldx, oldy, x, y, col1, col2, priority,
                            control, drawenable)
                    oldx, oldy = x, y
            elif opcode == 0xf7:
                # PIC_OP_RELATIVE_SHORT_LINES
                oldx, oldy = self.get_abs_coordinates(stream)
                while stream.peek() < 0xf0:
                    x, y = self.get_rel_coordinates(oldx, oldy, stream)
                    self.dither_line(oldx, oldy, x, y, col1, col2, priority,
                            control, drawenable)
                    oldx, oldy = x, y
            elif opcode == 0xf8:
                # PIC_OP_FILL
                if fill_in_black:
                    oldc1, oldc2 = c1, c2
                while stream.peek() < 0xf0:
                    x, y = self.get_abs_coordinates(stream)
                    self.dither_fill(x, y, col1, col2, priority, control,
                            drawenable)
                if fill_in_black:
                    c1, c2 = oldc1, oldc2
            elif opcode == 0xf9:
                # PIC_OP_SET_PATTERN
                #import pdb;pdb.set_trace()
                pattern_code = stream.get() #& 0x37
                pattern_size = pattern_code & 0x07
                print "PATTERN CODE", pattern_code, pattern_size
            elif opcode == 0xfa:
                # PIC_OP_ABSOLUTE_PATTERNS
                while stream.peek() < 0xf0:
                    if (pattern_code & PATTERN_FLAG_USE_PATTERN):
                        pattern_nr = (stream.get() >> 1) & 0x7f
                    x, y = self.get_abs_coordinates(stream)
                    self.draw_pattern(x, y, col1, col2, priority, control,
                            drawenable,
                            pattern_code & PATTERN_FLAG_USE_PATTERN,
                            pattern_size, pattern_nr,
                            pattern_code & PATTERN_FLAG_RECTANGLE)
            elif opcode == 0xfb:
                # PIC_OP_SET_CONTROL
                control = stream.get() & 0x0f
                drawenable |= DRAW_ENABLE_CONTROL
            elif opcode == 0xfc:
                # PIC_OP_DISABLE_CONTROL
                drawenable &= ~DRAW_ENABLE_CONTROL
            elif opcode == 0xfd:
                # PIC_OP_RELATIVE_MEDIUM_PATTERNS
                if pattern_code & PATTERN_FLAG_USE_PATTERN:
                    pattern_nr = (stream.get() >> 1) & 0x7f
                oldx, oldy = self.get_abs_coordinates(stream)
                self.draw_pattern(oldx, oldy, col1, col2, priority, control,
                        drawenable,
                        pattern_code & PATTERN_FLAG_USE_PATTERN,
                        pattern_size, pattern_nr,
                        pattern_code & PATTERN_FLAG_RECTANGLE)
                while stream.peek() < 0xf0:
                    if pattern_code & PATTERN_FLAG_USE_PATTERN:
                        pattern_nr = (stream.get() >> 1) & 0x7f
                    temp = stream.get()
                    if temp & 0x80:
                        y = oldy - (temp & 0x7f)
                    else:
                        y = oldy + temp
                    x = oldx + stream.get()
                    self.draw_pattern(x, y, col1, col2, priority, control,
                                      drawenable,
                                      pattern_code & PATTERN_FLAG_USE_PATTERN,
                                      pattern_size, pattern_nr,
                                      pattern_code & PATTERN_FLAG_RECTANGLE);

            elif opcode == 0xfe:
                # PIC_OP_OPX
                temp = stream.get()
                if temp == 0x00:
                    # PIC_OPX_SET_PALETTE_ENTRY
                    while stream.peek() < 0xf0:
                        index = stream.get()
                        color = stream.get()
                        #palette[index / 40][color % 40] = color
                elif temp == 0x01:
                    # PIC_OPX_SET_PALETTE
                    palette_number = stream.get()
                    for i in range(40):
                        stream.get()
                        #palette[palette_number][i] = stream.get()
                elif temp == 0x02:
                    # PIC_OPX_MONO0
                    stream.skip(41)
                elif temp == 0x03:
                    # PIC_OPX_MONO1
                    stream.skip(1)
                elif temp == 0x04:
                    # PIC_OPX_MONO2
                    pass
                elif temp == 0x05:
                    # PIC_OPX_MONO3
                    stream.skip(1)
                elif temp == 0x06:
                    # PIC_OPX_MONO4
                    pass
                elif temp == 0x07:
                    # PIC_OPX_EMBEDDED_VIEW
                    pass
                elif temp == 0x08:
                    # PIC_OPX_SET_PRIORITY_TABLE
                    for i in range(14):
                        stream.get()
                else:
                    pass
            elif opcode == 0xff:
                break
            else:
                n_unk += 1
                bads.append(opcode)
        return n_unk, n_tot

    def draw_pattern(self, x, y, col1, col2, priority, control, drawenable,
            use_pattern, pattern_size, pattern_nr, rectangle = True):
        to_draw = []
        if drawenable & DRAW_ENABLE_VISUAL:
            to_draw.append(self.axes["visual"])
        if drawenable & DRAW_ENABLE_PRIORITY:
            to_draw.append(self.axes["priority"])
        if drawenable & DRAW_ENABLE_CONTROL:
            to_draw.append(self.axes["control"])
        print "Drawing on %s from %s to %s" % (len(to_draw), (x, y),
                pattern_size)
        for ax in to_draw:
            # Alters (x,y) so that 0 <= (x - pattern_size), 319 >= (x +
            # pattern_size), 189 >= (y + pattern_size) and 0 <= (y -
            # pattern_size), then draws a rectangle or a circle filled with
            # col1, col2, priority, control, as determined by drawenable.  If
            # rectangle is not set, it will draw a rectangle, otherwise a
            # circle of size pattern_size.  pattern_nr is used to specify the
            # start index in the random bit table (256 random bits)
            if rectangle:
                patch = patches.Rectangle((x, y), 2*pattern_size+1,
                        pattern_size*2+2,
                        color = 'k')
                print patch
            else:
                patch = patches.Circle((x, y), pattern_size, alpha=0.3,
                        color='k')
            ax.add_patch(patch)

    def save(self, fn):
        for n, f in sorted(self.figures.items()):
            f.savefig(fn + n + ".png")

    def dither_line(self, *args, **kwargs):
        pass

    def dither_fill(self, *args, **kwargs):
        pass

class SCI0Picture(Picture):
    def __init__(self, data):
        # http://sci.sierrahelp.com/Documentation/SCISpecifications/16-SCI0-SCI01PICResource.html
        super(SCI0Picture, self).__init__(data)
