#!/usr/bin/env python3
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

HTTP_PORT = 8081

class AppMonitorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        result = subprocess.run(
            ["pgrep", "-f", "Monitor.AppImage"],
            capture_output=True
        )
        if result.returncode == 0:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "error", "message": "Monitor.AppImage not running"}')

    def log_message(self, format, *args):
        pass

server = HTTPServer(("0.0.0.0", HTTP_PORT), AppMonitorHandler)
print(f"App Monitor läuft auf Port {HTTP_PORT}")
server.serve_forever()
