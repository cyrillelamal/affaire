import unittest
import sqlite3
import os
import itertools


from src.core_modules.ORM import AbstractModel
from src.core_modules.ORM import field_types as ft
from src.core_modules.ORM import QueryBuilder


class TestCreateTable(unittest.TestCase):
    DB_PATH = './test.db'

    SQL_SELECT_TABLES = 'SELECT name FROM sqlite_master WHERE type="table"'

    def setUp(self) -> None:
        AbstractModel.DB_PATH = self.DB_PATH
        self.con = sqlite3.connect(AbstractModel.DB_PATH)

    def tearDown(self) -> None:
        self.con.close()
        os.remove(self.DB_PATH)
        AbstractModel.DB_PATH = None

    def test_create_table(self):
        cur = self.con.cursor()

        cur.execute(self.SQL_SELECT_TABLES)
        self.assertFalse(cur.fetchall())

        cols = {
            'lorem': ft.IntegerField,
            'ipsum': ft.TextField,
            'dolor': ft.BlobField,
            'amet': ft.ForeignKey
        }

        class Model(AbstractModel):
            pass

        class Ref(AbstractModel):
            pass

        for col_name, col_meta in cols.items():
            if col_meta is ft.ForeignKey:
                col_meta = col_meta(Ref)
            else:
                col_meta = col_meta()
            setattr(Model, col_name, col_meta)

        qb = QueryBuilder(Model)
        qb.create_table(False).build()
        sql = qb.sql
        self.assertIn('"model"', sql)
        qb.execute()
        cur.execute(self.SQL_SELECT_TABLES)
        self.assertTrue(cur.fetchall())

        qb = QueryBuilder(Ref)
        qb.create_table(False).build()
        sql = qb.sql
        self.assertIn('"ref', sql)
        qb.execute()
        cur.execute(self.SQL_SELECT_TABLES)
        tables = list(itertools.chain.from_iterable(cur.fetchall()))

        self.assertIn('model', tables)
        self.assertIn('ref', tables)
