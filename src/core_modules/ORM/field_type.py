import abc


from src.core_modules import exceptions


class FieldType:
    def __init__(self, primary_key=False, not_null=True, unique=False, default=None, use_default=False):
        self.primary_key = primary_key

        if primary_key:
            not_null = True
            unique = True
            use_default = False

        if unique:
            use_default = False

        self.not_null = not_null
        self.unique = unique
        self.default = default
        self.use_default = use_default

        self._name = None
        self.model = None  # type: 'AbstractModel'

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val: str):
        self._name = val

    @abc.abstractmethod
    def get_type(self) -> str:
        """
        Return the SQL type of the column
        :return: str
        """
        pass

    def to_sql(self) -> str:
        """
        Return SQL representation of the field without field name,
        e.g. 'INTEGER PRIMARY KEY AUTOINCREMENT' or 'TEXT NOT NULL', etc.
        :return: str
        """
        sql = f'{self.get_type()} '

        if self.primary_key:
            sql += 'PRIMARY KEY '
        if self.not_null and not self.primary_key:
            sql += 'NOT NULL '
        if self.use_default:
            default_val = self.default
            if default_val is None:
                default_val = 'NULL'
                if self.not_null:
                    raise exceptions.NotNullableFieldException('Default value "NULL" provided for not nullable field')
            elif isinstance(default_val, str):
                default_val = f"'{default_val}'"
            sql += f'DEFAULT {default_val}'

        return sql.strip()
