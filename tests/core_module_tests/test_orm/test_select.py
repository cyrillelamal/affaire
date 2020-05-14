import os
import sqlite3
import unittest
import time
import random
from collections import namedtuple


from src.core_modules.ORM import QueryBuilder
from src.core_modules.ORM import AbstractModel
from src.core_modules.ORM import field_types as ft


User = namedtuple('User', ['last_name', 'first_name', 'dob'])


class TestSelect(unittest.TestCase):
    DB_PATH = './test.db'
    NUM_OF_BOOKS = 5
    NUM_OF_USERS = 4

    def setUp(self) -> None:
        AbstractModel.DB_PATH = self.DB_PATH

        class Book(AbstractModel):
            id = ft.IntegerField(primary_key=True, autoincrement=True)
            desc = ft.TextField(not_null=False)
            owner = ft.ForeignKey('User', not_null=False)

        class User(AbstractModel):
            last_name = ft.TextField(primary_key=True)  # dummy
            first_name = ft.TextField(not_null=False)
            dob = ft.TextField(datetime=True)

        QueryBuilder(Book).create_table(True).build().execute()
        QueryBuilder(User).create_table(True).build().execute()

        self.book = Book
        self.user = User

        self.b = Book()
        self.u = User()
        self.b.desc = 'Book description'
        self.b.owner = self.u
        self.u.last_name = 'John'
        self.u.dob = '93'

        qb = QueryBuilder(Book).insert(self.b, True).build().execute()
        self.b.pk = qb.last_id
        for i in range(self.NUM_OF_BOOKS):
            QueryBuilder(self.book).insert(self.book()).build().execute()
        self.total_books = self.NUM_OF_BOOKS + 1

        self.con = sqlite3.connect(AbstractModel.DB_PATH)

    def tearDown(self) -> None:
        self.con.close()
        AbstractModel.DB_PATH = None
        os.remove(self.DB_PATH)

    def test_select_all(self):
        cur = self.con.cursor()

        cur.execute('SELECT * FROM "book"')
        rows = cur.fetchall()
        self.assertEqual(self.total_books, len(rows))

        qb = QueryBuilder(self.book).select().build()
        sql = qb.sql
        params = qb.params
        self.assertIn('SELECT', sql)
        self.assertIn('"book"', sql)
        self.assertNotIn('WHERE', sql)
        self.assertFalse(params)

        qb.execute()  # sqlite3.OperationalError: no such column: book.id
        res = qb.res
        self.assertTrue(res)
        self.assertIsInstance(res, list)
        for test_row, row in zip(res, rows):
            for test_col, col in zip(test_row, row):
                self.assertEqual(test_col, col)

        cur.close()

    def test_select_where(self):
        cur = self.con.cursor()
        cur.execute('SELECT * FROM "book" WHERE "id"=?', (1, ))
        book_row = cur.fetchone()

        qb = QueryBuilder(self.book).select().where(self.book.get_pk_col(), QueryBuilder.EQUALS, 1).build()
        sql = qb.sql
        params = qb.params
        self.assertIn('SELECT', sql)
        self.assertIn('"book"', sql)
        self.assertIn('WHERE', sql)
        self.assertIn('=', sql)
        self.assertIn(self.b.pk, params)

        qb.execute()
        res = qb.res
        self.assertIsInstance(res, list)
        row = res[0]
        for book_col, col in zip(book_row, row):
            self.assertEqual(book_col, col)

        cur.close()

    def test_where_null(self):
        cur = self.con.cursor()

        cur.execute('SELECT * FROM "book" WHERE "desc" IS NULL')
        # self.NUM_OF_BOOKS because of empty description
        qb = QueryBuilder(self.book).select().where(self.book.desc, QueryBuilder.IS, None).build()
        sql = qb.sql
        self.assertIn('IS', sql)

        qb.execute()
        res = qb.res
        self.assertEqual(self.NUM_OF_BOOKS, len(res))

        cur.close()

    def test_where_and(self):
        cur = self.con.cursor()

        cur.execute('SELECT * FROM "book"')
        book_row = cur.fetchone()
        where, and_where = 1, 'Book description'

        qb = QueryBuilder(self.book).select()\
            .where('id', '=', where)\
            .and_where('desc', '=', and_where)\
            .build()
        sql = qb.sql
        self.assertIn('AND', sql)
        params = qb.params
        self.assertIn(where, params)
        self.assertIn(and_where, params)

        qb.execute()
        res = qb.res
        self.assertTrue(res)
        row = res[0]

        for book_col, col in zip(book_row, row):
            self.assertEqual(book_col, col)

        and_where += f'{int(time.time())}'
        qb = QueryBuilder(self.book).select() \
            .where('id', '=', where) \
            .and_where('desc', '=', and_where) \
            .build()
        self.assertIn(and_where, qb.params)

        qb.execute()
        res = qb.res
        self.assertFalse(res)

        cur.close()

    def test_where_or(self):
        cur = self.con.cursor()
        where, or_where = 1, None

        qb = QueryBuilder(self.book).select() \
            .where('id', '=', where) \
            .or_where('desc', QueryBuilder.IS, or_where) \
            .build()
        sql = qb.sql
        self.assertIn('IS', sql)
        params = qb.params
        self.assertIn(where, params)
        self.assertIn(or_where, params)

        qb.execute()
        res = qb.res
        self.assertTrue(res)
        self.assertEqual(self.NUM_OF_BOOKS + 1, len(res))

        cur.close()

    def test_limit(self):
        qb = QueryBuilder(self.book).select().limit(1).build()
        sql = qb.sql
        params = qb.params
        self.assertIn('LIMIT', sql)
        self.assertIn(1, params)

        qb.execute()
        res = qb.res
        self.assertIsInstance(res, tuple)

        qb = QueryBuilder(self.book).select().limit(3).build()
        self.assertIn(3, qb.params)

        qb.execute()
        res = qb.res
        self.assertIsInstance(res, list)
        self.assertEqual(3, len(res))

    def test_offset(self):
        # id begins with 1:
        limit = 2
        offset = 2
        qb = QueryBuilder(self.book).select().limit(limit).offset(offset).build()
        sql = qb.sql
        params = qb.params
        self.assertIn('OFFSET', sql)
        self.assertIn(offset, params)

        qb.execute()
        res = qb.res
        self.assertIsInstance(res, list)
        first_id = res[0][0]
        self.assertEqual(offset + 1, first_id)
        self.assertEqual(offset, len(res))

    def test_order(self):
        for i in range(self.NUM_OF_USERS):
            u = self.user()
            u.last_name = 'John' + str(random.randint(1, 100))
            u.dob = str(random.randint(1, 100))
            QueryBuilder(self.u).insert(u).build().execute()
        cur = self.con.cursor()
        cur.execute('SELECT * FROM "user"')
        unsorted_rows = cur.fetchall()
        unsorted_users = map(lambda r: User(*r), unsorted_rows)
        sorted_users = sorted(unsorted_users, key=lambda user: user.dob)

        qb = QueryBuilder(self.user).select().order(self.user.dob, QueryBuilder.ASC).build()
        sql = qb.sql
        self.assertIn('ORDER BY', sql)
        self.assertIn('dob', sql)
        self.assertIn('ASC', sql)

        qb.execute()
        res = qb.res
        for qb_row, row in zip(res, sorted_users):
            for qb_col, col in zip(qb_row, row):
                self.assertEqual(qb_col, col)

        cur.close()
