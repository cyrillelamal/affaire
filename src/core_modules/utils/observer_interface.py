import abc


class ObserverInterface:
    @abc.abstractmethod
    def update(self, event: dict):
        """
        Invoked when controller's state has been changed.
        :return:
        """
        pass
