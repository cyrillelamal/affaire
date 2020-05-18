import webbrowser
import threading
import json
import os
from urllib import parse, request, error
from http.server import HTTPServer

from src.affaire.utils import APIHandler


class AuthenticationServer:
    """
    Server that handles Google APIs.
    """
    PORT = 8080

    GOOGLE_OAUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
    GOOGLE_EXCHANGE_CODE_ENDPOINT = 'https://oauth2.googleapis.com/token'

    CLIENT_ID = '910652228964-tcj77oha783fj8ko6bev0je5afr0k8o4.apps.googleusercontent.com'
    REDIRECT_URI = f'http://localhost:{PORT}'
    RESPONSE_TYPE = 'code'
    SCOPES = 'https://www.googleapis.com/auth/drive'
    STATE = 'google-auth'

    def __init__(self):
        self.res = dict()  # api responses
        self.code = str()
        self.access_token = str()

    @property
    def authorization_parameters(self) -> dict:
        return {
            'client_id': self.CLIENT_ID,
            'redirect_uri': self.REDIRECT_URI,
            'response_type': 'code',
            'scope': 'https://www.googleapis.com/auth/drive'
        }

    @property
    def access_token_params(self) -> dict:
        return {
            'client_id': self.CLIENT_ID,
            'client_secret': os.environ['AFFAIRE_SECRET'],
            'code': self.res['code'][0],
            'grant_type': 'authorization_code',
            'redirect_uri': self.REDIRECT_URI
        }

    def authenticate(self):
        """
        Open authentication dialog and exchange the code
        :return:
        """
        # Step 1: Set authorization parameters
        # Step 2: Redirect to Google's OAuth 2.0 server
        thread = self._redirect_to_oauth()
        # Step 3: Google prompts user for consent
        thread.join()
        # Step 4: Handle the OAuth 2.0 server response
        self._handle_code()  # server's thread is joined
        # Step 5: Exchange authorization code for refresh and access tokens
        if 'error' not in self.res:
            self._exchange_code()

        # after the fifth step 'res' property contains either {'error'} or {'access_token'}
        return self

    def synchronize(self, model, fetch_mode, access_token):
        """
        Upload to the remote server.
        :return:
        """
        from src.affaire.controllers import AffaireController

        self.access_token = access_token  # ready to do requests

        if fetch_mode == AffaireController.GOOGLE_PUSH:
            # push: creates a new file
            task_list = [t.__dict__ for t in model.select()]
            json_data = json.dumps(task_list).encode('utf-8')
            length = len(json_data)

            uri = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=media'
            req = request.Request(uri)
            req.add_header('Content-Type', 'application/json')
            req.add_header('Content-Length', str(length))
            req.add_header('authorization', f'Bearer {self.access_token}')

            try:
                res = json.loads((request.urlopen(req, json_data).read()).decode('utf-8'))
                last_file_id = res.get('id')
                return last_file_id
            except error.HTTPError:
                pass
        else:  # elif fetch_mode == AffaireController.GOOGLE_FETCH:
            pass  # TODO: implement

    def _redirect_to_oauth(self):
        thread = self._run_server()
        thread.start()

        url = self.GOOGLE_OAUTH_ENDPOINT + '?' + parse.urlencode(self.authorization_parameters)
        webbrowser.open(url)

        return thread

    def _handle_code(self):
        """
        Load response. It can contain errors or code
        :return:
        """
        self.res = APIHandler.RESPONSE

    def _exchange_code(self):
        self.code = self.res.get('code')
        data = parse.urlencode(self.access_token_params).encode('utf-8')
        res = request.urlopen(self.GOOGLE_EXCHANGE_CODE_ENDPOINT, data=data).read()
        self.res = json.loads(res.decode('utf-8'))

    @staticmethod
    def _run_server():
        def server():
            server_address = ('localhost', AuthenticationServer.PORT)
            httpd = HTTPServer(server_address, APIHandler)
            while True:
                httpd.handle_request()
                if APIHandler.RESPONSE is not None:
                    break

        return threading.Thread(target=server)

    def _fetch_data(self, model):
        pass
