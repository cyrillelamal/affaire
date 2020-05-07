import abc


class SettingsProviderInterface:
    """
    Load and save the application's settings.
    """
    @abc.abstractmethod
    def load_settings(self) -> dict:
        """
        Return settings as dict.
        :return:
        """
        pass

    @abc.abstractmethod
    def dump_settings(self, settings: dict):
        """
        Dump settings provided in dict.
        :param settings:
        :return:
        """
        pass
