from typing import Type

from src.core_modules.field_type import FieldType
from src.core_modules import exceptions


from src.core_modules.abstract_model import AbstractModel


class IntegerField(FieldType):
    """
    SQLite INTEGER type.
    """
    def __init__(self, autoincrement=False, **kwargs):
        super().__init__(**kwargs)
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
    SQLite REAL type.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_type(self) -> str:
        return 'REAL'


class TextField(FieldType):
    """
    SQLite TEXT type.
    """
    def __init__(self, datetime=False, **kwargs):
        super().__init__(**kwargs)

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
    Relation field.
    """
    def __init__(self, ref: [str, AbstractModel], reversed_by=None, **kwargs):
        """
        Relation field.
        :param ref:
        :param reversed_by:
        :param kwargs:
        """
        super().__init__(**kwargs)

        self.reversed_by = reversed_by
        self._ref = ref

    def get_type(self) -> str:
        return self.get_ref().get_pk_field().field.get_type()

    def to_sql(self) -> str:
        ref = self.get_ref()
        # noinspection PyTypeChecker
        if not issubclass(ref, AbstractModel):
            raise TypeError

        ref_pk = ref.get_pk_field().field_name

        col_name = f'{ref.get_table_name()}{AbstractModel.WORD_JOINER}{ref_pk}'

        sql = f'{col_name} {super().to_sql()}'

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
