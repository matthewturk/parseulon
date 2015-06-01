import weakref

class Resource:
    decomp_size = 0
    comp_size = 0
    comp_method = 0
    data = None

    def __init__(self, resource_map, r_id, r_type, file_id, offset):
        # We store a proxy to the resource_map so we can both avoid cyclic
        # collection *and* use its file handles.
        self.resource_map = weakref.proxy(resource_map)
        self.r_id = r_id
        self.r_type = r_type
        self.file_id = file_id
        self.offset = offset

    def parse(self):
        # Here we actually load up ...
        pass
