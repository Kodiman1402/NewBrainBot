# ---------------------------------------------------------
# NEW BRAIN DASHBOARD - V5 (STRIKE CONFIG)
# Created by: Kodiman_Himself
# ---------------------------------------------------------

import streamlit as st
import json
import os
import requests
import time
from datetime import datetime

st.set_page_config(page_title="NEW BRAIN Admin", page_icon="🧠", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
BAN_LOG_FILE = os.path.join(BASE_DIR, 'banned_log.json')
CMD_LOG_FILE = os.path.join(BASE_DIR, 'cmd_log.json')
USER_DB_FILE = os.path.join(BASE_DIR, 'known_users.json')
WARN_DB_FILE = os.path.join(BASE_DIR, 'warnings.json')

def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    return {}

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

config = load_json(CONFIG_FILE)
bot_token = config.get("bot_token", "")

def telegram_api(method, params):
    if not bot_token: return False, "Kein Token"
    try:
        r = requests.post(f"https://api.telegram.org/bot{bot_token}/{method}", params=params)
        res = r.json()
        if res.get("ok"): return True, res
        else: return False, res.get("description")
    except Exception as e: return False, str(e)

def log_manual_ban(user_id, user_name, chat_id, chat_title, reason):
    entry = {
        "user_id": user_id, "user_name": user_name,
        "chat_id": chat_id, "chat_title": chat_title,
        "reason": reason, "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    }
    logs = load_json(BAN_LOG_FILE)
    if isinstance(logs, dict): logs = []
    logs.insert(0, entry)
    save_json(BAN_LOG_FILE, logs)

st.title("🧠 NEW BRAIN - Kommandozentrale")
st.markdown("### Version 5 | Created by **Kodiman_Himself**")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Setup")
    new_token = st.text_input("Bot Token", value=bot_token, type="password")
    admin_id = st.text_input("Deine Telegram ID", value=config.get("admin_id", ""))
    if st.button("Setup Speichern"):
        config["bot_token"] = new_token
        config["admin_id"] = admin_id
        save_json(CONFIG_FILE, config)
        st.success("Gespeichert!")
        st.rerun()
    st.markdown("---")
    st.info(f"Aktive Gruppe: {config.get('active_chat_title', 'Noch keine')}")

tab_admin, tab_bans, tab_sec, tab_cmd, tab_wel = st.tabs([
    "⚡ Admin Actions", "🚫 Gebannte User", "🛡️ Sicherheit & Strikes", "💬 Befehle & Timer", "👋 Begrüßung"
])

with tab_admin:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔨 Manueller Bann")
        chat_id = config.get("active_chat_id", "")
        known_users = load_json(USER_DB_FILE)
        options = {f"{name} (ID: {uid})": uid for uid, name in known_users.items()}
        sel = st.selectbox("User auswählen:", ["Bitte wählen..."] + list(options.keys()))
        target_id = ""
        target_name = "Manuell"
        if sel != "Bitte wählen...":
            target_id = options[sel]
            target_name = sel.split(" (ID:")[0]
        manual_in = st.text_input("... oder ID eingeben:", value=target_id)
        reason = st.text_input("Grund:", "Verstoß gegen Regeln")
        
        if st.button("Benutzer Bannen", type="primary"):
            if not chat_id: st.error("Bot kennt die Gruppe noch nicht!")
            elif not manual_in: st.error("Keine ID!")
            else:
                s, m = telegram_api("banChatMember", {"chat_id": chat_id, "user_id": manual_in, "revoke_messages": True})
                if s:
                    st.success(f"{target_name} gebannt!")
                    log_manual_ban(manual_in, target_name, chat_id, config.get("active_chat_title"), f"Manuell: {reason}")
                    if config.get("admin_id"):
                        telegram_api("sendMessage", {"chat_id": config.get("admin_id"), "text": f"🚨 **MANUELLER BANN**\nUser: {target_name}", "parse_mode": "Markdown"})
                else: st.error(f"Fehler: {m}")

    with c2:
        st.subheader("🧹 Chat Bereinigung")
        cmd_logs = load_json(CMD_LOG_FILE)
        st.metric("Gespeicherte Nachrichten", len(cmd_logs))
        if st.button("🧹 Alles Löschen Starten"):
            if not cmd_logs: st.info("Nichts zu löschen.")
            else:
                bar = st.progress(0)
                for i, e in enumerate(cmd_logs):
                    telegram_api("deleteMessage", {"chat_id": e['chat_id'], "message_id": e['message_id']})
                    bar.progress((i+1)/len(cmd_logs))
                    time.sleep(0.05)
                save_json(CMD_LOG_FILE, [])
                st.success("Fertig!")
                time.sleep(1)
                st.rerun()

with tab_bans:
    st.subheader("Sperrliste")
    logs = load_json(BAN_LOG_FILE)
    if not logs: st.info("Keine Einträge.")
    else:
        for i, e in enumerate(logs):
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 3, 2, 2])
                c1.write(f"**{e.get('user_name')}**")
                c2.write(f"Grund: {e.get('reason')}")
                c3.write(e.get('timestamp'))
                if c4.button("🔓 Entsperren", key=f"unban_{i}"):
                    s, m = telegram_api("unbanChatMember", {"chat_id": e['chat_id'], "user_id": e['user_id'], "only_if_banned": True})
                    if s:
                        st.success("Entsperrt!")
                        logs.pop(i)
                        save_json(BAN_LOG_FILE, logs)
                        st.rerun()
                    else: st.error(m)
                st.divider()

