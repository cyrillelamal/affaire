import os
from typing import List


from src.core_modules import AbstractView
from src.core_modules.utils import ObserverInterface

from src.affaire.controllers import AffaireController
from src.affaire.exceptions import UnknownParameterException
from src.affaire.exceptions import UndefinedValueException


class CLIView(AbstractView, ObserverInterface):
    """
    Observer
    """
    ACCEPT = ['y', 'yes']
    DENY = ['n', 'no']

    @property
    def args(self) -> List[str]:
        return self._args

    def __init__(self, controller: 'AffaireController', args: List[str]):
        self.controller = controller  # type: AffaireController
        self._args = args

    # implementation
    def start(self):
        # like middleware or container
        # propose the user to authenticate with OAuth
        if not self.controller.settings['is_authorized']:
            if not self.controller.settings['skip_authentication']:
                self.propose_authentication()
        else:
            self.controller.synchronize(AffaireController.GOOGLE_FETCH)

    # implementation
    def loop(self):
        # run once
        # without 'while(1)'
        try:
            self.controller.dispatch(self.args)
        except UnknownParameterException as e:
            print(e)
        except UndefinedValueException as e:
            print(e)

    # implementation
    def stop(self):
        # update settings
        # synchronize
        if self.controller.settings.get('is_authorized', False):
            self.controller.synchronize(AffaireController.GOOGLE_PUSH)
        self.controller.dump_settings()

    # implementation
    def update(self, event: dict):
        action = event.get('action_name', '')
        msg = event.get('msg')
        if action.endswith('help') or action.endswith('version'):
            print(msg)
        elif action.endswith('task_delete'):
            if CLIView.approve(msg):
                self.controller.dispatch(['_', 'delete', '-f'])
        elif action.endswith('task_read'):
            for task in event.get('task_list'):
                print(task)
        elif action.endswith('authenticate'):
            print(msg)

    def propose_authentication(self):
        print('Log in with Google and share your tasks through all you devices')

        if CLIView.approve('Continue with Google? [y/n]:'):
            self.controller.authenticate()
        else:
            self.controller.settings['is_authorized'] = False
            self.controller.settings['skip_authentication'] = True
            print('You can authenticate later: run the "auth" action')

    @staticmethod
    def approve(msg: str) -> bool:
        """
        Freeze until the 'yes' or 'no' response is given.
        :param msg:
        :return:
        """
        msg = msg.strip()
        if not msg.endswith(':'):
            msg += ':'
        msg += ' '

        while True:
            inp = input(msg)

            if inp in CLIView.ACCEPT:
                return True
            elif inp in CLIView.DENY:
                return False

    @staticmethod
    def _clear():
        os.system('cls' if os.name == 'nt' else 'clear')
