import os
import sqlite3
import unittest


from src.core_modules.ORM import AbstractModel
from src.core_modules.ORM import field_types as ft
from src.core_modules.ORM import QueryBuilder


class TestDelete(unittest.TestCase):
    DB_PATH = './test.db'

    def setUp(self) -> None:
        AbstractModel.DB_PATH = self.DB_PATH

        class Scalar(AbstractModel):
            id = ft.IntegerField(primary_key=True, autoincrement=True)
            txt = ft.TextField()

        class Complex(AbstractModel):
            id = ft.IntegerField(primary_key=True, autoincrement=True)
            desc = ft.TextField()
            ref = ft.ForeignKey(Scalar)

        QueryBuilder(Scalar).create_table(True).build().execute()
        QueryBuilder(Complex).create_table(True).build().execute()

        self.scalar_model = Scalar
        self.complex_model = Complex

        self.con = sqlite3.connect(AbstractModel.DB_PATH)

        scalar_inst = Scalar()
        scalar_inst.txt = 'test_delete'
        qb = QueryBuilder(Scalar).insert(scalar_inst, True).build().execute()
        scalar_inst.pk = qb._last_id
        self.scalar_inst = scalar_inst

        complex_inst = Complex()
        complex_inst.desc = 'description'
        complex_inst.ref = scalar_inst
        qb = QueryBuilder(Complex).insert(complex_inst, True).build().execute()
        complex_inst.pk = qb._last_id
        self.complex_inst = complex_inst

    def tearDown(self) -> None:
        self.con.close()
        AbstractModel.DB_PATH = None
        os.remove(self.DB_PATH)

    def test_delete_scalar(self):
        cur = self.con.cursor()
        stmt = 'SELECT * FROM "scalar"'
        cur.execute(stmt)
        row = cur.fetchone()
        self.assertIsNotNone(row)
        inst = self.scalar_inst

        qb = QueryBuilder(self.scalar_model).delete(inst, True).build()
        sql = qb.sql
        params = qb.params
        self.assertIn('DELETE', sql)
        self.assertIn('"scalar"', sql)
        self.assertIn('WHERE', sql)
        self.assertIn(inst.pk, params)
        qb.execute()

        cur.execute(stmt)
        row = cur.fetchone()
        self.assertIsNone(row)

        cur.close()

    def test_delete_complex(self):
        cur = self.con.cursor()
        stmts = ('SELECT * FROM "complex"', 'SELECT * FROM "scalar"')
        for stmt in stmts:
            cur.execute(stmt)
            row = cur.fetchone()
            self.assertIsNotNone(row)
        inst = self.complex_inst

        qb = QueryBuilder(self.complex_model).delete(inst, True).build()
        sql = qb.sql
        params = qb.params
        self.assertIn('DELETE', sql)
        self.assertIn('"complex"', sql)
        self.assertIn(inst.pk, params)
        qb.execute()

        for stmt in stmts:
            cur.execute(stmt)
            row = cur.fetchone()
            self.assertIsNone(row)

        cur.close()
