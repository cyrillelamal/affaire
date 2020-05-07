import abc
from typing import List


from src.core_modules.utils import SettingsProviderInterface


class AbstractController:
    """
    Observable
    """
    _settings_provider = None  # type: SettingsProviderInterface

    _settings = None  # type: dict

    @abc.abstractmethod
    def dispatch(self, args: List[str]):
        """
        Entry point.
        Dispatch the request.
        :param args:
        :return:
        """
        pass

    @property
    def settings(self) -> dict:
        """
        Super-lazy settings provider.
        :return:
        """
        if self._settings is None:
            self._settings = self._settings_provider.load_settings()

        return self._settings
