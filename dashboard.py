# ---------------------------------------------------------
# NEW BRAIN DASHBOARD - V8 (ULTIMATE ADMIN)
# Created by: Kodiman_Himself
# ---------------------------------------------------------

import streamlit as st
import json
import os
import requests
import time
from datetime import datetime, date

st.set_page_config(page_title="NEW BRAIN Admin", page_icon="🧠", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
BAN_LOG_FILE = os.path.join(BASE_DIR, 'banned_log.json')
CMD_LOG_FILE = os.path.join(BASE_DIR, 'cmd_log.json')
USER_DB_FILE = os.path.join(BASE_DIR, 'known_users.json')
STATS_FILE = os.path.join(BASE_DIR, 'stats.json')
KARMA_FILE = os.path.join(BASE_DIR, 'karma.json')

def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

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
st.markdown("### Version 8 (Ultimate) | Created by **Kodiman_Himself**")
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

# NEUE TAB-STRUKTUR
tab_stats, tab_sec, tab_auto, tab_admin, tab_cmd, tab_wel = st.tabs([
    "📊 Statistik", "🛡️ Sicherheit", "📢 Automatisierung", "⚡ Admin & Bans", "💬 Befehle", "👋 Begrüßung"
])

# 1. STATISTIK
with tab_stats:
    c_left, c_right = st.columns(2)
    with c_left:
        st.subheader("Aktivitäts-Übersicht")
        stats = load_json(STATS_FILE)
        daily = stats.get("daily", {})
        users = stats.get("users", {})
        c1, c2 = st.columns(2)
        c1.metric("Nachrichten Heute", daily.get(str(date.today()), 0))
        c2.metric("Aktive Nutzer", len(users))
        
        st.divider()
        st.subheader("🏆 Top Chatter")
        if users:
            sorted_users = sorted(users.items(), key=lambda x: x[1], reverse=True)[:5]
            known = load_json(USER_DB_FILE)
            for uid, count in sorted_users:
                st.write(f"**{count}** Msgs: {known.get(uid, f'ID: {uid}')}")
    
    with c_right:
        st.subheader("🌟 Top Karma (Ehrenmänner)")
        karma = load_json(KARMA_FILE)
        if karma:
            sorted_k = sorted(karma.items(), key=lambda x: x[1], reverse=True)[:5]
            known = load_json(USER_DB_FILE)
            for uid, count in sorted_k:
                st.write(f"**{count}** Karma: {known.get(uid, f'ID: {uid}')}")
        else: st.info("Noch kein Karma vergeben.")

# 2. SICHERHEIT (Captcha, Links, Blacklist)
with tab_sec:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🤖 Anti-Bot Captcha")
        capt = config.get("captcha_active", False)
        new_capt = st.toggle("Captcha für neue User aktivieren", value=capt)
        if new_capt != capt:
            config["captcha_active"] = new_capt
            save_json(CONFIG_FILE, config)
            st.toast("Captcha-Einstellung gespeichert!")

        st.divider()
        st.subheader("🔗 Link-Schutz")
        prot = config.get("link_protection", False)
        new_prot = st.toggle("Links nur für Admins erlauben", value=prot)
        if new_prot != prot:
            config["link_protection"] = new_prot
            save_json(CONFIG_FILE, config)
            st.toast("Link-Schutz gespeichert!")

    with c2:
        st.subheader("⚖️ Strike-System (Timeouts)")
        st.caption("Ein Strike bevor das Limit erreicht ist, wird der User automatisch für 24h stummgeschaltet. Beim Limit = Bann.")
        curr_max = config.get("max_strikes", 3)
        new_max = st.slider("Max. Strikes:", 1, 10, curr_max)
        if new_max != curr_max:
            config["max_strikes"] = new_max
            save_json(CONFIG_FILE, config)
            st.toast("Strikes gespeichert!")
            
        st.divider()
        st.subheader("Blacklist")
        cur_bl = ", ".join(config.get("banned_words", []))
        new_bl = st.text_area("Wörter (Komma-getrennt):", value=cur_bl)
        if st.button("Blacklist Speichern"):
            config["banned_words"] = [w.strip().lower() for w in new_bl.split(",") if w.strip()]
            save_json(CONFIG_FILE, config)
            st.success("Gespeichert!")

# 3. AUTOMATISIERUNG (News & Nachtruhe)
with tab_auto:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📢 Auto News-Ticker")
        st.caption("Postet automatisch im Hintergrund.")
        news_act = config.get("news_active", False)
        new_news_act = st.toggle("News-Ticker aktivieren", value=news_act)
        
        news_msg = st.text_area("News Nachricht:", value=config.get("news_message", ""))
        news_int = st.slider("Intervall (Stunden):", 1, 48, config.get("news_interval", 12))
        
        if st.button("News Speichern"):
            config["news_active"] = new_news_act
            config["news_message"] = news_msg
            config["news_interval"] = news_int
            save_json(CONFIG_FILE, config)
            st.success("Gespeichert!")
            st.rerun()

    with c2:
        st.subheader("🌙 Nachtruhe-Modus")
        st.caption("Sperrt den Chat nachts für alle normalen User (löscht Nachrichten sofort).")
        nm_act = config.get("nightmode_active", False)
        new_nm_act = st.toggle("Nachtruhe aktivieren", value=nm_act)
        
        col_t1, col_t2 = st.columns(2)
        nm_start = col_t1.text_input("Startzeit (HH:MM):", value=config.get("nightmode_start", "23:00"))
        nm_end = col_t2.text_input("Endzeit (HH:MM):", value=config.get("nightmode_end", "07:00"))
        
        if st.button("Nachtruhe Speichern"):
            config["nightmode_active"] = new_nm_act
            config["nightmode_start"] = nm_start
            config["nightmode_end"] = nm_end
            save_json(CONFIG_FILE, config)
            st.success("Gespeichert!")
            st.rerun()

# 4. ADMIN & BANS
with tab_admin:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔨 Manueller Bann")
        chat_id = config.get("active_chat_id", "")
        known_users = load_json(USER_DB_FILE)
        options = {f"{name} (ID: {uid})": uid for uid, name in known_users.items()}
        sel = st.selectbox("User:", ["Bitte wählen..."] + list(options.keys()))
        target_id = "" if sel == "Bitte wählen..." else options[sel]
        manual_in = st.text_input("ID Eingabe:", value=target_id)
        reason = st.text_input("Grund:", "Verstoß")
        
        if st.button("Bannen", type="primary"):
            if not chat_id: st.error("Keine Gruppe aktiv!")
            elif not manual_in: st.error("Keine ID!")
            else:
                s, m = telegram_api("banChatMember", {"chat_id": chat_id, "user_id": manual_in, "revoke_messages": True})
                if s:
                    st.success("Gebannt!")
                    log_manual_ban(manual_in, sel.split(" (ID:")[0], chat_id, config.get("active_chat_title"), f"Manuell: {reason}")
                else: st.error(f"Fehler: {m}")
                
        st.divider()
        st.subheader("🧹 Chat Verlauf leeren")
        cmd_logs = load_json(CMD_LOG_FILE)
        st.metric("Gespeicherte Befehle", len(cmd_logs))
        if st.button("Alles Löschen"):
            bar = st.progress(0)
            for i, e in enumerate(cmd_logs):
                telegram_api("deleteMessage", {"chat_id": e['chat_id'], "message_id": e['message_id']})
                bar.progress((i+1)/len(cmd_logs))
                time.sleep(0.05)
            save_json(CMD_LOG_FILE, [])
            st.success("Fertig!")

    with c2:
        st.subheader("🚫 Sperrliste")
        logs = load_json(BAN_LOG_FILE)
        if not logs: st.info("Leer.")
        else:
            for i, e in enumerate(logs):
                st.write(f"**{e.get('user_name')}** ({e.get('timestamp')})")
                st.caption(e.get('reason'))
                if st.button("Entsperren", key=f"u_{i}"):
                    s, m = telegram_api("unbanChatMember", {"chat_id": e['chat_id'], "user_id": e['user_id'], "only_if_banned": True})
                    if s:
                        logs.pop(i)
                        save_json(BAN_LOG_FILE, logs)
                        st.rerun()
                st.markdown("---")

# 5. BEFEHLE
with tab_cmd:
    st.subheader("⏲️ Timer (Auto-Löschen)")
    ct = config.get("delete_timer", 300)
    nt = st.slider("Löschen nach (Sek):", 10, 3600, ct, 10)
    if nt != ct:
        config["delete_timer"] = nt
        save_json(CONFIG_FILE, config)
        st.toast("Timer gespeichert!")
        
    st.divider()
    st.subheader("Befehls-Editor")
    commands = config.get("commands", {})
    col1, col2 = st.columns([1, 2])
    nc = col1.text_input("Neuer Befehl (ohne /)")
    nr = col2.text_input("Antwort des Bots")
    if st.button("Hinzufügen"):
        if nc and nr:
            commands[nc.lower()] = nr
            config["commands"] = commands
            save_json(CONFIG_FILE, config)
            st.rerun()

    st.markdown("---")
    st.write("### Aktive Befehle:")
    for cmd, resp in list(commands.items()):
        cols = st.columns([1, 3, 1])
        with cols[0]: st.markdown(f"**/{cmd}**")
        with cols[1]: st.write(resp)
        with cols[2]:
            if st.button("Löschen 🗑️", key=f"del_{cmd}"):
                del commands[cmd]
                config["commands"] = commands
                save_json(CONFIG_FILE, config)
                st.rerun()
        st.divider()

# 6. WELCOME
with tab_wel:
    st.subheader("Begrüßung")
    wm = st.text_area("Text:", value=config.get("welcome_message", ""))
    wt = config.get("welcome_timer", 300)
    nw = st.slider("Timer (Begrüßung löschen nach Sek):", 10, 86400, wt, 10)
    if st.button("Speichern"):
        config["welcome_message"] = wm
        config["welcome_timer"] = nw
        save_json(CONFIG_FILE, config)
        st.success("Gespeichert!")
