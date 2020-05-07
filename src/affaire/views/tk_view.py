import tkinter as tk
from typing import Tuple


from src.core_modules.utils import ObserverInterface
from src.affaire.controllers import AffaireController


class TKView(tk.Frame, ObserverInterface):
    CONTROLLER = None  # type: AffaireController
    
    WIN_SIZE = (640, 480)
    FRAME_PADDING = {'pady': 10, 'padx': 10}

    ROOT = tk.Tk()

    task_create = None  # type: tk.Frame
    task_list = None  # type: tk.Frame
    task_detail = None  # type: tk.Frame
    task_sort = None  # type: tk.Frame

    title = None  # type: tk.Label

    def __init__(self, master=None, **kw):
        super().__init__(**kw)

        self.master = master
        self.pack()  # widget in the master windows

        self.configure_window()

        self.propose_authentication()

        self.create_widgets()
        self.set_labels()



    # def run(self):
        
    def configure_window(self):
        self.ROOT.title('Affaire')

        width, height = self._load_win_size()
        self.ROOT.geometry(f'{width}x{height}')

    def create_widgets(self):
        # new task
        self.task_create = tk.Frame(self, name='task_create', **self.FRAME_PADDING)
        self.task_create.pack(fill=tk.X, expand=True)

        # sort tasks
        self.task_sort = tk.Frame(self, name='task_sort', **self.FRAME_PADDING)
        self.task_sort.pack(fill=tk.X, expand=True)

        # list of the tasks
        self.task_list = tk.Frame(self, name='task_list', background='green', pady=10, padx=10)
        self.task_list.pack(fill=tk.X, expand=True)

        # modify the task
        self.task_detail = tk.Frame(self, name='task_detail', background='red', pady=10, padx=10)
        self.task_detail.pack(fill=tk.X, expand=True)

    def set_labels(self):
        self.title = tk.Label(self.task_list, text='Tasks')
        self.title.pack(side='top')

    def propose_authentication(self):
        settings = self.CONTROLLER.settings

        if settings.get('isAuthenticated', False) or settings.get('ignoreAuthentication', False):
            return
        else:
            authentication = tk.Frame(self, name='authentication', **self.FRAME_PADDING)

            login_btn = tk.Button(authentication,
                                  text='Enter with Google', command=self.CONTROLLER.auth_with_google
                                  )
            login_btn.pack()

            skip_btn = tk.Button(authentication,
                                 text='Skip', command=self.CONTROLLER.skip_auth
                                 )
            skip_btn.pack()

            authentication.pack()

    def _load_win_size(self) -> Tuple[int, int]:
        try:
            # TODO: settings provider
            win_size = tuple(self.CONTROLLER.settings['winSize'])
        except KeyError:
            win_size = self.WIN_SIZE

        return win_size
