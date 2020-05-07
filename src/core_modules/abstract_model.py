import string
import collections
import sqlite3
from typing import List

from src.core_modules import AbstractController
# from src.core_modules import QueryBuilder

Column = collections.namedtuple('Field', ['field_name', 'field'])


class AbstractModel:
    """
    Abstract.
    The class represents a relation (table).
    """
    WORD_JOINER = '_'  # string used to concatenate words in the table name

    _table_name = None  # table name based on the class name: count once
    _table_cols = None  # type: List[Column]
    _pk_field = None  # column name used as primary key: count once

    @classmethod
    def get(cls, pk_val: [str, int, float] = None) -> list:
        """
        SELECT
        :param pk_val:
        :return:
        """
        pass

    def save(self):
        pass  # TODO: implement

    def delete(self, pk_val: [int, str] = None):
        """
        Delete the instance from the database. Either the current instance or via query.
        :param pk_val: If some value is provided, delete the corresponding instance without fetching it.
        :return:
        """
        cls = type(self)

        table_name = cls.get_table_name()
        pk_field = cls.get_pk_field().field_name

        if pk_val is None:
            # remove the current (fetched) instance
            pk_val = getattr(self, pk_field)
            # else remove via query

        sql = f'DELETE FROM "{table_name}" WHERE "{pk_field}"=?'

        con = sqlite3.connect(AbstractController.db_path)
        cur = con.cursor()
        cur.execute(sql, (pk_val,))
        cur.close()
        con.close()

    @classmethod
    def get_table_name(cls) -> str:
        """
        Return the table name based on the class name.
        Capital letter will be lowered.
        The first capital letter is simply lowered.
        The other capital letters will be preceded by the word joiner.
        :return: str
        """
        if cls._table_name is None:
            cls._table_name = ''.join(
                map(
                    lambda ch: cls.WORD_JOINER + ch.lower() if ch in string.ascii_uppercase else ch.lower(),
                    cls.__name__
                )
            )
            if cls._table_name.startswith(cls.WORD_JOINER):
                cls._table_name = cls._table_name[len(cls.WORD_JOINER):]

        return cls._table_name

    @classmethod
    def get_cols(cls) -> List[Column]:
        """
        Return the columns of the table.
        Field name is a string representing the column.
        Field is an instance of 'FieldType' containing column meta data.
        :param: eager: bool If true, fetch all related models.
        :return: List[Column]
        """
        from src.core_modules.field_type import FieldType  # cyclic import resolving

        if cls._table_cols is None:
            cls._table_cols = [
                Column(field_name=key, field=val)
                for key, val in cls.__dict__.items()
                if isinstance(val, FieldType)
            ]
            if len(cls._table_cols) == 0:  # specify the PK column at least
                cls._table_cols.append(cls._gen_pk_field())

        # if eager:
        #     def walker(cols):  # not Johnny
        #         for col in cols:
        #             if isinstance(col.field, ForeignKey) and not getattr(col.field, 'marked', False):
        #                 setattr(col.field, 'marked', True)
        #                 yield from walker(col.field.get_ref().get_cols())
        #                 setattr(col.field, 'marked', False)
        #             else:
        #                 yield col
        #     return list(walker(cls._table_cols))

        return cls._table_cols

    @classmethod
    def get_pk_field(cls) -> Column:
        """
        Return the primary key column.
        If the primary key is not specified, set the synthetic one ('id').
        :return: Column
        """
        if cls._pk_field is None:
            for col in cls.get_cols():
                if col.field.primary_key:
                    cls._pk_field = col
                    break
            else:
                # the user has not specified a PK field
                # generate a synthetic one
                cls._pk_field = cls._gen_pk_field()

        return cls._pk_field

    @classmethod
    def to_sql(cls):
        """
        Return SQL creating the corresponding table.
        :return: str
        """
        sql = f'CREATE TABLE IF NOT EXISTS {cls.get_table_name()} (\n' \
              + ',\n'.join(f'{col.field_name} {col.field.to_sql()}' for col in cls.get_cols()) \
              + '\n)'

        return sql

    @classmethod
    def _gen_pk_field(cls, name='id') -> Column:
        """
        Return the synthetic PK column.
        :param name: Name of the column.
        :return: Column
        """
        from src.core_modules.field_types import IntegerField

        return Column(field_name=name, field=IntegerField(primary_key=True, autoincrement=True))
