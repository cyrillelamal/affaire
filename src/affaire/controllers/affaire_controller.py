import functools
from typing import List, Iterable, Callable, Tuple


from src.core_modules import AbstractController
from src.core_modules.utils import SubjectInterface, ObserverInterface
from src.core_modules.utils import SettingsProviderInterface

from src.affaire.exceptions import SettingsKeyError, HelpKeyError
from src.affaire.models import Task
from src.affaire.utils import AuthenticationServer
from src.affaire.utils import ArgsSchemaProviderInterface


def notify(action_name='', prefix='action_'):
    """
    Notify observers with the returned value.
    :param action_name: If provided, bound to the returned dict the name.
    :param prefix: Action named prefix used to distinguish the actions in the view.
    :return: type: Callable
    """
    def notify_decorator(action: Callable):
        @functools.wraps(action)
        def wrapped_action(*args, **kwargs):
            instance = args[0]
            if isinstance(instance, AffaireController):
                res = action(*args, **kwargs)
                if isinstance(res, dict) and action_name:
                    res['action_name'] = f'{prefix}{action_name}'
                instance.notify_observers(res)
                return res
        return wrapped_action
    return notify_decorator


# TODO: separate => { authentication_controller, affaire_controller }
class AffaireController(AbstractController, SubjectInterface):
    """
    Observable
    """
    def __init__(self,
                 settings_provider: 'SettingsProviderInterface',
                 args_schema_provider: 'ArgsSchemaProviderInterface'
                 ):
        self._settings_provider = settings_provider
        self._args_schema_provider = args_schema_provider

        self._observers = list()  # type: List[ObserverInterface]

        self._args = list()  # type: List[str]
        self._args_schema = None  # CLI actions mapper type: dict

        self._params = dict()  # mapped CLI params

    # implementation
    def register_observer(self, observer: 'ObserverInterface'):
        self._observers.append(observer)

    # implementation
    def remove_observer(self, observer: 'ObserverInterface'):
        self._observers.remove(observer)

    # implementation
    def notify_observers(self, event: dict):
        for observer in self._observers:
            observer.update(event)

    # implementation
    def dispatch(self, args: List[str]):
        """
        Dispatcher based on main function arguments.
        :param args: CLI parameters.
        :return:
        """
        first_arg = ''
        if len(args) > 1:
            _, first_arg, *self._args = args

        for action in self.args_schema['actions']:
            if first_arg in action.get('names', list()):
                self._params = action.get('params', dict())
                action = getattr(self, action.get('action', None))
                break
        else:
            action = self.help
            if first_arg.startswith('-'):
                action = self._dispatch_meta(first_arg)

        if action is not None:  # type: Callable
            action()

    @notify('authenticate')
    def authenticate(self):
        AuthenticationServer().authenticate()
        # TODO: authenticate
        # TODO: set settings

    def task_create(self):
        """
        INSERT
        :return:
        """
        task = Task()
        for arg, val in self._fusion():
            for param, props in self._params.items():
                if arg in [param, *props.get('aliases', list())]:
                    setattr(task, props.get('field'), val)
        task.save()

    @notify('task_read')
    def task_read(self):
        """
        SELECT
        :return:
        """
        params = dict(self._fusion())
        return {
            'task_list': Task.select(params)
        }

    # TODO: update

    def task_delete(self):
        """
        DELETE
        :return:
        """
        params = dict(self._fusion())

        for task in Task.select(params):
            task.delete()

    @notify('help')
    def help(self):
        try:
            help_ = self.settings['help']  # type: dict
        except KeyError:
            raise SettingsKeyError('The manual is not provided')

        # default key
        about = self._args[0] if self._args else 'all'

        try:
            res = help_[about]
        except KeyError:
            try:
                res = help_['panic']  # advise the user
            except KeyError:
                raise HelpKeyError('The "panic" key is undefined')

        return {'body': res}

    @notify('version')
    def version(self):
        try:
            v = self.settings['version']
        except KeyError:
            raise SettingsKeyError('The version is not provided')

        return {'version': v}

    @property
    def args_schema(self) -> dict:
        if self._args_schema is None:
            self._args_schema = self._args_schema_provider.load_schema()

        return self._args_schema

    def dump_settings(self):
        """
        Alias for the view or other observers
        :return:
        """
        self._settings_provider.dump_settings(self.settings)

    def synchronize(self):
        """
        Synchronize with VK
        :return:
        """
        pass

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

    # TODO: default argument's reducer
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
