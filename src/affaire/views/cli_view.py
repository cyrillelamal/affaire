import os
from typing import List


from src.core_modules import AbstractView
from src.core_modules.utils import ObserverInterface

from src.affaire.controllers import AffaireController


class CLIView(AbstractView, ObserverInterface):
    """
    Observer
    """
    def __init__(self, controller: 'AffaireController', args: List[str]):
        self._controller = controller  # type: 'AffaireController'
        self._args = args

    def start(self):
        pass

    def loop(self):
        # run once
        # without 'while(1)'
        self.controller.dispatch(self._args)

    def stop(self):
        pass
        # TODO: synchronize before exit

    def update(self, event: dict):
        action = event.get('action', '')
        if action == 'propose_authentication':
            self._display('Log in with VK')
            self._controller.authenticate()
        elif action == 'help':
            self._display(event['body'])
        # TODO: implement

    @staticmethod
    def _display(string: str):
        print(string)

    @staticmethod
    def _clear():
        os.system('cls' if os.name == 'nt' else 'clear')
