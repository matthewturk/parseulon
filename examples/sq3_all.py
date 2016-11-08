import numpy as np
import matplotlib.pyplot as plt
import parseulon
import yt

m = parseulon.ResourceMapSCI0("SQ3/resource.map")
for rtype in ("view", "picture", "script", "text",
              "sound", "vocab", "font", "cursor", "patch"):
    n = {0:0, 1:0, 2:0}
    for i, v in sorted(getattr(m, rtype).items()):
        n[v.compression_method] += 1
    print "% 10s: % 4i % 4i % 4i % 4i" % (rtype, n[0], n[1], n[2],
        sum(n.values()))
#p = m.picture[1].view
#m.picture[1].view.draw()
for k in []:#sorted(m.picture):
    #if m.picture[k].compression_method != 0:
    #    continue
    if not np.any(m.picture[k].data.view("uint8") == 0xff):
        continue
    n_unk, n_tot = m.picture[k].view.draw()
    print k, n_tot, n_unk/float(n_tot)*100
for k in sorted(m.sound):
    s = m.sound[k].view
    s.parse_events()
    print "Writing", k
    s.write_midi("output/sound_%05i.mid" % k)
