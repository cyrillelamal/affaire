import json
import os


from src.core_modules.utils import SettingsProviderInterface


class JSONSettingsProvider(SettingsProviderInterface):
    """
    Load and dump the settings into the JSON-file
    """
    FALLBACK_JSON_PATH = None

    def __init__(self, settings_path: str, fallback_json_path: str = None):
        self._settings_path = settings_path
        if fallback_json_path is not None:
            JSONSettingsProvider.FALLBACK_JSON_PATH = fallback_json_path

    def load_settings(self) -> dict:
        if os.path.exists(self._settings_path):
            file_path = self._settings_path
        elif JSONSettingsProvider.FALLBACK_JSON_PATH is not None:
            file_path = JSONSettingsProvider.FALLBACK_JSON_PATH
        else:
            raise FileNotFoundError(f'Neither "settings" nor "fallback settings" files are not provided')

        with open(file_path, 'rt') as f:
            return json.loads(f.read())

    def dump_settings(self, settings: dict):
        with open(self._settings_path, 'wt') as f:
            f.write(json.dumps(settings))
