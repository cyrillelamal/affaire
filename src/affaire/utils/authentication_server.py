import webbrowser
import threading
import os
from urllib import parse
from http.server import HTTPServer, BaseHTTPRequestHandler


class Handler(BaseHTTPRequestHandler):
    """
    API responses handler
    """
    RESPONSE = None  # type: dict

    def do_GET(self):
        query = parse.urlsplit(self.path).query
        params = parse.parse_qs(query)

        if self.path.startswith('/auth'):
            self.send_response(200)
            self.send_header('content-type', 'application/json')
            self.end_headers()
            self.wfile.write(str(params).encode('utf8'))
        else:
            self.html_response(
                "Hey buddy, I think you've got the wrong door, "
                "the leather club's two blocks down",
                418
            )
        Handler.RESPONSE = params

    def html_response(self, html: str, code: int):
        self.send_response(code)
        self.send_header('content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf8'))


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
        t = threading.Thread(target=self._run_server)
        # t.start()

        # self._open_dialog()
        # t.join()

        res = Handler.RESPONSE
        # TODO: uncomment and implement

    @staticmethod
    def _run_server():
        server_address = ('localhost', 8080)
        httpd = HTTPServer(server_address, Handler)
        while True:
            httpd.handle_request()
            if Handler.RESPONSE is not None:
                break

    def _open_dialog(self):
        webbrowser.open(self.authentication_link)


AuthenticationServer().authenticate()
