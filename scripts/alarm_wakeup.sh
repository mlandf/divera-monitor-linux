#!/bin/bash
# Wird von der Divera App bei Alarmeingang ausgeführt.
# Simuliert einen PIR-Broadcast um den Bildschirmschoner via pir_listener.py zu deaktivieren.
# Workaround: Bildschirmschoner-Tab in Divera 2.3.1 unter Linux ist defekt.

python3 -c "
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.sendto(b'PIR Raised', ('127.0.0.1', 2311))
"
