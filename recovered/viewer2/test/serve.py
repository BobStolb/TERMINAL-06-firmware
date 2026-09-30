"""Static server for the tests: like `python3 -m http.server`, but text types say UTF-8, as the host does."""
import http.server, sys


class H(http.server.SimpleHTTPRequestHandler):
    extensions_map = dict(http.server.SimpleHTTPRequestHandler.extensions_map, **{
        ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
        ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml; charset=utf-8"})

    def log_message(self, *a):
        pass


http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
