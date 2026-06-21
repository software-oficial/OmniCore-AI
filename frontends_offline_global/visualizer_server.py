import http.server
import socketserver
import urllib.error
import urllib.request

PORT = 8000
BACKEND_URL = "https://api.automatizacion-whatsapp.com"


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        self.handle_proxy()

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.handle_proxy()
        else:
            super().do_GET()

    def handle_proxy(self):
        # Redirigir /api/ a BACKEND_URL/dashboard/api/
        target_url = self.path.replace("/api/", "/dashboard/api/")
        url = BACKEND_URL + target_url

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else None

        req = urllib.request.Request(url, data=post_data, method=self.command)
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req) as response:
                self.send_response(response.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(response.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read())


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
        print(f"Proxy Server started on port {PORT} -> {BACKEND_URL}")
        httpd.serve_forever()
