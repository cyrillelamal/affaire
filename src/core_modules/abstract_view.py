import abc


from src.core_modules.abstract_controller import AbstractController


class AbstractView:
    """
    Observer
    Rather an interface.
    """
    _controller = None  # type: AbstractController
    
    _args = None  # type: list

    def run(self):
        """
        Algorithm
        Entry point.
        :return:
        """
        self.start()
        self.loop()
        self.stop()

    @abc.abstractmethod
    def start(self):
        """
        Create view.
        :return:
        """
        pass

    @abc.abstractmethod
    def loop(self):
        """
        Main workflow.
        :return:
        """
        pass

    @abc.abstractmethod
    def stop(self):
        """
        Destroy view.
        :return:
        """
        pass

    @property
    def controller(self):
        return self._controller

    @property
    def args(self):
        return self._args
