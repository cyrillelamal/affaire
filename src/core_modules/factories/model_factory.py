from typing import Type, List, Iterable, Union


class ModelFactory:
    """
    Create objects
    """
    from src.core_modules.ORM import AbstractModel
    from src.core_modules.ORM import ForeignKey

    def __init__(self, constructor: Type[AbstractModel], data: [list, tuple]):
        self.constructor = constructor  # basic constructor
        self.data = data  # fetched row or rows

        self._joins = list()  # joined columns

    @property
    def joins(self) -> List[ForeignKey]:
        """
        Joined columns.
        :return:
        """
        return self._joins

    def append_joins(self, *joined_cols: Iterable[Union[ForeignKey, str]], reset=False):
        """
        Append the models foreign keys that have been used in JOIN statements.
        :param joined_cols: ForeignKey field or name of property.
        :param reset: If True, clear the current list of joins
        :return:
        """
        from src.core_modules.ORM import ForeignKey

        if reset:
            self._joins.clear()

        for joined_col in joined_cols:
            if isinstance(joined_col, ForeignKey):
                self._joins.append(joined_col)
            elif isinstance(joined_col, str):
                for col in self.constructor.get_cols(False):
                    if col.name == joined_col:
                        self._joins.append(col)
                        break
                else:
                    raise KeyError(f'The column with name "{joined_col}" does not exist')
            else:
                raise TypeError(f'Unsupported parameter as column identifier {joined_col}, {type(joined_col)}')

        return self

    def to_list(self) -> List[AbstractModel]:
        """
        Map the data to list of models.
        :return:
        """
        if isinstance(self.data, tuple):
            objects = self.fill_row(self.data)
        elif isinstance(self.data, list):
            objects = [self.fill_row(row) for row in self.data]
        elif self.data is None:
            objects = list()
        else:
            raise TypeError('Inappropriate data to be filled')
        return objects

    def fill_row(self, row: tuple) -> AbstractModel:
        """
        Fill one object with the fetched row.
        :param row:
        :return:
        """
        from src.core_modules.ORM import ForeignKey

        joins = self.joins

        def filler(model, cols, start):
            # create instance and fill it
            inst = model()
            end = start + len(cols)
            data = row[start:end]
            for col, val in zip(cols, data):
                if col.primary_key:
                    inst.pk = val
                setattr(inst, col.name, val)

            # pass recursively the related model constructors
            for fk_col in filter(lambda c: isinstance(c, ForeignKey), cols):
                try:
                    ref_model = joins.pop(joins.index(fk_col)).get_ref()
                    ref_cols = ref_model.get_cols(False)
                    ref_start = end + len(ref_cols)
                    filler(ref_model, ref_cols, ref_start)
                except ValueError:
                    continue

            return inst

        return filler(self.constructor, self.constructor.get_cols(False), 0)
