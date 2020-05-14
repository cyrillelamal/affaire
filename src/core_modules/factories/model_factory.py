from typing import Type


# TODO: implement it
# TODO: walk model's columns
# TODO: ensure order of columns
class ModelFactory:
    """
    Create objects
    """
    from src.core_modules.ORM.abstract_model import AbstractModel

    def __init__(self, constructor: Type[AbstractModel]):
        self.constructor = constructor

    @staticmethod
    def fill_row(constructor: Type[AbstractModel], data_row: [tuple, list], eager=False):
        """
        Fill single row.
        :param constructor: Model class.
        :param data_row: Fetched row.
        :param eager: If True, initialize all nested models.
        :return: Model
        """
        model_instance = constructor()

        if eager:
            model_instance = ModelFactory._fill_eager(constructor, data_row)
        else:
            for field, val in zip(constructor.get_cols(), data_row):
                setattr(model_instance, field.field_name, val)

        return model_instance

    def load_json(self, data: dict):
        pass  # TODO: implement

    @staticmethod
    def _fill_eager(base_model: type(AbstractModel), data: [tuple, list]):
        """
        Recursive filling.
        :param base_model: Model class.
        :param data: Fetched row.
        :return: Model
        """
        from src.core_modules.ORM.field_types import ForeignKey

        # FIXME: self recursion
        def walker(instance_, cols, data_):
            for col in cols:
                if isinstance(col.field, ForeignKey):
                    nested_model = col.field.get_ref()
                    nested_instance = nested_model()
                    setattr(instance_, col.field_name, nested_instance)
                    walker(nested_instance, nested_model.get_cols(), data_)
                else:
                    setattr(instance_, col.field_name, next(data_))

        def data_iterator(data_):
            yield from data_

        model_instance = base_model()
        walker(model_instance, base_model.get_cols(), data_iterator(data))

        return model_instance
