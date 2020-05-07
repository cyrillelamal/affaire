import json
import os
import sqlite3


from src.core_modules.utils.settings_provider_interface import SettingsProviderInterface
from src.core_modules.utils.connection import Connection


class DBSettingsProvider(SettingsProviderInterface):
    """
    Load settings from the database.
    Save settings in the database.
    """
    DEFAULT_SETTINGS = 'default_settings.json'

    def __init__(self, db_path: str):
        self._db_path = db_path

    def load_settings(self) -> dict:
        """
        Load settings from the application database.
        The action can overwrite the current settings.
        :return:
        """
        with Connection(self._db_path, False) as cur:
            try:
                cur.execute('SELECT "settings"."settings" FROM "settings" LIMIT 1')
                res = json.loads(cur.fetchone()[0])
            except sqlite3.OperationalError:
                res = self.load_fallback_settings()
            except json.decoder.JSONDecodeError:
                raise Exception('TODO: incorrect settings format')  # TODO: incorrect settings format

            return res

    def dump_settings(self, settings: dict):
        """
        Update settings in the application database.
        :return:
        """
        with Connection(self._db_path, True) as cur:
            cur.execute('UPDATE "settings" SET "settings"= ?', json.dumps(settings))

    def load_fallback_settings(self) -> dict:
        """
        Create the table with the settings.
        Insert default setting in the table.
        :return:
        """
        with Connection(self._db_path, True) as cur:
            cur.execute('CREATE TABLE "settings" ("settings" TEXT PRIMARY KEY)')

        dir_name = os.path.dirname(self._db_path)  # at main.py level
        settings_file = os.path.join(dir_name, self.DEFAULT_SETTINGS)
        with open(settings_file, 'rt') as f:
            settings = json.loads(f.read())

        with Connection(self._db_path, True) as cur:
            cur.execute('INSERT INTO "settings" ("settings") VALUES (?)', (json.dumps(settings), ))

        return settings
