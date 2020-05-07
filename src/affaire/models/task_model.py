import datetime
from typing import List

from src.core_modules.abstract_model import AbstractModel
from src.core_modules.field_types import IntegerField, TextField
from src.core_modules.query_builder import QueryBuilder


class Task(AbstractModel):
    """
    Combination of model and repository
    """
    # id = IntegerField(primary_key=True, autoincrement=True)
    body = TextField()
    created_at = TextField(datetime=True)
    updated_at = TextField(datetime=True)
    expires_at = TextField(datetime=True)
    is_active = IntegerField()

    @classmethod
    def select(cls, params: dict) -> List[AbstractModel]:
        pass

    @classmethod
    def update(cls, params: dict):
        pass

    def __str__(self):
        txt = f'{self.body} '
        if self.expires_at is not None:
            txt += f'expires at {self.expires_at}'

        return txt.strip()
