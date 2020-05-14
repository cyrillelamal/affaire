import abc


class ArgsSchemaProviderInterface:
    @abc.abstractmethod
    def load_schema(self) -> dict:
        """
        Provider CLI argument mapper to the model
        :return:
        """
        pass
