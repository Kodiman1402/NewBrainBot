# 🧠 NEW BRAIN BOT (v8.0 - Ultimate Admin)

**Created by Kodiman_Himself**

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/kodimanhimself)

Ein mächtiger, moderner Telegram Admin-Bot mit Web-Dashboard zur Verwaltung von Communities. Entwickelt für Linux-Server (Proxmox LXC, VPS, Raspberry Pi, Debian/Ubuntu).

---

## ✨ Features (v8.0)

* **🤖 Anti-Bot Captcha:** Neue User müssen einen Button klicken, um zu beweisen, dass sie Menschen sind (sonst erfolgt ein stummer Kick nach 2 Min).
* **🌟 Gamification & Karma:** Level-Up System bei Nachrichten-Meilensteinen. User können sich mit `+1` oder `Danke` Karma geben (`/karma` Ranking).
* **📊 Statistik & Leaderboard:** Live-Übersicht im Dashboard und Top-Chatter Ranking per Befehl (`/top`).
* **⏳ Timeout-Strikes:** Bevor ein User gebannt wird, erhält er bei Warnungen (z.B. Blacklist-Wörter) automatische 24h-Stummschaltungen zur Abkühlung.
* **🌙 Nachtruhe-Modus:** Sperrt den Chat nachts automatisch für alle normalen User (Zeiten frei wählbar).
* **📢 Auto News-Ticker:** Sendet vollautomatisch in festgelegten Intervallen deine News, Links oder Werbung in die Gruppe.
* **🛡️ Link-Schutz:** Löscht automatisch Links von Nicht-Admins.
* **🖥️ Web-Interface:** Steuere alles, inklusive Blacklist und Custom-Commands, bequem über den Browser (Streamlit).

---

## 🚀 Detaillierte Installation (Linux Server)

Diese Anleitung führt dich Schritt für Schritt durch die Installation auf einem frischen Linux-System (Debian/Ubuntu). Es wird vorausgesetzt, dass du als `root` User angemeldet bist.

### 1. System aktualisieren & Pakete installieren
Zuerst bringen wir das System auf den neuesten Stand und installieren Git sowie Python3.
```bash
apt update && apt upgrade -y
apt install git python3 python3-pip python3-venv nano -y
```

### 2. Repository klonen
Wir laden den Code von GitHub herunter und wechseln in das Verzeichnis. Der Ordner wird `/root/new_brain` heißen.
```bash
cd /root/
git clone [https://github.com/Kodiman1402/NewBrainBot.git](https://github.com/Kodiman1402/NewBrainBot.git) new_brain
cd new_brain
```

### 3. Virtuelle Umgebung (venv) einrichten
Um Konflikte mit anderen System-Paketen zu vermeiden, erstellen wir eine isolierte Python-Umgebung für den Bot.
```bash
python3 -m venv venv
source venv/bin/activate
```
*(Dein Terminal-Prompt sollte nun mit `(venv)` beginnen).*

### 4. Abhängigkeiten installieren
Jetzt installieren wir die benötigten Python-Bibliotheken (Telegram-API, Streamlit fürs Dashboard etc.).
```bash
pip install -r requirements.txt
```

### 5. Konfiguration vorbereiten
Wir kopieren die Muster-Konfigurationsdatei, damit der Bot seine Datenbank anlegen kann.
```bash
cp config_sample.json config.json
```
*(Hinweis: Du musst die `config.json` nicht manuell bearbeiten. Du kannst den Bot Token und deine Admin-ID später bequem über das Web-Dashboard eintragen!)*

---

## 🤖 Autostart einrichten (Systemd Services)

Damit der Bot und das Dashboard dauerhaft im Hintergrund laufen und nach einem Server-Neustart automatisch wieder anspringen, richten wir zwei Dienste ein.

### 1. Bot Service erstellen
```bash
nano /etc/systemd/system/newbrain-bot.service
```
Füge folgenden Inhalt ein (Speichern mit `STRG+O`, `Enter`, Schließen mit `STRG+X`):
```ini
[Unit]
Description=New Brain Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/new_brain
ExecStart=/root/new_brain/venv/bin/python3 bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Dashboard Service erstellen
```bash
nano /etc/systemd/system/newbrain-gui.service
```
Füge folgenden Inhalt ein:
```ini
[Unit]
Description=New Brain Web Dashboard
After=network.target

[Service]
User=root
WorkingDirectory=/root/new_brain
ExecStart=/root/new_brain/venv/bin/streamlit run dashboard.py --server.port 8501
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Services aktivieren und starten
Jetzt sagen wir dem System, dass es diese neuen Dienste laden und starten soll:
```bash
systemctl daemon-reload
systemctl enable newbrain-bot
systemctl enable newbrain-gui
systemctl start newbrain-bot
systemctl start newbrain-gui
```

---

## 🌍 Firewall & Zugriff (WICHTIG)

Das Web-Dashboard läuft auf Port **8501**. Wenn du eine Firewall (wie `ufw`) aktiv hast, musst du diesen Port freigeben:
```bash
ufw allow 8501/tcp
```

Öffne nun deinen Browser und rufe das Dashboard auf:
👉 **`http://<DEINE-SERVER-IP>:8501`**

Dort gehst du links in der Sidebar auf **Setup** und trägst deinen Telegram Bot Token (von [@BotFather](https://t.me/BotFather)) und deine Telegram User-ID ein.

---

## 🎮 Benutzung & Wichtige Befehle

**Für Administratoren:**
* **Bot-Rechte:** Stelle sicher, dass der Bot in deiner Telegram-Gruppe als Administrator hinzugefügt wurde und zwingend das Recht **"Nachrichten löschen"** sowie **"Benutzer sperren"** hat!
* `/ban` - Antworte auf die Nachricht eines Users mit `/ban`, um ihn sofort zu bannen und seine letzten Nachrichten zu löschen.

**Für User (Gamification):**
* `/top` oder `/ranking` - Zeigt die 5 aktivsten User (Nachrichten).
* `/karma` oder `/ehrenmann` - Zeigt die 5 User mit dem meisten Karma.
* `+1`, `Danke`, `👍` - Als Antwort auf eine hilfreiche Nachricht schreiben, um dem Helfer Karma zu geben.

---
**Lizenz:** MIT License | **Developer:** Kodiman_Himself
