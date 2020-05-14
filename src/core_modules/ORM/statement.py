from typing import List


class Statement:
    SELECT = 1
    WHERE = 2
    LIMIT = 4
    OFFSET = 8
    JOIN = 16
    ORDER = 32
    CREATE_TABLE = 64

    def __init__(self, *terms: str, final=False, type_=None):
        self.terms = [*terms]  # type: List[str]
        self.params = list()

        self.final = final  # followed by ';'

        self.type = type_

    def to_sql(self) -> str:
        sql = str()

        for term in self.terms:
            term = term.strip()
            sql += ' ' + term

        return sql
