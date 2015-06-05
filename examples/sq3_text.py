import matplotlib.pyplot as plt
import parseulon

m = parseulon.ResourceMapSCI0("SQ3/resource.map")
print m.text[0].data.tostring()
v = m.view[0].view
print v
for i, ic in enumerate(v.cells[0].image_cells):
    plt.clf()
    plt.imshow(ic.im, interpolation="nearest")
    plt.savefig("image_%02i.png" % i)
