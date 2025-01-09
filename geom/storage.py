from threading import Lock


class Storage(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Storage, cls).__new__(cls)

        return cls.instance

    def __init__(self):
        self.lock = Lock()
        self.lines = {}
        self.points = {}
        self.constraints = {}

        self.kv_storage_ = {}

    def get(self, key):
        if self.lock.locked():
            raise RuntimeError('storage is busy')
        with self.lock:
            if key in self.__dict__:
                return self.__dict__[key]

            return self.kv_storage_[key]

    def set(self, key, value):
        if self.lock.locked():
            raise RuntimeError('storage is busy')
        with self.lock:
            if key in self.__dict__:
                self.__dict__[key] = value
                return

            self.kv_storage_[key] = value
