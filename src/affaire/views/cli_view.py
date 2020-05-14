import os
from typing import List


from src.core_modules import AbstractView
from src.core_modules.utils import ObserverInterface

from src.affaire.controllers import AffaireController


class CLIView(AbstractView, ObserverInterface):
    """
    Observer
    """
    ACCEPT = ['y', 'yes']
    DENY = ['n', 'no']

    def __init__(self, controller: 'AffaireController', args: List[str]):
        self._controller = controller  # type: 'AffaireController'
        self._args = args

    def start(self):
        # like middleware or container
        # propose the user to authenticate via OAuth
        if not self._controller.settings['isAuthorized']:
            if not self._controller.settings['skipAuthentication']:
                self.propose_authentication()

    def loop(self):
        # run once
        # without 'while(1)'
        self._controller.dispatch(self._args)

    def stop(self):
        self._controller.dump_settings()
        self._controller.synchronize()

    def update(self, event: dict):
        print(event)
        action = event.get('action', '')
        if action == 'help':
            self._display(event['body'])
        # TODO: implement

    def propose_authentication(self):
        self._display('Log in via VK and share your list through all you devices')

        inp = None
        while inp not in ['', *self.ACCEPT, *self.DENY]:
            self._display('Continue with VK? [y/n] (y): ', end='')
            inp = self._input()
            self._display('')

        if inp in ['', *self.ACCEPT]:
            self._controller.authenticate()
        else:
            self._controller.settings['isAuthorized'] = False
            self._controller.settings['skipAuthentication'] = True

    @staticmethod
    def _display(string: str, end='\n'):
        print(string, end=end)

    @staticmethod
    def _input() -> str:
        return input()

    @staticmethod
    def _clear():
        os.system('cls' if os.name == 'nt' else 'clear')