with tab_sec:
    st.subheader("⚖️ Verwarnungs-System (Strikes)")
    st.info("Wie viele Verstöße darf sich ein User erlauben, bevor er gebannt wird?")
    curr_max = config.get("max_strikes", 1)
    new_max = st.slider("Max. Verwarnungen (1 = Sofort Bann):", 1, 10, curr_max)
    
    if new_max != curr_max:
        config["max_strikes"] = new_max
        save_json(CONFIG_FILE, config)
        st.success(f"Eingestellt: Bann erfolgt ab Verstoß {new_max}.")
        time.sleep(1)
        st.rerun()

    st.divider()
    st.subheader("Verbotene Wörter (Blacklist)")
    current = ", ".join(config.get("banned_words", []))
    new_in = st.text_area("Wörter durch Komma trennen:", value=current, height=150)
    if st.button("Blacklist Speichern"):
        config["banned_words"] = [w.strip().lower() for w in new_in.split(",") if w.strip()]
        save_json(CONFIG_FILE, config)
        st.success("Gespeichert!")

with tab_cmd:
    st.subheader("⏲️ Timer")
    curr_timer = config.get("delete_timer", 300)
    new_timer = st.slider("Löschen nach (Sekunden):", 10, 3600, curr_timer, 10)
    if new_timer != curr_timer:
        config["delete_timer"] = new_timer
        save_json(CONFIG_FILE, config)
        st.toast("Timer gespeichert!")
    st.divider()
    st.subheader("Befehle")
    commands = config.get("commands", {})
    col1, col2 = st.columns([1, 2])
    new_cmd = col1.text_input("Neuer Befehl", placeholder="regeln")
    new_resp = col2.text_input("Antwort", placeholder="Hier sind die Regeln...")
    if st.button("Hinzufügen"):
        if new_cmd and new_resp:
            commands[new_cmd.lower()] = new_resp
            config["commands"] = commands
            save_json(CONFIG_FILE, config)
            st.rerun()
    st.write("Aktive Befehle:")
    for cmd, resp in list(commands.items()):
        cols = st.columns([1, 3, 1])
        cols[0].markdown(f"**/{cmd}**")
        cols[1].text(resp)
        if cols[2].button("🗑️", key=f"del_{cmd}"):
            del commands[cmd]
            config["commands"] = commands
            save_json(CONFIG_FILE, config)
            st.rerun()

with tab_wel:
    st.subheader("Begrüßung")
    msg = st.text_area("Text:", value=config.get("welcome_message", ""))
    wlc_timer = config.get("welcome_timer", 300)
    new_wlc = st.slider("Löschen nach:", 10, 86400, wlc_timer, 10)
    if st.button("Speichern"):
        config["welcome_message"] = msg
        config["welcome_timer"] = new_wlc
        save_json(CONFIG_FILE, config)
        st.success("Gespeichert!")
