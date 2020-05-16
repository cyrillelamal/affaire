from typing import List, Type


from src.core_modules.ORM import Statement
from src.core_modules.utils import Connection
from src.core_modules.ORM.exceptions import UndefinedFieldException
from src.core_modules.ORM.exceptions import EmptyQueryException
from src.core_modules.ORM.exceptions import SQLSyntaxError


# noinspection SqlResolve
class QueryBuilder:
    """
    Chained query builder
    """
    from src.core_modules.ORM import AbstractModel
    from src.core_modules.ORM import FieldType

    # predicates
    EQUALS = '='
    LIKE = 'LIKE'
    IN = 'IN'
    IS = 'IS'

    # sorting predicates
    ASC = "ASC"
    DESC = "DESC"

    # response types
    RES_ALL = 1
    RES_ROW = 2

    def __init__(self, model: [AbstractModel, Type[AbstractModel]]):
        from src.core_modules.ORM import AbstractModel

        self._script = False  # run as script

        if isinstance(model, AbstractModel):
            model = type(model)
        self.model = model  # type: Type[AbstractModel]

        # SQL statements to be concatenated and executed
        self.stmts = list()  # type: List[Statement]

        self.sql = str()
        self.params = list()

        # the last inserted id
        self._last_id = None
        # the fetched response
        self._res = None  # type: [list, tuple]

        # the response type
        self._res_type = None

    def create_table(self, eager=True):
        """
        CREATE TABLE statement for the 'model' property.
        :param eager: If True, execute without 'IF NOT EXISTS'
        :return:
        """
        from src.core_modules.ORM import FieldType, ForeignKey

        sql = 'CREATE TABLE '

        if not eager:
            sql += 'IF NOT EXISTS '

        sql += f'"{self.model.get_table_name()}" (\n'

        for col in self.model.get_cols():
            # if isinstance(col, ForeignKey)
            #     col_name
            if not isinstance(col, FieldType):  # PyCharm type hinting
                continue
            elif isinstance(col, ForeignKey):
                # chain the referenced model name and its primary key column name
                col_name = col.get_ref_col_name()
            else:
                col_name = col.name
            sql += f'"{col_name}" {col.to_sql()},\n'

        if sql.endswith(',\n'):
            sql = sql[:-2]

        sql += '\n)'

        if sql.endswith('(\n\n)'):
            raise SQLSyntaxError('Tables must contain at least one column')

        stmt = Statement(sql, final=True, type_=Statement.CREATE_TABLE)
        self.stmts.append(stmt)

        return self

    def insert(self, inst: AbstractModel, eager=True):
        """
        INSERT statement
        :param inst: Model instance to be inserted
        :param eager: If True, insert or update all nested models
        :return:
        """
        from src.core_modules.ORM import FieldType
        from src.core_modules.ORM import IntegerField
        from src.core_modules.ORM import ForeignKey
        from src.core_modules.ORM import AbstractModel

        table_name = self.model.get_table_name()

        sql = f'INSERT INTO "{table_name}" ('
        params = list()  # to be escaped

        for col in self.model.get_cols():
            if not isinstance(col, FieldType):  # PyCharm type hinting
                continue
            elif isinstance(col, ForeignKey):  # recursive saving
                ref_inst = getattr(inst, col.name)
                if not isinstance(ref_inst, AbstractModel):  # The related model is not provided
                    continue
                if eager:  # proceed recursive saving
                    ref_inst.save(eager)
                col_name = col.get_ref_col_name()
                col_val = ref_inst.pk
            else:  # the recursion's base case
                col_name = col.name
                col_val = getattr(inst, col_name, None)
                if isinstance(col, IntegerField):
                    if col.autoincrement:
                        continue
            # the column must be inserted
            if col_val is None or isinstance(col_val, FieldType):
                # either default value of forgotten value
                if col.not_null and not col.use_default:
                    raise UndefinedFieldException(f'Column "{col_name}" requires a value')
                # continue  # ' INSERT INTO "book" () VALUES ()'
                col_val = None

            sql += f'"{col_name}", '
            params.append(col_val)

        if sql.endswith(', '):
            sql = sql[:-2]

        sql += ') VALUES ('

        sql += '?, ' * len(params)
        if sql.endswith(', '):
            sql = sql[:-2]

        sql += ')'

        if '()' in sql:
            if not self.model.get_pk_col().autoincrement:
                raise EmptyQueryException(f'The query does not contain columns or values')

        stmt = Statement(sql, final=True)
        stmt.params.extend(params)
        self.stmts.append(stmt)
        self.params.extend(params)

        return self

    def update(self, inst: AbstractModel, eager=True):
        from src.core_modules.ORM import FieldType
        from src.core_modules.ORM import ForeignKey
        from src.core_modules.ORM import AbstractModel

        sql = f'UPDATE "{self.model.get_table_name()}"\nSET '
        params = list()

        for col in self.model.get_cols():
            if not isinstance(col, FieldType):  # PyCharm type hinting
                continue
            elif isinstance(col, (ForeignKey, AbstractModel)):
                ref_inst = getattr(inst, col.name, None)
                if eager:
                    if ref_inst is None:
                        continue
                    elif isinstance(ref_inst, AbstractModel):
                        ref_inst.save(eager)
                    else:
                        continue  # TODO: check if the referenced model is bound via the correct primary key value
                col_name = col.get_ref_col_name()
                param = ref_inst.pk if ref_inst is not None else None
            else:
                col_name = col.name
                param = getattr(inst, col_name)
                if isinstance(param, FieldType):  # empty value
                    param = None
            sql += f'"{col_name}"=?, '
            params.append(param)

        if sql.endswith(', '):
            sql = sql[:-2] + '\n'

        pk_col_name = self.model.get_pk_col().name
        sql += f'WHERE "{pk_col_name}"=?'
        params.append(inst.pk)

        stmt = Statement(sql, final=True)  # TODO: not final (WHERE clause)
        stmt.params.extend(params)
        self.stmts.append(stmt)
        self.params.extend(params)

        return self

    def delete(self, inst: AbstractModel, eager=True):
        from src.core_modules.ORM import ForeignKey
        from src.core_modules.ORM import AbstractModel

        cols = self.model.get_cols()
        table_name = self.model.get_table_name()
        pk_col_name = self.model.get_pk_col().name
        pk_val = inst.pk

        sql = f'DELETE FROM "{table_name}" WHERE "{pk_col_name}"=?'

        if eager:
            for ref_col in filter(lambda col: isinstance(col, ForeignKey), cols):
                ref_inst = getattr(inst, ref_col.name, None)
                if isinstance(ref_inst, AbstractModel):
                    ref_inst.delete()

        params = [pk_val]

        stmt = Statement(sql, final=True)  # TODO: not final (WHERE clause)
        stmt.params.extend(params)
        self.stmts.append(stmt)
        self.params.extend(params)

        return self

    def select(self):
        """
        SELECT statement.
        Create two parts of the statement: {SELECT, FROM}.
        :return:
        """
        from src.core_modules.ORM import FieldType, ForeignKey
        from src.core_modules.ORM import AbstractModel

        sql = 'SELECT '

        cols = self.model.get_cols(False)
        for col in cols:
            if not isinstance(col, FieldType) and not isinstance(col.model, AbstractModel):
                raise TypeError(f'Unsupported type of the column {col}')
            elif isinstance(col, ForeignKey):
                col_name = f'{col.get_ref_col_name()}'
            else:
                col_name = col.name
            sql += f'"{self.model.get_table_name()}"."{col_name}", '

        if sql.endswith(', '):
            sql = sql[:-2]
        else:
            sql += '*'

        sql += '\n'

        stmt = Statement(sql, final=False, type_=Statement.SELECT)

        sql = f'FROM "{self.model.get_table_name()}"\n'

        stmt.terms.append(sql)
        self.stmts.append(stmt)  # SELECT
        self._res_type = self.RES_ALL

        return self

    def where(self, param: [str, FieldType], predicate: str, term: [str, int, float, bool, AbstractModel]):
        """
        WHERE statement.
        :param param: The left term
        :param predicate: The predicate
        :param term: The right term
        :return:
        """
        from src.core_modules.ORM import AbstractModel

        col_name = self._ensure_col_name(param)

        if isinstance(term, AbstractModel):
            term = term.pk
        if term is None:
            predicate = self.IS

        sql = f'WHERE "{col_name}" {predicate} ?'
        if predicate == self.LIKE:
            term = '%' + term + '%'
        params = [term]

        stmt = Statement(sql, final=False, type_=Statement.WHERE)
        stmt.params.extend(params)

        self.stmts.append(stmt)
        self.params.extend(params)

        return self

    def and_where(self, param: [str, FieldType], predicate: str, term: [str, int, float, bool, AbstractModel]):
        """
        AND statement in WHERE clause.
        The base WHERE clause must append one statement and one parameter!
        :param param: The left term
        :param predicate: The predicate
        :param term: The right term
        :return:
        """
        try:
            prev_type = self.stmts[-1].type  # [-2]
        except IndexError:
            raise SQLSyntaxError('Unexpected "WHERE" statement')

        self.where(param, predicate, term)

        if prev_type == Statement.WHERE:
            # the parameter is the same as delegated to the base 'WHERE'
            last_stmt = self.stmts[-1]
            sql = last_stmt.terms[0]
            sql = 'AND ' + sql.replace('WHERE', '').strip()
            last_stmt.terms[0] = sql

        return self

    def or_where(self, param: [str, FieldType], predicate: str, term: [str, int, float, bool, AbstractModel]):
        """
        OR statement in WHERE clause.
        The base WHERE clause must append one statement and one parameter!
        :param param: The left term
        :param predicate: The predicate
        :param term: The right term
        :return:
        """
        self.where(param, predicate, term)

        # the parameter is the same as delegated to the base WHERE
        last_stmt = self.stmts[-1]
        sql = last_stmt.terms[0]
        sql = 'OR ' + sql.replace('WHERE', '')
        last_stmt.terms[0] = sql

        return self

    def limit(self, limit: int):
        """
        LIMIT statement.
        :param limit: Number of selected rows
        :return:
        """
        sql = f'LIMIT ?'
        params = [limit]

        stmt = Statement(sql, final=False, type_=Statement.LIMIT)
        stmt.params = params

        self.stmts.append(stmt)
        self.params.extend(params)

        if 1 == limit:
            self._res_type = self.RES_ROW
        else:
            self._res_type = self.RES_ALL

        return self

    def offset(self, offset: int):
        """
        OFFSET statement.
        :param offset: Number of columns to be truncated
        :return:
        """
        sql = f'OFFSET ?'
        params = [offset]

        stmt = Statement(sql, final=False, type_=Statement.OFFSET)
        stmt.params = params

        self.stmts.append(stmt)
        stmt.params = params
        self.params.extend(params)
        self._res_type = self.RES_ALL

        return self

    def order(self, by: [str, FieldType], order='ASC'):
        """
        ORDER BY statement.
        :param by: The column (name) by which is ordered the query
        :param order: Type of ordering
        :return:
        """
        if order not in [self.ASC, self.DESC]:
            raise SQLSyntaxError(f'Unexpected ORDER type {order}')

        col_name = self._ensure_col_name(by)

        sql = f'ORDER BY {col_name} {order}'

        stmt = Statement(sql, final=True, type_=Statement.ORDER)
        self.stmts.append(stmt)

        return self

    # TODO: JOIN

    def build(self):
        """
        Prepare statements to be executed
        :return:
        """
        sql = str()
        params = list()

        i = 0
        while i < len(self.stmts):
            stmt = self.stmts[i]
            if stmt.final:
                # the single statement without concatenations
                sql += stmt.to_sql()
                params.extend(stmt.params)
                i += 1
            else:
                # terms = stmt.terms
                try:
                    next_stmt = self.stmts[i + 1]
                    if next_stmt.type & (Statement.WHERE | Statement.LIMIT | Statement.OFFSET | Statement.ORDER):
                        sql += stmt.to_sql()
                        params.extend(stmt.params)
                        i += 1
                    elif next_stmt.type == Statement.JOIN:
                        pass  # TODO: join
                except IndexError:
                    sql += stmt.to_sql()
                    params.extend(stmt.params)
                    i += 1

        self.sql = sql
        self.params = params

        return self

    def execute(self):
        """
        Execute the accumulated statements
        :return:
        """
        from src.core_modules.ORM.field_types import IntegerField

        last_id = None

        with Connection(self.model.DB_PATH, True) as cur:
            if self.script:
                cur.executescript(self.sql)
            else:
                cur.execute(self.sql, tuple(self.params))
                pk_col = self.model.get_pk_col()

                if self._res_type is not None:
                    self._res = self._fetch(cur)

                if isinstance(pk_col, IntegerField):
                    if pk_col.autoincrement:
                        last_id = cur.lastrowid

        self._destructor()
        self._last_id = last_id

        return self

    @property
    def script(self):
        return self._script

    @property
    def last_id(self):
        """
        Last inserted id
        :return:
        """
        return self._last_id

    @property
    def res(self):
        """
        Response
        :return:
        """
        return self._res

    def _ensure_col_name(self, col_name: [str, FieldType]) -> str:
        """
        Return the column named if its exist in the model
        :param col_name:
        :return:
        """
        from src.core_modules.ORM import FieldType, ForeignKey

        # the user provides the column's meta
        if isinstance(col_name, FieldType):
            if isinstance(col_name, ForeignKey):
                col_name = col_name.get_ref_col_name()
            else:
                col_name = col_name.name
        # the user provides the column name
        elif isinstance(col_name, str):
            for col_meta in self.model.get_cols(False):
                if isinstance(col_meta, ForeignKey):
                    if col_name == col_meta.get_ref_col_name():
                        break
                elif isinstance(col_meta, FieldType):
                    if col_name == col_meta.name:
                        break
                else:
                    continue
            else:
                raise SQLSyntaxError(f'The field {col_name} is not defined in the model')
        else:
            raise TypeError(f'Unsupported type of term "{col_name}" ({type(col_name)}')

        return col_name

    def _fetch(self, cur):
        if self._res_type == self.RES_ALL:
            return cur.fetchall()
        elif self._res_type == self.RES_ROW:
            return cur.fetchone()

    def _destructor(self):
        """
        Additional after-scrip logic
        :return:
        """
        self.stmts.clear()
        self.params.clear()
        self.sql = str()
