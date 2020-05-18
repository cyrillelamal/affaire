import datetime
from typing import List


from src.core_modules.ORM import AbstractModel
from src.core_modules.ORM.field_types import IntegerField, TextField
from src.core_modules.factories import ModelFactory
from src.core_modules.ORM import QueryBuilder

from src.affaire.exceptions import UnknownParameterException
from src.affaire.exceptions import UndefinedValueException


class Task(AbstractModel):
    """
    Combination of model and repository
    """
    body = TextField()
    created_at = TextField(datetime=True)
    updated_at = TextField(datetime=True)
    expires_at = TextField(datetime=True, not_null=False)
    is_active = IntegerField(default=1, use_default=True)

    def __init__(self):
        super().__init__()
        self.is_active = True

    def save(self, eager=True):
        now = str(datetime.datetime.now())
        self.created_at = now
        self.updated_at = now

        super(Task, self).save(eager)

    @classmethod
    def select(cls, params: dict = None, schema: dict = None) -> List[AbstractModel]:
        """
        Repository: particular realisation
        :param params: Parameters from CLI
        :param schema: args_schema.json -> "params" key
        :return:
        """
        qb = QueryBuilder(cls).select()

        if params is not None and schema is not None:
            for param, val in params.items():  # user's input
                if param == '-f':
                    continue
                for short_arg, props in schema.items():
                    if param in [short_arg, *props.get('aliases')]:
                        field_name = props.get('field', None)
                        if field_name is None:
                            if val is None:
                                raise UndefinedValueException(f'Parameter {param} requires a value')
                        elif field_name in ['is_active']:
                            qb.and_where(field_name, QueryBuilder.EQUALS, 1)
                        else:
                            qb.and_where(field_name, QueryBuilder.LIKE, val)
                        break
                    else:
                        continue
                else:
                    raise UnknownParameterException(f'Unknown parameter {param}')

        qb.build()
        qb.execute()

        task_list = ModelFactory(cls, qb.res).to_list()

        return task_list

    @classmethod
    def update(cls, params: dict):
        pass

    def __str__(self):
        txt = f'{self.body} '
        if self.expires_at is not None:
            txt += f'expires at {self.expires_at}'

        return txt.strip()
