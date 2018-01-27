class MaxList(list):
    """A list that will pop the lowest index on adding an item which exceeds the max size"""
    

    def __init__(self, max_size):
        self.max_size = max_size

    def append(self, item):
        if len(self) < self.max_size:
            super(MaxList, self).append(item)
        else:
            del self[0]
            super(MaxList, self).append(item)
