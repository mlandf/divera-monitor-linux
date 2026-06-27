# divera-monitor-linux

Vollständige Einrichtungsanleitung und Skripte für die **DIVERA 24/7 Monitor-App** unter Debian 13 Trixie + LXDE – von der Grundkonfiguration bis zum laufenden Einsatzmonitor mit PIR-Bewegungsmelder-Integration.

Erstellt und eingesetzt bei der **Freiwilligen Feuerwehr Höhndorf**.

---

## Was ist das hier?

Dieses Repository enthält alles, was ihr braucht, um einen dedizierten Rechner als Divera-Einsatzmonitor aufzusetzen – von Autologin über VNC-Fernzugriff bis hin zur automatischen Bildschirmsteuerung per Bewegungsmelder. Die Anleitung setzt eine fertige Debian-Installation voraus (Desktop: LXDE), alles weitere ist Schritt für Schritt dokumentiert.

Das Setup entstand aus einer Weiterentwicklung unserer bisherigen Lösung: Wir hatten bereits einen **PIR-Bewegungsmelder** (WEMOS D1 Mini / ESP8266) im Einsatz, der nach der [offiziellen Divera-Anleitung](https://help.divera247.com/pages/viewpage.action?pageId=125960245) gebaut wurde. Dieser sendet bei erkannter Bewegung einen UDP-Broadcast auf Port 2311 mit der Nachricht `PIR Raised`.

### Das Problem

Der **Bildschirmschoner-Tab in Divera 2.3.1 unter Linux ist defekt** – die App kann den UDP-Broadcast des Bewegungsmelders unter Linux nicht verarbeiten. Damit funktioniert die native Bildschirmsteuerung nicht.

### Die Lösung

Statt den ESP-Bewegungsmelder anzupassen, lauschen wir selbst auf den UDP-Broadcast und steuern **xscreensaver direkt auf OS-Ebene**. Der Bewegungsmelder bleibt vollständig unverändert.

Zusätzlich wird bei **Alarmeingang** über die Divera-Skript-Integration ein Shell-Script ausgeführt, das denselben Broadcast lokal simuliert – damit wird der Bildschirmschoner auch im Alarmfall zuverlässig deaktiviert.

Der `pir_listener.py` bringt außerdem einen eingebetteten **HTTP-Statusserver auf Port 8080** mit, der zur Überwachung via [Uptime Kuma](https://github.com/louislam/uptime-kuma) oder ähnlichen Tools genutzt werden kann.

---

## Voraussetzungen

- Debian 13 Trixie, frisch installiert
- Desktop-Umgebung: **LXDE** (kein GNOME, kein KDE)
- User `divera` mit sudo-Rechten angelegt
- SSH-Zugang eingerichtet
- DIVERA 24/7 Monitor-App 2.3.1

---

## Inhalt

```
divera-monitor-linux/
├── README.md
├── EINRICHTUNG.md               # Vollständige Schritt-für-Schritt-Anleitung
├── scripts/
│   ├── pir_listener.py          # UDP-Listener + HTTP-Statusserver (Port 8080)
│   ├── app_monitor.py           # App-Monitor HTTP-Statusserver (Port 8081)
│   └── alarm_wakeup.sh          # Alarm-Wakeup für Divera Skript-Integration
└── systemd/
    ├── pir-listener.service     # systemd Service für pir_listener.py
    ├── app-monitor.service      # systemd Service für app_monitor.py
    └── x11vnc.service           # systemd Service für VNC-Zugang
```

---

## Schnellstart

Die vollständige Anleitung mit allen Schritten findet ihr in **[EINRICHTUNG.md](EINRICHTUNG.md)**.

### Skripte deployen

```bash
mkdir -p /home/divera/divera
cp scripts/pir_listener.py /home/divera/divera/
cp scripts/app_monitor.py /home/divera/divera/
cp scripts/alarm_wakeup.sh /home/divera/divera/
chmod +x /home/divera/divera/pir_listener.py
chmod +x /home/divera/divera/app_monitor.py
chmod +x /home/divera/divera/alarm_wakeup.sh
```

### systemd Services einrichten

```bash
sudo cp systemd/pir-listener.service /etc/systemd/system/
sudo cp systemd/app-monitor.service /etc/systemd/system/
sudo cp systemd/x11vnc.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pir-listener.service app-monitor.service x11vnc.service
```

### Status prüfen

```bash
sudo systemctl status pir-listener.service app-monitor.service x11vnc.service
curl http://localhost:8080
curl http://localhost:8081
```

---

## Monitoring

Beide Skripte stellen HTTP-Endpunkte bereit, die sich einfach in [Uptime Kuma](https://github.com/louislam/uptime-kuma) oder ähnliche Monitoring-Tools einbinden lassen.

### Endpunkte

| Port | Skript | Beschreibung |
|------|--------|-------------|
| `8080` | `pir_listener.py` | PIR Listener läuft und hört auf UDP-Broadcasts |
| `8081` | `app_monitor.py` | Divera Monitor App läuft als Prozess |

### Wie funktioniert der App-Monitor?

`app_monitor.py` ist ein schlanker HTTP-Server, der bei jeder Anfrage per `pgrep` prüft ob der `Monitor.AppImage` Prozess auf dem System aktiv ist. Je nach Ergebnis antwortet er mit HTTP 200 oder HTTP 503:

```
# App läuft:
HTTP 200 → {"status": "ok"}

# App nicht gefunden:
HTTP 503 → {"status": "error", "message": "Monitor.AppImage not running"}
```

Da der HTTP-Status allein für Uptime Kuma bereits ausreicht (200 = UP, 503 = DOWN), kann man den Monitor einfach als **HTTP-Monitor** einrichten. Wer zusätzlich auf den JSON-Inhalt prüfen will, kann in Uptime Kuma den Monitortyp **HTTP(s) – Schlüsselwort** verwenden und als Schlüsselwort `"status": "ok"` eintragen – damit wird der Monitor nur dann als UP gewertet, wenn sowohl der HTTP-Statuscode 200 als auch das Schlüsselwort in der Antwort vorhanden sind.

### Uptime Kuma Konfiguration

**PIR Listener (Port 8080):**
- Typ: `HTTP(s)`
- URL: `http://<IP>:8080`
- Erwarteter HTTP-Status: `200`

**App Monitor (Port 8081):**
- Typ: `HTTP(s) – Schlüsselwort`
- URL: `http://<IP>:8081`
- Schlüsselwort: `"status": "ok"`
- Erwarteter HTTP-Status: `200`

---

## Bekannte Probleme

| Problem | Ursache | Lösung |
|---------|---------|--------|
| Bildschirmschoner lässt sich nicht per App steuern | Bildschirmschoner-Tab in Divera 2.3.1 Linux defekt | `pir_listener.py` steuert xscreensaver direkt auf OS-Ebene |
| Bildschirm bleibt im Alarmfall schwarz | App kann Screensaver nicht wecken | `alarm_wakeup.sh` via Divera Skript-Integration |
| Weißer Bildschirm nach der Nacht | Nächtliche IP-Neuvergabe des Providers | Optionaler Cronjob (siehe EINRICHTUNG.md) |

---

## Lizenz

MIT – frei nutzbar und anpassbar.
