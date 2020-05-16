import string
import time
from typing import List


class AbstractModel:
    """
    Each subclass represents a relation (table).
    """
    DB_PATH = str()  # TODO: move it to the settings and settings provider

    WORD_JOINER = str('_')  # string used to concatenate words in the table name and columns names

    # The table name
    _name = None  # type: str
    # The table's columns meta
    _cols = None  # type: List['FieldType']
    # The primary key column meta
    _pk_col = None  # type: 'FieldType'

    def __init__(self):
        self._pk_val = None  # The database's primary key value

    @property
    def pk(self) -> [str, int, float]:
        """
        Return the original frozen primary key value of the instance.
        It changes only after commit.
        :return:
        """
        return self._pk_val

    @pk.setter
    def pk(self, val: [str, int, float]):
        """
        Set the primary key value of the instance.
        It does not affect the original primary key value until a commit.
        :param val:
        :return:
        """
        model = type(self)

        if self._pk_val is None:
            self._pk_val = val

        setattr(self, model.get_pk_col().name, val)

    def save(self, eager=True):
        """
        Insert or update the instance.
        :return:
        """
        from src.core_modules.ORM import QueryBuilder

        model = type(self)

        qb = QueryBuilder(model)
        if self.pk is None:
            qb.insert(self, eager)
        else:
            qb.update(self, eager)
        qb.build().execute()

        last_id = qb.last_id
        if last_id is None or 0 == last_id:  # not synthetic primary key inserted by the user
            self._pk_val = getattr(self, model.get_pk_col().name, None)
        else:  # autoincrement id
            # the model's pk is None
            self.pk = last_id

        return self

    def delete(self, eager=True):
        """
        Delete the instance from the database.
        :return:
        """
        from src.core_modules.ORM import QueryBuilder

        qb = QueryBuilder(type(self))
        qb.delete(self, eager).build().execute()

        self._pk_val = None

        return self

    # TODO: READ (get, select)

    @classmethod
    def create_table(cls, eager=True):
        """
        Create the table that the class represents.
        :param eager: If True, execute statement without 'IF NOT EXISTS'
        :return:
        """
        from src.core_modules.ORM import QueryBuilder

        qb = QueryBuilder(cls)
        qb.create_table(eager).build().execute()

        return cls

    @classmethod
    def get_table_name(cls) -> str:
        """
        Return the table name based on the class name.
        Capital letter will be lowered.
        The first capital letter is simply lowered.
        The other capital letters will be preceded by the word joiner.
        :return: str
        """
        if cls._name is None:
            cls._name = ''.join(
                map(
                    lambda ch: cls.WORD_JOINER + ch.lower() if ch in string.ascii_uppercase else ch.lower(),
                    cls.__name__
                )
            )
            if cls._name.startswith(cls.WORD_JOINER):
                cls._name = cls._name[len(cls.WORD_JOINER):]

        return cls._name

    @classmethod
    def get_cols(cls, eager=False):
        """
        Return the columns of the table.
        !!! A magic method with strong relations !!!
        !!! the method bounds the model class and the property name to the columns !!!
        Field name is a string representing the column.
        Field is an instance of 'FieldType' containing column meta data.
        :param: eager: If true, fetch all related models (as list).
        :return: List['FieldType']
        """
        from src.core_modules.ORM import FieldType, ForeignKey

        if cls._cols is None or eager:
            cls._cols = list()

            # bind the column's name and its model to the field
            for col_name, col_meta in cls.__dict__.items():
                if '_pk_col' == col_name:  # the primary key column alias
                    continue
                if isinstance(col_meta, FieldType):
                    col_meta.model = cls
                    col_meta.name = col_name
                    cls._cols.append(col_meta)

            if not cls._cols:
                cls._cols.append(cls._gen_pk())
            cls._pk_col = cls.get_pk_col()

            if eager:  # present as linear structure
                marker = f'_marked_{int(time.time())}'

                def walker(cols):  # not Johnny
                    for col in cols:
                        if isinstance(col, ForeignKey) and not getattr(col, marker, False):
                            setattr(col, marker, True)
                            yield from walker(col.get_ref().get_cols(eager))
                            delattr(col, marker)
                        else:
                            yield col

                cls._cols = list(walker(cls._cols))

        return cls._cols

    @classmethod
    def get_pk_col(cls):
        """
        Return the primary key column.
        If the primary key is not specified, set the synthetic one.
        :return: 'FieldType'
        """
        if cls._pk_col is None:
            for col in cls.get_cols():
                if col.primary_key:
                    cls._pk_col = col
                    break
            else:
                # the user has not specified a PK field
                # generate a synthetic one
                pk_col = cls._gen_pk()
                if cls._cols is not None:
                    cls._cols.insert(0, pk_col)
                else:
                    cls._cols = [pk_col]
                cls._pk_col = pk_col

        return cls._pk_col

    @staticmethod
    def init_db():
        """
        CREATE DATABASE with tables corresponding to the application.
        :return:
        """
        for model in AbstractModel.__subclasses__():
            if issubclass(model, AbstractModel):
                model.create_table(True)

    @classmethod
    def _gen_pk(cls, name='id'):
        """
        Generate and return the synthetic PK column.
        :param name: Name of the column.
        :return:
        """
        from src.core_modules.ORM import IntegerField

        pk_col = IntegerField(primary_key=True, autoincrement=True)
        pk_col.name = name
        pk_col.model = cls

        return pk_col
