import webbrowser
import os
import json
from urllib.request import urlopen
from urllib.parse import urlparse, parse_qsl, quote, urlencode, unquote
import random


class AuthenticationServer:
    AUTHORIZE_URL = 'http://oauth.vk.com/authorize'

    def __init__(self):
        # TODO: deque them with server thread
        _access_token = ''
        _user_id = ''

        _error = ''
        _error_description = ''

    @property
    def open_dialog_params(self) -> dict:
        return {
            'client_id': '7453330',
            'display': 'page',
            'redirect_uri': 'http://localhost:8080/auth',
            'scope': 'notes',
            'response_type': 'token',
            'v': '5.103'
        }

    @property
    def authentication_link(self) -> str:
        return self.AUTHORIZE_URL + '?' + unquote(urlencode(self.open_dialog_params, doseq=True))

    @property
    def client_secret(self) -> str:
        return os.environ['AFFAIRE_CLIENT_SECRET']

    def authenticate(self):
        self._run_server()
        self._open_dialog()
        # TODO: join the thread
        # TODO: read get parameters at 'redirect_uri'

    def _run_server(self):
        pass

    def _open_dialog(self):
        webbrowser.open(self.authentication_link)
