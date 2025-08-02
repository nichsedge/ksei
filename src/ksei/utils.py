import json
import os

class FileAuthStore:
    def __init__(self, directory):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def _get_path(self, key):
        return os.path.join(self.directory, f"{key}.json")

    def get(self, key):
        try:
            with open(self._get_path(key), "r") as f:
                return json.load(f)
        except:
            return None

    def set(self, key, value):
        with open(self._get_path(key), "w") as f:
            json.dump(value, f)
