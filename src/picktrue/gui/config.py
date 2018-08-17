import json
import os
from pathlib import Path


class AttrDict(dict):
    """Allows attributes to be bound to and also behaves like a dict"""

    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(r"'AttrDict' object has no attribute '%s'" % attr)

    def __setattr__(self, attr, value):
        self[attr] = value


class ConfigStore(AttrDict):

    _save_file = Path(os.path.expanduser("~/.picktrue-config.json"))

    @classmethod
    def from_config_file(cls):
        path = Path(cls._save_file)
        if not os.path.exists(path):
            return cls()
        with open(path, "rb") as f:
            return cls(**json.load(f))

    def __setattr__(self, key, value):
        super(ConfigStore, self).__setattr__(key, value)
        self._save()

    def _save(self):
        path = Path(self._save_file)
        with open(path, "w") as f:
            json.dump(self, f)

    def op_store_path(self, name, path):
        path = Path(path)
        self[name] = str(path)
        self._save()

    def op_read_path(self, name):
        path = self.get(name, None)
        return Path(path) if path is not None else None


config_store = ConfigStore.from_config_file()
