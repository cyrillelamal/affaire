from typing import Type


from src.core_modules.ORM.field_type import FieldType
from src.core_modules import exceptions

from src.core_modules.ORM.abstract_model import AbstractModel


class IntegerField(FieldType):
    """
    SQLite INTEGER type
    """
    def __init__(self, autoincrement=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.autoincrement = autoincrement

    def get_type(self) -> str:
        return 'INTEGER'

    def to_sql(self) -> str:
        sql = super().to_sql()

        if self.autoincrement:
            props = sql.split(' ')
            if 'PRIMARY' in props and 'KEY' in props:
                props.insert(props.index('KEY') + 1, 'AUTOINCREMENT')
            sql = ' '.join(props)

        return sql.strip()


class RealField(FieldType):
    """
    SQLite REAL type
    """
    def __init__(self, *args,  **kwargs):
        super().__init__(*args, **kwargs)

    def get_type(self) -> str:
        return 'REAL'


class TextField(FieldType):
    """
    SQLite TEXT type
    """
    def __init__(self, datetime=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.datetime = datetime  # apply datetime function while SELECT

    def get_type(self) -> str:
        return 'TEXT'


class BlobField(FieldType):
    """
    SQLite BLOB type
    """
    def get_type(self) -> str:
        return 'BLOB'


class ForeignKey(FieldType):
    """
    Relation field
    """
    CASCADE = 1
    IGNORE = 2

    def __init__(self, ref: [str, AbstractModel], reversed_by=None, on_delete=None, **kwargs):
        """
        Relation field.
        :param ref: Referenced class or its name in CamelCase
        :param reversed_by:
        :param kwargs:
        """
        super().__init__(**kwargs)

        self.reversed_by = reversed_by
        self._ref = ref

        self.on_delete = on_delete

    def get_type(self) -> str:
        return self.get_ref().get_pk_col().get_type()

    def to_sql(self) -> str:
        ref = self.get_ref()

        ref_name = self.get_ref_col_name()

        sql = f'{ref.get_pk_col().get_type()},\n'
        sql += f'CONSTRAINT fk_{ref.get_table_name()}s\n'
        sql += f'FOREIGN KEY ({ref_name})\n'
        sql += f'REFERENCES {ref.get_table_name()}({ref.get_pk_col().name})\n'
        if self.on_delete == ForeignKey.CASCADE:
            sql += 'ON DELETE CASCADE'
        if sql.endswith('\n'):
            sql = sql[:-1]

        return sql

    def get_ref(self) -> Type[AbstractModel]:
        """
        Return model referenced in the field.
        :return: Model
        """
        if isinstance(self._ref, str):
            for cls in AbstractModel.__subclasses__():
                if self._ref == cls.__name__:
                    self._ref = cls
                    break
            else:
                raise exceptions.NoReferencedModelError(f'Model named {self._ref} does not exist')
        elif not issubclass(self._ref, AbstractModel):
            raise TypeError(f'Referenced model expected to be "str" or "Model"')

        # noinspection PyTypeChecker
        return self._ref

    def get_ref_col_name(self):
        """
        Return column name based on the referenced table name and its primary key column.
        :return:
        """
        ref = self.get_ref()
        ref_pk = ref.get_pk_col().name

        return f'{ref.get_table_name()}{AbstractModel.WORD_JOINER}{ref_pk}'
