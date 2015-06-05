import parseulon

m = parseulon.ResourceMapSCI0("SQ3/resource.map")
print m.text[0].data.tostring()
print m.view[0].view
