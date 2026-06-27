#!/usr/bin/env python3
import socket
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

UDP_PORT = 2311
MESSAGE = "PIR Raised"
HTTP_PORT = 8080

class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

    def log_message(self, format, *args):
        pass  # HTTP Logs unterdrücken

def start_webserver():
    server = HTTPServer(("0.0.0.0", HTTP_PORT), StatusHandler)
    server.serve_forever()

# Webserver in eigenem Thread starten
thread = threading.Thread(target=start_webserver, daemon=True)
thread.start()
print(f"Statusseite läuft auf Port {HTTP_PORT}")

# UDP Listener
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(("", UDP_PORT))

print(f"Lausche auf UDP Port {UDP_PORT}...")

while True:
    data, addr = sock.recvfrom(1024)
    message = data.decode("utf-8", errors="ignore").strip()
    print(f"Empfangen von {addr}: {message}")
    if MESSAGE in message:
        print("Bewegung erkannt! Bildschirmschoner deaktivieren...")
        subprocess.run(["xscreensaver-command", "-deactivate"])
