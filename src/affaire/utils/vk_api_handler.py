from urllib import parse
from http.server import BaseHTTPRequestHandler


# noinspection PyPep8Naming
class VKAPIHandler(BaseHTTPRequestHandler):
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
        VKAPIHandler.RESPONSE = params

    def html_response(self, html: str, code: int):
        self.send_response(code)
        self.send_header('content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf8'))