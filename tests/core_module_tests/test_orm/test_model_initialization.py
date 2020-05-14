import unittest

from src.core_modules.ORM import AbstractModel
from src.core_modules.ORM import field_types as ft


class TestModelInitialization(unittest.TestCase):
    def test_get_table_name(self):
        class Word(AbstractModel):  # single word
            pass
        self.assertEqual('word', Word.get_table_name())

        class MultipleWords(AbstractModel):  # # multiple words
            pass
        self.assertEqual('multiple_words', MultipleWords.get_table_name())

    def test_type_mapping(self):
        self.assertEqual('INTEGER', ft.IntegerField().get_type())
        self.assertEqual('REAL', ft.RealField().get_type())
        self.assertEqual('TEXT', ft.TextField().get_type())
        self.assertEqual('BLOB', ft.BlobField().get_type())

    def test_get_columns_lazy(self):
        cols = {
            'id': ft.IntegerField(primary_key=True),
            'title': ft.TextField(),
            'owner': ft.ForeignKey('NestedModel')
        }

        class AModel(AbstractModel):
            pass
        for col_name, col_meta in cols.items():
            setattr(AModel, col_name, col_meta)

        for col in AModel.get_cols(False):
            self.assertIn(col.name, cols)
            col_meta = cols.get(col.name)
            self.assertIs(col, col_meta)
            del cols[col.name]
        self.assertFalse(cols)

    def test_get_columns_eager(self):
        super_model_cols = {
            'lorem': ft.IntegerField(primary_key=True),
            'title': ft.TextField(),
            'owner': ft.ForeignKey('NestedModel')
        }
        nested_model_cols = {
            'date': ft.TextField(),
            'title': ft.TextField()
        }

        total_cols = len(nested_model_cols) + len(super_model_cols)

        class SuperModel(AbstractModel):
            pass
        for col_name, col_meta in super_model_cols.items():
            setattr(SuperModel, col_name, col_meta)

        class NestedModel(AbstractModel):
            pass
        for col_name, col_meta in nested_model_cols.items():
            setattr(NestedModel, col_name, col_meta)

        super_cols = SuperModel.get_cols(True)
        self.assertEqual(total_cols, len(super_cols))

        nested_cols = NestedModel.get_cols(True)
        self.assertEqual(len(nested_model_cols), len(nested_cols))

    def test_get_pk_col(self):
        class Model(AbstractModel):
            pass
        desc = {
            'pk': ft.IntegerField(primary_key=True),
            'not_pk': ft.IntegerField(primary_key=False),
            'another': ft.IntegerField()
        }

        model = self.fill_model_description(Model, desc)
        pk = model.get_pk_col()
        self.assertIsInstance(pk, ft.FieldType)
        self.assertIs(pk, desc.get('pk'))

    def test_default_fields(self):
        class Model(AbstractModel):
            pass
        desc = {
            'int_def': ft.IntegerField(default=1, use_default=True),
            'int_no_def': ft.IntegerField(default=1, use_default=False),
            'txt_def': ft.TextField(default='txt', use_default=True),
            'txt_no_def': ft.TextField(default='txt', use_default=False)
        }
        model = self.fill_model_description(Model, desc)

        for col in model.get_cols(False):
            desc_col = desc.get(col.name)
            if desc_col is not None and desc_col.use_default:
                self.assertTrue(col.use_default)
                self.assertEqual(desc_col.default, col.default)

    def test_default_pk(self):
        class Model(AbstractModel):
            pass

        self.assertTrue(Model.get_pk_col().primary_key)

        not_pk_col = ft.IntegerField()
        setattr(Model, 'not_pk_col', not_pk_col)
        self.assertIsNot(Model.get_pk_col(), not_pk_col)

    def test_column_description(self):
        class ScalarModel(AbstractModel):
            id = ft.IntegerField(primary_key=True, autoincrement=True)
            title = ft.TextField(not_null=False)
            price = ft.RealField(not_null=False)
            img = ft.BlobField(not_null=False)

        for col in ScalarModel.get_cols():
            if isinstance(col, ft.FieldType):
                sql = col.to_sql()
                if col.primary_key or col.unique:
                    self.assertNotIn('DEFAULT', sql)
                elif col.use_default:
                    self.assertIn('DEFAULT', sql)

    @staticmethod
    def fill_model_description(model: type(AbstractModel), cols: dict):
        for col_name, col_meta in cols.items():
            setattr(model, col_name, col_meta)
        return model
