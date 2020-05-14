import unittest
import sqlite3
import os


from src.core_modules.ORM import AbstractModel
from src.core_modules.ORM import field_types as ft
from src.core_modules.ORM import QueryBuilder
from src.core_modules.ORM.exceptions import UndefinedFieldException
from src.core_modules.ORM.exceptions import EmptyQueryException


class TestInsert(unittest.TestCase):
    DB_PATH = './test.db'

    def setUp(self) -> None:
        AbstractModel.DB_PATH = self.DB_PATH

        class Scalar(AbstractModel):
            lorem = ft.IntegerField(primary_key=True)
            ipsum = ft.TextField()
            dolor = ft.BlobField()

        class Complex(AbstractModel):
            ref = ft.ForeignKey(Scalar, not_null=False)

        self.scalar_model = Scalar
        self.complex_model = Complex

        self.con = sqlite3.connect(AbstractModel.DB_PATH)

        QueryBuilder(Scalar).create_table(True).build().execute()
        qb = QueryBuilder(Complex).create_table(True).build()
        qb.execute()

    def tearDown(self) -> None:
        self.con.close()
        os.remove(self.DB_PATH)
        AbstractModel.DB_PATH = None

    def test_insert_scalar(self):
        inst = self.scalar_model()
        inst.ipsum = 'SUM'
        inst.dolor = '0xAA'

        qb = QueryBuilder(self.scalar_model)
        self.assertRaises(UndefinedFieldException, qb.insert, inst, True)

        inst.lorem = 1337
        qb.insert(inst, True).build()
        sql = qb.sql
        self.assertIn('INSERT', sql.upper())
        self.assertIn('scalar', sql)
        params = qb.params
        self.assertEqual(3, len(params))
        cur = self.con.cursor()
        cur.execute('SELECT * FROM "scalar"')
        rows = cur.fetchall()
        self.assertFalse(rows)

        qb.execute()
        cur.execute('SELECT * FROM "scalar"')
        rows = cur.fetchall()
        self.assertTrue(rows)
        cur.close()

    def test_insert_complex(self):
        inst = self.complex_model()

        qb = QueryBuilder(self.complex_model)
        inst.ref = self.scalar_model()
        inst.ref.lorem = 9000
        inst.ref.ipsum = 'SUM'
        inst.ref.dolor = '0xFF'
        qb.insert(inst, True).build()
        sql = qb.sql
        params = qb.params
        self.assertIn('INSERT', sql)
        self.assertIn('"complex"', sql)
        self.assertIn(9000, params)
        qb.execute()

        cur = self.con.cursor()
        cur.execute('SELECT * FROM "scalar" WHERE "lorem"=?', (9000, ))
        row = cur.fetchone()
        self.assertTrue(row)
        self.assertIn(9000, row)
        self.assertIn('SUM', row)
        self.assertIn('0xFF', row)
        cur.execute('SELECT * FROM "complex"')
        row = cur.fetchone()
        self.assertTrue(row)
        self.assertIn(9000, row)
        self.assertEqual(2, len(row))  # 2 != 1
