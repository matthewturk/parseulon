class View(object):
    def __init__(self, data):
        self.data = data

class SCI0View(View):
  def __init__(self, data):
        super(SCI0View, self).__init__(data)
        # Now we parse
