import abc


from src.core_modules.utils import ObserverInterface


class SubjectInterface:
    @abc.abstractmethod
    def register_observer(self, observer: 'ObserverInterface'):
        pass

    @abc.abstractmethod
    def remove_observer(self, observer: 'ObserverInterface'):
        pass

    @abc.abstractmethod
    def notify_observers(self):
        pass
