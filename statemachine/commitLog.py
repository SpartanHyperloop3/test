import copy

class commitLog(object):
    """Data structure that allows append only operations
    
    The commitLog is a list that limits the addition of new data
    to being appended to the end of the list. This ensures that the
    data at the end of the list is always the most current with respect
    to time.
    """
    def __init__(self,maxSize):
        self.data = []
        self.maxSize = maxSize

    def append(self, data):
        if len(self.data)/self.maxSize > 0:
            del self.data[:]
        self.data.append(copy.deepcopy(data))

    def retrieveMostCurrentEntry(self):
        if (len(self.data) - 1) >= 0:
            return self.data[len(self.data)-1]

    def retrieveEntryByOffset(self,offset):
        if offset >= len(self.data) or (offset < 0):
           return "Index Outside of Range"
        return self.data[offset]

    def retrieveMostCurrentIndex(self):
        return (len(self.data) - 1)
