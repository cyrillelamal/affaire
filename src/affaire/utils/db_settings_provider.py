import json
import sqlite3


from src.core_modules.utils import SettingsProviderInterface
from src.core_modules.utils import Connection


# noinspection SqlResolve
class DBSettingsProvider(SettingsProviderInterface):
    """
    Load settings from the database.
    Save settings in the database.
    """
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
                cur.execute('SELECT "settings"."settings" FROM "settings" WHERE "settings"."id"=1 LIMIT 1')
                res = json.loads(cur.fetchone()[0])
            except sqlite3.OperationalError:
                raise Exception('TODO: db is not specified')  # TODO: db is not specified
            except json.decoder.JSONDecodeError:
                raise Exception('TODO: incorrect settings format')  # TODO: incorrect settings format

            return res

    def dump_settings(self, settings: dict):
        """
        Update settings in the application database.
        :return:
        """
        with Connection(self._db_path, True) as cur:
            cur.execute('UPDATE "settings" SET "settings"= ? WHERE id=1', (json.dumps(settings), ))
