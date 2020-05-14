# import unittest
#
#
# from src.core_modules.abstract_model import AbstractModel
# from src.core_modules import field_types as ft
#
#
# from src.core_modules.factories.model_factory import ModelFactory
#
#
# class TestModelFactory(unittest.TestCase):
#     def setUp(self) -> None:
#         class ScalarModel(AbstractModel):
#             id = ft.IntegerField(primary_key=True, autoincrement=True)
#             title = ft.TextField()
#             price = ft.RealField()
#
#         class ComplexModel(AbstractModel):
#             scalar_model = ft.ForeignKey(ScalarModel)
#             title = ft.TextField()
#
#         self.scalar_model = ScalarModel
#         self.complex_model = ComplexModel
#
#     # def test_get_cols_lazy(self):
#     #     # fetch only the model fields
#     #     cols = self.scalar_model.get_cols()
#     #     self.assertEqual(3, len(cols))
#     #     for col in cols:
#     #         self.assertIsInstance(col, Column)
#     #
#     #     # dumb mode
#     #     # eager fetching should not affect scalar model
#     #     cols = self.scalar_model.get_cols(True)
#     #     self.assertEqual(3, len(cols))
#     #     for col in cols:
#     #         self.assertIsInstance(col, Column)
#     #     cols = list(self.complex_model.get_cols())
#     #     self.assertEqual(2, len(cols))
#     #     for col in cols:
#     #         self.assertIsInstance(col, Column)
#     #
#     # def test_eager_col_names(self):
#     #     # all related fields
#     #     def walker(cols_):  # not Johnny
#     #         for col_ in cols_:
#     #             if isinstance(col_.field, list):
#     #                 walker(col_.field)
#     #             else:
#     #                 self.assertIsInstance(col_, Column)
#     #
#     #     cols = self.complex_model.get_cols(True)
#     #     print(cols)
#     #     for col in cols:
#     #         self.assertIsInstance(col, Column)
#
#     def test_lazy_filling(self):
#         # without joins
#         # order is important
#         db_row = (1, 'Lorem', 99.99)  # SQL generated according to cols
#
#         sm = ModelFactory.fill_row(self.scalar_model, db_row, eager=False)
#         self.assertEqual(getattr(sm, 'id', None), 1)
#         self.assertEqual(getattr(sm, 'title', None), 'Lorem')
#         self.assertEqual(getattr(sm, 'price', None), 99.99)
#
#         # order is important
#         db_row = (1, 'Dolor')  # Foreign key value
#         cm = ModelFactory.fill_row(self.complex_model, db_row, eager=False)
#         self.assertEqual(getattr(cm, 'scalar_model', None), 1)
#         self.assertEqual(getattr(cm, 'title', None), 'Dolor')
#
#     def test_eager_filling(self):
#         # with joins
#         # scalar models should not be affected
#         data = (1, 'Lorem', 99.99)
#         sm = ModelFactory.fill_row(self.scalar_model, data, eager=True)
#         self.assertEqual(getattr(sm, 'id'), 1)
#         self.assertEqual(getattr(sm, 'title'), 'Lorem')
#         self.assertEqual(getattr(sm, 'price'), 99.99)
#
#         data = (1, 'Lorem', 23.99, 'Dolor')
#         cm = ModelFactory.fill_row(self.complex_model, data, eager=True)
#         self.assertEqual(getattr(cm, 'title'), 'Dolor')
#         self.assertIsInstance(cm.scalar_model, self.scalar_model)
#         sm = cm.scalar_model
#         self.assertEqual(getattr(sm, 'title'), 'Lorem')
#         self.assertEqual(getattr(sm, 'price'), 23.99)
#         self.assertEqual(getattr(sm, 'id'), 1)
