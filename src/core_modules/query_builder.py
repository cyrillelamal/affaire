from typing import List


from src.core_modules import AbstractModel


class QueryBuilder:
    """
    Chained query builder
    """
    class CLAUSES:
        LIKE = 'LIKE'
        IN = 'IN'
        EQUAL = '='

    class CONSTS:
        ASC = "ASC"
        DESC = "DESC"

    def __init__(self, model: type(AbstractModel)):
        self.model = model

        self._sql = ''

    def select_all(self):
        self._sql += 'SELECT '

        return self

    def where(self, param: [str, AbstractModel], predicate: str, term: [str, AbstractModel]):
        return self

    def and_where(self):
        pass

    def limit(self, limit: int):
        return self

    def order(self, by: str, order=None):
        return self

    def build(self):
        return self

    def execute(self):
        return self

    def fetch(self) -> List[AbstractModel]:
        pass
