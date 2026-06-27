# divera-monitor-linux

Einrichtungsanleitung und Skripte für die **DIVERA 24/7 Monitor-App** unter Debian 13 Trixie + LXDE, inklusive PIR-Bewegungsmelder-Integration via UDP-Broadcast.

Erstellt und eingesetzt bei der **Freiwilligen Feuerwehr Höhndorf**.

---

## Hintergrund

Die Divera Monitor-App wird auf dedizierten Rechnern als Einsatzmonitor betrieben. Ergänzt wird das Setup durch einen **PIR-Bewegungsmelder** (WEMOS D1 Mini / ESP8266), der nach der [offiziellen Divera-Anleitung](https://help.divera247.com/pages/viewpage.action?pageId=125960245) gebaut wurde und einen UDP-Broadcast auf Port 2311 mit der Nachricht `PIR Raised` sendet, sobald Bewegung erkannt wird.

### Das Problem

Der **Bildschirmschoner-Tab in Divera 2.3.1 unter Linux ist defekt** (bekanntes Problem, bestätigt durch Divera-Support). Die App kann den nativen UDP-Broadcast des Bewegungsmelders unter Linux nicht verarbeiten – der Bildschirmschoner lässt sich damit nicht steuern.

### Die Lösung

Anstatt den ESP-Bewegungsmelder anzupassen, lauschen wir selbst auf den UDP-Broadcast und steuern **xscreensaver direkt auf OS-Ebene**. Der ESP bleibt unverändert.

Zusätzlich wird bei **Alarmeingang** über die Divera-Skript-Integration ein Shell-Script ausgeführt, das denselben UDP-Broadcast lokal simuliert – so wird der Bildschirmschoner auch im Alarmfall zuverlässig deaktiviert.

Der `pir_listener.py` enthält außerdem einen eingebetteten **HTTP-Statusserver auf Port 8080**, der zur Überwachung via [Uptime Kuma](https://github.com/louislam/uptime-kuma) oder ähnlichen Tools genutzt werden kann.

---

## Voraussetzungen

- Debian 13 Trixie
- LXDE Desktop
- User `divera` mit sudo-Rechten
- DIVERA 24/7 Monitor-App 2.3.1

---

## Inhalt

```
divera-monitor-linux/
├── README.md
├── EINRICHTUNG.md               # Vollständige Schritt-für-Schritt-Anleitung
├── scripts/
│   ├── pir_listener.py          # UDP-Listener + HTTP-Statusserver
│   └── alarm_wakeup.sh          # Alarm-Wakeup für Divera Skript-Integration
└── systemd/
    ├── pir-listener.service     # systemd Service für pir_listener.py
    └── x11vnc.service           # systemd Service für VNC-Zugang
```

---

## Schnellstart

Vollständige Anleitung: **[EINRICHTUNG.md](EINRICHTUNG.md)**

### Skripte deployen

```bash
mkdir -p /home/divera/divera
cp scripts/pir_listener.py /home/divera/divera/
cp scripts/alarm_wakeup.sh /home/divera/divera/
chmod +x /home/divera/divera/pir_listener.py
chmod +x /home/divera/divera/alarm_wakeup.sh
```

### systemd Services einrichten

```bash
sudo cp systemd/pir-listener.service /etc/systemd/system/
sudo cp systemd/x11vnc.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pir-listener.service x11vnc.service
```

### Status prüfen

```bash
sudo systemctl status pir-listener.service x11vnc.service
curl http://localhost:8080
# Erwartete Antwort: {"status": "ok"}
```

---

## Monitoring

Der `pir_listener.py` stellt auf **Port 8080** einen HTTP-Endpunkt bereit:

| Endpunkt | Antwort |
|----------|---------|
| `GET /` | `{"status": "ok"}` mit HTTP 200 |

In Uptime Kuma: HTTP-Monitor auf `http://<IP>:8080`, Erwartung HTTP 200.

---

## Bekannte Probleme

| Problem | Ursache | Lösung |
|---------|---------|--------|
| Bildschirmschoner lässt sich nicht per App steuern | Bildschirmschoner-Tab in Divera 2.3.1 Linux defekt | pir_listener.py steuert xscreensaver direkt |
| Bildschirm bleibt im Alarmfall schwarz | App kann Screensaver nicht wecken | alarm_wakeup.sh via Divera Skript-Integration |
| Weißer Bildschirm nach der Nacht | Nächtliche IP-Neuvergabe des Providers | Optionaler Cronjob (siehe EINRICHTUNG.md) |

---

## Lizenz

MIT – frei nutzbar und anpassbar.
