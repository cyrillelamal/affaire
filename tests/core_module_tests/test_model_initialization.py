import unittest

from src.core_modules.abstract_model import AbstractModel, Column
from src.core_modules import field_types as ft


class TestModelInitialization(unittest.TestCase):
    def test_get_table_name(self):
        # single word
        class Word(AbstractModel):
            pass

        self.assertEqual('word', Word.get_table_name())

        # multiple words
        class MultipleWords(AbstractModel):
            pass

        self.assertEqual('multiple_words', MultipleWords.get_table_name())

    def test_get_columns(self):
        class Book(AbstractModel):
            id = ft.IntegerField(primary_key=True)
            title = ft.TextField()
            owner = ft.ForeignKey('User')

        fields = ['id', 'title', 'owner']

        for field_name, field in Book.get_cols():
            self.assertIn(field_name, fields)
            del fields[fields.index(field_name)]
            self.assertIsInstance(field, ft.FieldType)
        self.assertFalse(fields)

    def test_type_mapping(self):
        self.assertEqual('INTEGER', ft.IntegerField().get_type())
        self.assertEqual('REAL', ft.RealField().get_type())
        self.assertEqual('TEXT', ft.TextField().get_type())
        self.assertEqual('BLOB', ft.BlobField().get_type())

    def test_default_fields_provider(self):
        class ScalarModel(AbstractModel):
            id = ft.IntegerField(primary_key=True, autoincrement=True)
            title = ft.TextField(use_default=True)
            price = ft.RealField(use_default=True)
            img = ft.BlobField(use_default=True)
            owner = ft.IntegerField(use_default=False)

        default_fields = [col for col in ScalarModel.get_cols() if col.field.use_default]
        self.assertEqual(3, len(default_fields))

    def test_primary_key_initialization(self):
        # with defined pk
        class WithPK(AbstractModel):
            num = ft.IntegerField(primary_key=True)
            title = ft.IntegerField()

        pk_field = WithPK.get_pk_field()
        self.assertEqual('num', pk_field.field_name)
        self.assertIsInstance(pk_field.field, ft.IntegerField)
        self.assertTrue(pk_field.field.primary_key)
        self.assertFalse(WithPK.title.primary_key)

        # with undefined pk
        class WithoutPK(AbstractModel):
            num = ft.IntegerField()
            title = ft.TextField()

        pk_field = WithoutPK.get_pk_field()
        self.assertEqual('id', pk_field.field_name)
        self.assertIsInstance(pk_field.field, ft.IntegerField)
        self.assertTrue(pk_field.field.primary_key)
        self.assertFalse(WithoutPK.title.primary_key)

    def test_column_description(self):
        class ScalarModel(AbstractModel):
            id = ft.IntegerField(primary_key=True, autoincrement=True)
            title = ft.TextField(not_null=False)
            price = ft.RealField(not_null=False)
            img = ft.BlobField(not_null=False)

        sql = ScalarModel.to_sql()

        regex = r''
        for col in ScalarModel.get_cols():
            self.assertIsInstance(col, Column)
            regex += f'{col.field_name}'
            regex += r'( )+'
            regex += f'{col.field.get_type()}'
            if col.field.primary_key:
                regex += r'( )+PRIMARY KEY'
            if isinstance(col.field, ft.IntegerField) and col.field.autoincrement:
                regex += r'( )+AUTOINCREMENT'
            if col.field.not_null and not col.field.primary_key:
                regex += r'( )+NOT NULL'
            regex += r'(.*\n)?'
        regex += r'\)$'
        self.assertRegex(sql, regex)

        for _, col in ScalarModel.get_cols():
            if isinstance(col, ft.FieldType):
                sql = col.to_sql()
                if col.primary_key or col.unique:
                    self.assertNotIn('DEFAULT', sql)
                elif col.use_default:
                    self.assertIn('DEFAULT', sql)
            else:
                self.assertTrue(False)

    def test_init_scalar_fields(self):
        class Book(AbstractModel):
            id = ft.IntegerField()
            title = ft.TextField()

        self.assertIsInstance(Book.id, ft.IntegerField)
        self.assertIsInstance(Book.title, ft.TextField)

    def test_init_referer_fields(self):
        class Place(AbstractModel):  # dependable
            coords = ft.TextField()

        class Book(AbstractModel):  # main
            # directly
            place = ft.ForeignKey(Place, reversed_by='books')
            # as string
            owner = ft.ForeignKey('User', reversed_by='books')

        class User(AbstractModel):  # dependable
            name = ft.TextField()

        self.assertEqual(Book.place.get_ref(), Place)
        self.assertEqual(Book.owner.get_ref(), User)

        regex = f'^{Place.get_table_name()}{Book.WORD_JOINER}{Book.get_pk_field().field_name} ' \
                f'{Book.get_pk_field().field.get_type()}'
        self.assertRegex(Book.place.to_sql(), regex + r'( ){1,}NOT NULL$')
        regex = f'^{User.get_table_name()}{User.WORD_JOINER}{User.get_pk_field().field_name} ' \
                f'{User.get_pk_field().field.get_type()}'
        self.assertRegex(Book.owner.to_sql(), regex + r'( ){1,}NOT NULL$')
