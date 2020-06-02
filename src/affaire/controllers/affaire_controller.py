import datetime
import re
import functools
import time
from typing import List, Callable


from src.core_modules import AbstractController
from src.core_modules.utils import SubjectInterface, ObserverInterface
from src.core_modules.utils import SettingsProviderInterface

from src.affaire.exceptions import SettingsKeyError, HelpKeyError, UnknownParameterException
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


class AffaireController(AbstractController, SubjectInterface):
    """
    Observable
    """
    GOOGLE_FETCH = 1
    GOOGLE_PUSH = 2
    
    def __init__(self,
                 settings_provider: 'SettingsProviderInterface',
                 args_schema_provider: 'ArgsSchemaProviderInterface'
                 ):
        self._settings_provider = settings_provider
        self._args_schema_provider = args_schema_provider

        self._observers = list()  # type: List[ObserverInterface]

        self._args = list()  # type: List[str]
        # CLI actions mapper
        self._args_schema = None

        self._params = dict()  # mapped CLI params

        # whether it needs synchronization
        self._is_updated = False

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

    # TODO: composition with DispatcherInterface
    # implementation
    def dispatch(self, args: List[str]):
        """
        Dispatcher based on main function arguments.
        :param args: CLI parameters.=
        :return:
        """
        first_arg = str()
        if len(args) > 1:
            _, first_arg, *self._args = args

        for action in self.args_schema.get('actions', dict()):
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
        if self.settings['is_authorized']:
            res = {'msg': 'You are authenticated already'}
        else:
            s = AuthenticationServer().authenticate()
            res = s.res
            
            if res.get('error', False):
                self.settings['is_authorized'] = False
                self.settings['skip_authentication'] = True
            else:
                # token_exchange is invoked -> 'res' contains the token
                expires_at = int(time.time()) + int(res.get('expires_in', -1))
                self.settings['token_expires_at'] = expires_at
                self.settings['access_token'] = res.get('access_token', None)
                self.settings['is_authorized'] = True
                res['msg'] = 'Congratulations! you are now logged in with Google'

        return res

    def task_create(self):
        """
        INSERT
        :return:
        """
        task = Task()

        for arg, val in self._parse_args('task_create').items():
            for param, props in self._params.items():
                if arg in [param, *props.get('aliases', list())]:
                    if props.get('field', None) == 'expires_at':
                        if '+' in val:
                            digit = re.search(r'(\d+)', val)
                            if digit:
                                delta_days = int(digit.group(1))
                            else:
                                delta_days = 1
                            val = datetime.datetime.now() + datetime.timedelta(days=delta_days)
                    setattr(task, props.get('field'), val)
                    break
            else:
                raise UnknownParameterException(f'Unknown parameter {arg}')

        task.save()
        self._is_updated = True

    @notify('task_read')
    def task_read(self):
        """
        SELECT
        :return:
        """
        params = self._parse_args('task_read')

        return {
            'task_list': Task.select(params, self._params)
        }

    def task_update(self):
        """
        UPDATE
        :return:
        """
        params = self._parse_args('task_update')

        read_params = list()
        for action in self.args_schema.get('actions', list()):  # type: dict
            action_name = action.get('action', None)
            if 'task_read' == action_name:
                for short_arg, props in action.get('params', dict()).items():
                    read_params.append(short_arg)
                    read_params.extend(props.get('aliases', list()))

        select_params = {
            k: v
            for k, v in params.items()
            if k in read_params
        }
        update_params = {
            k: v
            for k, v in params.items()
            if k not in read_params
        }

        tasks = Task.select(select_params, self._params)
        for task in tasks:
            if not update_params:
                task.is_active = not task.is_active
            for param, val in update_params.items():
                props = self._params.get(param, None)
                if props is None:
                    raise UnknownParameterException(f'Unknown parameter {param}')
                field_name = props.get('field', None)
                if field_name:
                    setattr(task, field_name, val)

            task.save(False)

        self._is_updated = True

    def task_delete(self):
        """
        DELETE
        :return:
        """
        params = self._parse_args('task_delete')
        if not params and not self._params.get('-f'):
            self.notify_observers({
                'action_name': 'action_task_delete',
                'msg': 'This action will remove all your tasks. Are you sure? [y/n]: '
            })
        else:
            for task in Task.select(params, self._params):
                task.delete(True)

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

        return {'msg': res}

    @notify('version')
    def version(self):
        try:
            v = self.settings['version']
        except KeyError:
            raise SettingsKeyError('The version is not provided')

        return {'msg': v}

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

    def synchronize(self, mode):
        """
        Synchronize with Google
        :return:
        """
        s = AuthenticationServer()

        expires_at = self.settings.get('token_expires_at', -1)
        if expires_at is None or expires_at <= int(time.time()) - 1:
            s.authenticate()  # get the code and then the token
            res = s.res

            self.settings['token_expires_at'] = int(time.time()) + int(res.get('expires_in', -1))
            self.settings['access_token'] = res.get('access_token')

        if self._is_updated:
            last_file_id = s.synchronize(Task, mode, self.settings['access_token'])
            self.settings['last_file_id'] = last_file_id

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

    def _parse_args(self, action_name: str) -> dict:
        """
        Fusion CLI arguments to pairs (key, value)
        :return:
        """
        parsed_args = dict()

        def default_params_range():
            """Yield default argument's short names"""
            schema = self.args_schema.get('actions', list())
            for action in schema:  # type: dict
                if action_name != action.get('action', None):
                    continue
                params = action.get('params', dict())
                for short_arg in params.keys():
                    yield short_arg
            idx = 1
            while True:
                yield idx
                idx += 1

        default_params_generator = default_params_range()

        i = 0
        while i < len(self._args):
            arg = self._args[i]
            if arg.startswith('-'):
                try:
                    next_arg = self._args[i+1]
                    if next_arg.startswith('-'):
                        i += 1
                        parsed_args[arg] = None
                    else:
                        i += 2
                        parsed_args[arg] = next_arg
                except IndexError:
                    i += 1
                    parsed_args[arg] = None
            else:
                i += 1
                val = arg
                arg = next(default_params_generator)
                while arg in parsed_args:
                    arg = next(default_params_generator)
                parsed_args[arg] = val

        return parsed_args
