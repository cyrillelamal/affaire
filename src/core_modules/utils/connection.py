import sqlite3


class Connection:
    """
    Sqlite3 connection context
    """
    # instance's properties
    _con = None  # type: sqlite3.Connection
    _cur = None  # type: sqlite3.Cursor

    def __init__(self, db_path: str, commit=True):
        self._db_path = db_path
        self.commit = commit

    def __enter__(self) -> sqlite3.Cursor:
        self._con = sqlite3.connect(self._db_path)
        self._cur = self._con.cursor()

        return self._cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.commit:
            self._con.commit()

        self._cur.close()
        self._con.close()
