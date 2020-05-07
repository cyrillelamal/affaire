import unittest
import sqlite3

from src.core_modules import AbstractModel
from src.core_modules import field_types as ft


class TestScalarModelWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        self.base_db = settings.DATABASE  # path

        settings.DATABASE = ':memory:'

        self.con = sqlite3.connect(settings.DATABASE)
        self.cur = self.con.cursor()

        class ScalarModel(AbstractModel):
            id = ft.IntegerField(primary_key=True, autoincrement=True)
            title = ft.TextField()
            price = ft.RealField()
            img = ft.BlobField()

        self.model = ScalarModel

    def tearDown(self) -> None:
        self.cur.execute('DROP TABLE IF EXISTS scalar_model')
        self.con.commit()
        self.cur.close()
        self.con.close()

        settings.DATABASE = self.base_db

    # def test_create_table(self):
    #     self.cur.build("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    #     self.assertFalse(self.cur.fetchall())
    #     self.model.create_table(commit=True)
    #
    # def test_create_tables(self):
    #     # class AnotherModel(Model):
    #     #     id = ft.IntegerField(primary_key=True, autoincrement=True)
    #     #     title = ft.TextField()
    #     #
    #     # self.assertFalse(Model._table_stack)
    #     Model.create_tables()
    #     # self.assertEqual(2, len(Model._table_stack)
