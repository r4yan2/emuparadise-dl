import operator

class MemoryDBM(object):

    def __init__(self):
        self.db = dict()
        self.counter = 1

    def create(self, obj):
        cls = obj.__class__
        self.db[cls] = dict()

    def write(self, obj, item):
        self.db[obj.__class__][self.counter] = item
        self.counter += 1

    def get_results(self, cls):
        return [(fid, *operator.itemgetter('name', 'system', 'size')(rom)) for fid, rom in self.db[cls].items()]

    def query(self, fake_id):
        for backend, values in self.db.items():
            if fake_id in values:
                return backend, values[fake_id]['gid']
        return False, False

