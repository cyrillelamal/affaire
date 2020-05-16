import webbrowser
import threading
import os
from urllib import parse
from http.server import HTTPServer


from src.affaire.utils import VKAPIHandler


class AuthenticationServer:
    """
    Server that handles VK APIs.
    """
    AUTHORIZE_URL = 'http://oauth.vk.com/authorize'

    AUTH_URI = '/auth'

    @property
    def open_dialog_params(self) -> dict:
        return {
            'client_id': '7453330',
            'display': 'page',
            'redirect_uri': f'http://localhost:8080{self.AUTH_URI}',
            'scope': 'docs',
            'response_type': 'code',
            'v': '5.103'
        }

    @property
    def authentication_link(self) -> str:
        return self.AUTHORIZE_URL\
               + '?'\
               + parse.unquote(parse.urlencode(self.open_dialog_params))

    @property
    def client_secret(self) -> str:
        return os.environ['AFFAIRE_CLIENT_SECRET']  # TODO: where to save the secret?

    def authenticate(self):
        """

        :return:
        """
        print('auth')
        t = threading.Thread(target=self._run_server)
        # t.start()
        #
        # self._open_dialog()
        # t.join()

        res = VKAPIHandler.RESPONSE
        return {}
        # TODO: implement

    def synchronize(self):
        pass

    @staticmethod
    def _run_server():
        server_address = ('localhost', 8080)
        httpd = HTTPServer(server_address, VKAPIHandler)
        while True:
            httpd.handle_request()
            if VKAPIHandler.RESPONSE is not None:
                break

    def _open_dialog(self):
        webbrowser.open(self.authentication_link)
