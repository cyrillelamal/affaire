import json


from src.core_modules.utils import SettingsProviderInterface


class JSONSettingsProvider(SettingsProviderInterface):
    """
    Load and dump the settings into the JSON-file
    """
    def __init__(self, settings_path: str):
        self._settings_path = settings_path

    def load_settings(self) -> dict:
        with open(self._settings_path, 'rt') as f:
            return json.loads(f.read())

    def dump_settings(self, settings: dict):
        with open(self._settings_path, 'wt') as f:
            f.write(json.dumps(settings))
