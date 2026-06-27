# Divera Einsatzmonitor – Einrichtungsanleitung
**Debian 13 Trixie + LXDE**

---

## 1. Debian Installation

- Desktop: Debian desktop environment + LXDE + Standard-Systemwerkzeuge
- Kein GNOME, kein KDE – LXDE ist leichtgewichtig und ausreichend

---

## 2. Grundsystem einrichten

```bash
# Als root: sudo installieren und User Rechte geben
apt install sudo -y
adduser divera sudo

# SSH installieren
apt install openssh-server -y
```

---

## 3. Autologin einrichten (LightDM)

```bash
sudo nano /etc/lightdm/lightdm.conf
```

Inhalt:

```ini
[Seat:*]
autologin-user=divera
autologin-user-timeout=0
```

Nach dem Reboot prüfen ob LXDE-Session läuft:

```bash
ps aux | grep lxsession
```

---

## 4. Automatische Updates deaktivieren

Updates werden über Patchmon verwaltet, daher automatische Updates komplett deaktivieren:

```bash
sudo systemctl disable apt-daily.timer apt-daily-upgrade.timer
sudo systemctl stop apt-daily.timer apt-daily-upgrade.timer
```

Prüfen ob noch Timer aktiv sind:

```bash
systemctl list-timers | grep apt
```

> Sollte leer sein – fertig.

---

## 5. Divera Abhängigkeiten installieren

```bash
sudo apt install libfuse2 vlc xdotool xscreensaver dbus notification-daemon -y
```

---

## 6. Divera Monitor App installieren

```bash
# Herunterladen
wget -O ~/Monitor.AppImage "https://s3.florian.divera247.de/public/software/monitor/DIVERA247-Monitor-2.3.1-x86_64.AppImage"

# In sauberen Ordner verschieben
mkdir -p /home/divera/divera
mv ~/Monitor.AppImage /home/divera/divera/Monitor.AppImage

# Ausführbar machen
chmod +x /home/divera/divera/Monitor.AppImage
```

---

## 7. VNC-Zugang einrichten

Da ein Site-to-Site-Tunnel zum Monitor besteht, reicht VNC als einfache und schlanke Lösung – kein unnötiger Overhead.

```bash
sudo apt install x11vnc -y
```

Passwort setzen (max. 8 Zeichen!):

```bash
x11vnc -storepasswd
```

Als systemd Service:

```bash
sudo nano /etc/systemd/system/x11vnc.service
```

Inhalt:

```ini
[Unit]
Description=x11vnc VNC Server
After=graphical.target lightdm.service

[Service]
Type=simple
User=divera
Environment=DISPLAY=:0
ExecStart=/usr/bin/x11vnc -display :0 -rfbauth /home/divera/.vnc/passwd -forever -loop -noxdamage -repeat -rfbport 5900 -shared
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable x11vnc.service
sudo systemctl start x11vnc.service
```

> Verbindung: Port 5900, landet direkt in der LXDE-Session von User divera.

---

## 8. Divera Autostart einrichten

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/divera.desktop
```

Inhalt:

```ini
[Desktop Entry]
Type=Application
Exec=/home/divera/divera/Monitor.AppImage
```

---

## 9. Xscreensaver einrichten

```bash
nano ~/.config/autostart/xscreensaver.desktop
```

Inhalt:

```ini
[Desktop Entry]
Type=Application
Exec=xscreensaver -no-splash
```

In `xscreensaver-demo` den Modus auf **Blank Screen Only** setzen. Bei der Frage nach light-locker auf **Kill** klicken.

---

## 10. PIR Bewegungsmelder Listener

Der Bewegungsmelder (WEMOS D1 Mini) sendet einen UDP-Broadcast auf Port 2311 mit der Nachricht `PIR Raised`. Da der Bildschirmschoner-Tab in Divera 2.3.1 unter Linux defekt ist (bekanntes Problem laut Divera), lauschen wir selbst darauf und steuern xscreensaver direkt.

Der Listener enthält zusätzlich einen eingebetteten HTTP-Statusserver auf Port 8080 zur Überwachung via Uptime Kuma.

```bash
nano /home/divera/divera/pir_listener.py
```

Inhalt:

```python
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
```

```bash
chmod +x /home/divera/divera/pir_listener.py
```

Als systemd Service:

```bash
sudo nano /etc/systemd/system/pir-listener.service
```

Inhalt:

```ini
[Unit]
Description=Divera PIR Bewegungsmelder Listener
After=network.target graphical.target

[Service]
Type=simple
User=divera
Environment=DISPLAY=:0
ExecStart=/usr/bin/python3 /home/divera/divera/pir_listener.py
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable pir-listener.service
sudo systemctl start pir-listener.service
```

Testen (UDP Broadcast simulieren):

```bash
python3 -c "
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.sendto(b'PIR Raised', ('255.255.255.255', 2311))
print('Gesendet!')
"
```

HTTP Status testen:

```bash
curl http://localhost:8080
# Erwartete Antwort: {"status": "ok"}
```

> Uptime Kuma: HTTP Monitor auf `http://<IP>:8080`, erwartet HTTP 200.

---

## 11. Alarm Wakeup Script (Divera Skript-Integration)

Da der Bildschirmschoner-Tab in Divera 2.3.1 unter Linux defekt ist, wird bei Alarmeingang ein Shell-Script ausgeführt, das den PIR Listener direkt triggert und so den Bildschirmschoner deaktiviert.

```bash
nano /home/divera/divera/alarm_wakeup.sh
```

Inhalt:

```bash
#!/bin/bash
python3 -c "
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.sendto(b'PIR Raised', ('127.0.0.1', 2311))
"
```

```bash
chmod +x /home/divera/divera/alarm_wakeup.sh
```

In der Divera App einrichten:

- **Einstellungen → Skripte**
- Script: `/home/divera/divera/alarm_wakeup.sh`
- Zeitpunkt: **Bei Alarmeingang**

---

## Bekannte Probleme

- **Bildschirmschoner-Tab in Divera 2.3.1 auf Linux ist defekt** – wird durch PIR Listener auf OS-Ebene umgangen. Alarm-Wakeup über Skript-Integration (Schritt 11).
- **Weißer Bildschirm nach der Nacht** durch nächtliche IP-Neuvergabe des Providers (bisher nicht aufgetreten) – bei Bedarf automatischen Neustart der App nachts per Cronjob einrichten:

```bash
crontab -e
```

Eintrag:

```
0 3 * * * DISPLAY=:0 pkill -f Monitor.AppImage; sleep 5; /home/divera/divera/Monitor.AppImage &
```

---

## Verzeichnisstruktur

```
/home/divera/divera/
├── Monitor.AppImage
├── pir_listener.py
└── alarm_wakeup.sh

~/.config/autostart/
├── divera.desktop
└── xscreensaver.desktop

/etc/systemd/system/
├── pir-listener.service
└── x11vnc.service
```
