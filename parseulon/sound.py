import numpy as np
import struct
import midi

Events = midi.events.EventRegistry.Events

status_codes = {
        0x80: ("NOTE_OFF", 2),
        0x90: ("NOTE_ON", 2),
        0xA0: ("KEY_PRESSURE", 2),
        0xB0: ("CONTROL", 2),
        0xC0: ("PROGRAM", 1),
        0xD0: ("PRESSURE", 1),
        0xE0: ("PITCH_WHEEL", 2),
        0xF0: ("SYSTEM_DATA_START", 0),
        0xF7: ("SYSTEM_DATA_STOP", 0),
        0xFC: ("STOP", 0)
}

class Sound(object):
    def __init__(self, data):
        self.events = []
        self.data = data.view("u1")
        self.digital_sample = self.data[0]
        self.initialization = {}
        for i in range(16):
            self.initialization[i] = self.data[1+i*2:1+i*2+2]
        self.eventstream = self.data[33:]

    def parse_events(self):
        i = 0
        while self.eventstream[i] != 0xfc:
            delay = 0
            while 1:
                delay += self.eventstream[i]
                if self.eventstream[i] != 0xf8:
                    i += 1
                    break
                i += 1
            # Only if the first bit is set do we do anything
            if (self.eventstream[i] & 128):
                e = self.eventstream[i]
                if e == 0xfc:
                    print i
                    break
                channel = e & 0x0f
                status = e & 0xf0
                name, nb = status_codes[status]
                i += 1
            if not name.startswith("SYSTEM_DATA"):
                self.events.append(
                    Events[status](tick = delay, channel=channel,
                        data = self.eventstream[i:i+nb]))
            i += nb

    def write_midi(self, fn):
        pattern = midi.Pattern()
        track = midi.Track()
        pattern.append(track)
        for e in self.events:
            track.append(e)
        eot = midi.EndOfTrackEvent(tick=1)
        track.append(eot)
        midi.write_midifile(fn, pattern)

class SCI0Sound(Sound):
    def __init__(self, data):
        super(SCI0Sound, self).__init__(data)
