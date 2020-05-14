import unittest
import sqlite3
import os


from src.core_modules.ORM import AbstractModel
from src.core_modules.ORM import field_types as ft
from src.core_modules.ORM import QueryBuilder


class TestUpdate(unittest.TestCase):
    DB_PATH = './test.db'

    def setUp(self) -> None:
        AbstractModel.DB_PATH = self.DB_PATH

        class Scalar(AbstractModel):
            lorem = ft.IntegerField(primary_key=True, autoincrement=True)
            ipsum = ft.TextField()
            dolor = ft.BlobField()

        class Complex(AbstractModel):
            id = ft.IntegerField(primary_key=True, autoincrement=True)
            ref = ft.ForeignKey(Scalar, not_null=False)

        self.scalar_model = Scalar
        self.complex_model = Complex

        self.con = sqlite3.connect(AbstractModel.DB_PATH)

        QueryBuilder(Scalar).create_table(False).build().execute()
        QueryBuilder(Complex).create_table(False).build().execute()

        inst = self.scalar_model()
        inst.ipsum = 'SUM'
        inst.dolor = '0xAA'
        self.scalar_inst = inst
        qb = QueryBuilder(self.scalar_model).insert(inst).build().execute()
        self.scalar_inst.pk = qb._last_id  # normally filled via Factory

        complex_inst = self.complex_model()
        complex_inst.ref = inst
        self.complex_inst = complex_inst
        qb = QueryBuilder(self.complex_model).insert(complex_inst).build().execute()
        self.complex_inst.pk = qb._last_id  # normally filled via Factory

    def tearDown(self) -> None:
        self.con.close()
        os.remove(self.DB_PATH)
        AbstractModel.DB_PATH = None

    def test_update_scalar(self):
        cur = self.con.cursor()
        inst = self.scalar_inst
        stmt = 'SELECT * FROM "scalar"'

        inst.ipsum = 'updated'
        inst.dolor = ''

        qb = QueryBuilder(self.scalar_model).update(inst, True).build()
        sql = qb.sql
        params = qb.params
        self.assertIn('UPDATE', sql.upper())
        self.assertIn(1, params)
        self.assertIn('updated', params)
        self.assertIn('', params)

        cur.execute(stmt)
        row = cur.fetchone()  # not modified
        self.assertIn('SUM', row)
        self.assertIn('0xAA', row)
        qb.execute()
        cur.execute(stmt)
        row = cur.fetchone()  # modified
        self.assertIn(1, row)
        self.assertIn('updated', row)
        self.assertIn('', row)

        # modify the primary kye value
        inst.lorem = 1337
        qb = QueryBuilder(self.scalar_model).update(inst, True).build()
        params = qb.params
        self.assertIn(1, params)
        self.assertIn(1337, params)
        qb.execute()
        cur.execute(stmt)
        row = cur.fetchone()
        self.assertIn(inst.lorem, row)

        cur.close()

    def test_update_complex(self):
        cur = self.con.cursor()
        inst = self.complex_inst

        cur.execute('SELECT * FROM "complex"')
        row = cur.fetchone()
        self.assertEqual(1, row[0])
        cur.execute('SELECT * FROM "scalar"')
        row = cur.fetchone()
        self.assertIn(inst.ref.ipsum, row)  # 'SUM"

        inst.id = 1337
        inst.ref.ipsum = 'updated'
        inst.ref.dolor = 'null'

        qb = QueryBuilder(self.complex_model).update(self.complex_inst, True).build()
        sql = qb.sql
        self.assertIn('"complex"', sql)
        params = qb.params
        self.assertIn(1337, params)  # new value
        self.assertIn(1, params)  # original primary key value
        qb.execute()
        cur.execute('SELECT * FROM "complex"')
        row = cur.fetchone()
        self.assertIn(1337, row)
        self.assertIsInstance(inst.ref, AbstractModel)
        cur.execute('SELECT * FROM "scalar"')
        row = cur.fetchone()
        self.assertIn('updated', row)
        self.assertIn('null', row)

        cur.close()
