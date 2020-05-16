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

    def __init__(self, controller: 'AffaireController', args: List[str]):
        self._controller = controller  # type: AffaireController
        self._args = args

    # implementation
    def start(self):
        # like middleware or container
        # propose the user to authenticate via OAuth
        if not self._controller.settings['isAuthorized']:
            if not self._controller.settings['skipAuthentication']:
                self.propose_authentication()

    # implementation
    def loop(self):
        # run once
        # without 'while(1)'
        # noinspection PyBroadException
        try:
            self._controller.dispatch(self._args)
        except UnknownParameterException as e:
            print(e)
        except UndefinedValueException as e:
            print(e)
        except Exception:
            print('Internal error')

    # implementation
    def stop(self):
        # update settings
        # synchronize
        self._controller.dump_settings()
        self._controller.synchronize()

    # implementation
    def update(self, event: dict):
        action = event.get('action_name', '')
        msg = event.get('msg')
        if action.endswith('help') or action.endswith('version'):
            print(msg)
        elif action.endswith('task_delete'):
            if CLIView._approve(msg):
                self._controller.dispatch(['_', 'delete', '-f'])
        elif action.endswith('task_read'):
            for task in event.get('task_list'):
                print(task)

    def propose_authentication(self):
        print('Log in via VK and share your tasks through all you devices')

        inp = CLIView._approve('Continue with VK? [y/n]:')

        if inp in ['', *CLIView.ACCEPT]:
            self._controller.authenticate()
        else:
            self._controller.settings['isAuthorized'] = False
            self._controller.settings['skipAuthentication'] = True
            print('You can authenticate later: run the "auth" action')

    @staticmethod
    def _approve(msg: str) -> bool:
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
