import json
from typing import List, Iterable, Callable, Tuple


from src.core_modules import AbstractController
from src.core_modules.utils import SubjectInterface, ObserverInterface
from src.core_modules.utils import SettingsProviderInterface

from src.affaire.exceptions import SettingsKeyError, HelpKeyError
from src.affaire.models import Task
from src.affaire.utils import AuthenticationServer


# TODO: separate => { authentication_controller, affaire_controller }
class AffaireController(AbstractController, SubjectInterface):
    """
    Observable
    """
    def __init__(self, settings_provider: 'SettingsProviderInterface'):
        self._settings_provider = settings_provider

        self._observers = list()  # type: List[ObserverInterface]
        self._response = dict()

        self._args = list()  # type: List[str]
        self._args_schema = None  # CLI actions mapper

        self._params = dict()  # CLI params mapper

    def register_observer(self, observer: 'ObserverInterface'):
        self._observers.append(observer)

    def remove_observer(self, observer: 'ObserverInterface'):
        self._observers.remove(observer)

    def notify_observers(self):
        for observer in self._observers:
            observer.update(self._response)
        self._response = dict()

    def dispatch(self, args: List[str]):
        """
        Dispatcher based on main function arguments.
        :param args: CLI parameters.
        :return:
        """
        if len(args) > 1:
            _, first_arg, *self._args = args
        else:
            first_arg = ''
            self._args = list()

        for action in self.args_schema['actions']:
            if first_arg in action['names']:
                action = getattr(self, action['action'])
                self._params = action['params']
                break
        else:
            action = self.help
            if first_arg.startswith('-'):
                action = self._dispatch_meta(first_arg)

        self.propose_authentication()
        action()
        self.notify_observers()

    def propose_authentication(self):
        if not self.settings['isAuthorized']:
            if not self.settings['skipAuthentication']:  # TODO: force parameter
                self._response = {
                    'action': 'propose_authentication'
                }
                self.notify_observers()

    def authenticate(self):
        res = AuthenticationServer().authenticate()
        # TODO: authenticate
        # TODO: set settings
        self._response = dict()
        self.notify_observers()

    def task_create(self):
        """
        INSERT
        :return:
        """
        task = Task()
        for arg, val in self._fusion():
            for param, props in self._params.items():
                if arg in [param, *props['aliases']]:
                    setattr(task, props['field'], val)
        task.save()

    def task_read(self):
        """
        SELECT
        :return:
        """
        params = dict(self._fusion())
        self._response['task_list'] = Task.select(params)

    # TODO: update

    def task_delete(self):
        """
        DELETE
        :return:
        """
        params = dict(self._fusion())

        for task in Task.select(params):
            task.delete()

    def help(self):
        try:
            help_ = self.settings['help']  # type: dict
        except KeyError:
            raise SettingsKeyError('The manual is not provided')

        # default key
        about = 'all'  # TODO: implement with args

        try:
            res = help_[about]
        except KeyError:
            try:
                res = help_['panic']  # advise the user
            except KeyError:
                raise HelpKeyError('The "panic" key is undefined')

        self._response['action'] = 'help'
        self._response['body'] = res

    def version(self):
        try:
            self._response = self.settings['version']
        except KeyError:
            raise SettingsKeyError('The version is not provided')

    # TODO: generic 'args_schema' provider
    @property
    def args_schema(self) -> dict:
        if self._args_schema is None:
            with open('./args_schema.json') as f:
                self._args_schema = json.loads(f.read())

        return self._args_schema

    def _dispatch_meta(self, first_arg: str) -> Callable:
        """
        Additional dispatcher
        :param first_arg:
        :return:
        """
        if first_arg in ['-v', '--version']:
            action = self.version
        else:
            action = self.help

        return action

    # TODO; default argument's reducer
    def _fusion(self) -> Iterable[Tuple[str, str]]:
        """
        Fusion CLI arguments to pairs (key, value)
        :return:
        """
        i = 0
        while i < len(self._args):
            arg = self._args[i]  # current arg
            val = None
            try:
                na = self._args[i+1]  # next arg
                if not na.startswith('-'):
                    val = na
            except IndexError:
                pass
            if val is None:
                i += 1
            else:
                i += 2

            yield arg, val
