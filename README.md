Markdown
# 🧠 NEW BRAIN BOT (v6.1)

**Created by Kodiman_Himself**

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/kodimanhimself)

Ein mächtiger, moderner Telegram Admin-Bot mit Web-Dashboard zur Verwaltung von Communities. Entwickelt für Linux-Server (Proxmox, VPS, Raspberry Pi).

---

## ✨ Features (v6.1)

* **📊 Statistik-Dashboard:** Live-Übersicht über Nachrichtenaktivität, Top-User und tägliche Statistiken.
* **🛡️ Link-Schutz:** Löscht automatisch Links von Nicht-Admins (konfigurierbar und ein/ausschaltbar).
* **⚖️ Strike-System:** Verwarnungen statt sofortigem Bann. Einstellbar von 1 (Sofortbann) bis 10 Verwarnungen.
* **⚡ Admin-Tools:** Bannen (mit Nachrichtenlöschung), Entbannen und Kicken direkt über Telegram oder das Web-Interface.
* **🧹 Auto-Clean:** Der Bot hält den Chat sauber und löscht Befehle sowie seine eigenen Antworten automatisch nach X Sekunden.
* **🖥️ Web-Interface:** Steuere alles bequem über den Browser (Streamlit).
* **📝 Befehls-Editor:** Erstelle eigene Befehle (z.B. `/regeln`) direkt im Dashboard.

---

## 🚀 Installation auf einem Linux Server

Diese Anleitung wurde für **Debian/Ubuntu** (und Proxmox LXC) geschrieben.

### 1. Vorbereitung
Stelle sicher, dass Git und Python installiert sind:
```bash
apt update && apt upgrade -y
apt install git python3 python3-pip python3-venv -y
2. Repository klonen
Lade den Bot auf deinen Server:

Bash
cd /root/
git clone [https://github.com/Kodiman1402/NewBrainBot.git](https://github.com/Kodiman1402/NewBrainBot.git)
cd NewBrainBot
3. Virtuelle Umgebung erstellen
Wir isolieren den Bot, damit das System sauber bleibt:

Bash
python3 -m venv venv
source venv/bin/activate
4. Abhängigkeiten installieren
Bash
pip install -r requirements.txt
⚙️ Konfiguration
Konfigurationsdatei erstellen:
Benenne die Beispiel-Konfiguration um, damit du sie bearbeiten kannst:

Bash
mv config_sample.json config.json
Daten eintragen:
Du kannst die Datei entweder jetzt im Terminal bearbeiten (nano config.json) ODER später bequem über das Web-Dashboard eingeben.

Bot Token: Bekommst du von @BotFather.

Admin ID: Deine eigene Telegram-ID (der Bot verrät sie dir später mit dem Befehl /id).

🤖 Autostart einrichten (Systemd Services)
Damit der Bot und das Dashboard auch weiterlaufen, wenn du das Terminal schließt (oder der Server neu startet), richten wir Systemd-Services ein.

Hinweis: Diese Pfade gehen davon aus, dass der Bot in /root/NewBrainBot liegt. Passe sie an, falls du einen anderen Ordner nutzt.

1. Bot Service erstellen
Erstelle die Datei:

Bash
nano /etc/systemd/system/newbrain-bot.service
Füge folgenden Inhalt ein:

Ini, TOML
[Unit]
Description=New Brain Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/NewBrainBot
ExecStart=/root/NewBrainBot/venv/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
2. Dashboard Service erstellen
Erstelle die Datei:

Bash
nano /etc/systemd/system/newbrain-gui.service
Füge folgenden Inhalt ein:

Ini, TOML
[Unit]
Description=New Brain Web Dashboard
After=network.target

[Service]
User=root
WorkingDirectory=/root/NewBrainBot
ExecStart=/root/NewBrainBot/venv/bin/streamlit run dashboard.py --server.port 8501
Restart=always

[Install]
WantedBy=multi-user.target
3. Services aktivieren und starten
Bash
systemctl daemon-reload
systemctl enable newbrain-bot
systemctl enable newbrain-gui
systemctl start newbrain-bot
systemctl start newbrain-gui
🎮 Benutzung
Telegram Befehle
/id - Zeigt deine ID oder die ID des Nutzers, auf den du antwortest (wichtig für die Einrichtung).

/ban - (Als Antwort auf eine Nachricht) Bannt den User sofort und löscht alle seine Nachrichten der letzten 48 Stunden.

Eigene Befehle - Du kannst im Dashboard beliebige Befehle (z.B. /hilfe, /regeln, /spenden) anlegen.

Web Dashboard
Öffne deinen Browser und gehe zu:
http://DEINE-SERVER-IP:8501

Hier kannst du:

Im Tab "Setup" (Sidebar) deinen Token und deine Admin-ID speichern.

Statistiken einsehen.

Den Link-Schutz aktivieren/deaktivieren.

User manuell bannen.

Timer für das automatische Löschen einstellen.

☕ Support
Gefällt dir das Projekt? Ich freue mich über einen Kaffee!

Lizenz: MIT License | Developer: Kodiman_Himself
