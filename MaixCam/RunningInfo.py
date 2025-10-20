from enum import Enum

class RunMode(Enum):
    STOP = 0
    RUN = 1
    DEBUG = 2

class RunningInfo:
    _instance = None


    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RunningInfo, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.data = {}
        self._initialized = True
        self.run_mode = RunMode.STOP

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = RunningInfo()
        return cls._instance