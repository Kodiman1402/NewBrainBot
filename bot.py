# ---------------------------------------------------------
# NEW BRAIN BOT - V6 (SERVER EDITION)
# Created by: Kodiman_Himself
# ---------------------------------------------------------

import logging
import json
import asyncio
import os
from datetime import datetime, date
from telegram import Update, ChatMember
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Logging
logging.basicConfig(
    format='%(asctime)s - NEW BRAIN V6 - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Pfade
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')
BAN_LOG_FILE = os.path.join(BASE_DIR, 'banned_log.json')
CMD_LOG_FILE = os.path.join(BASE_DIR, 'cmd_log.json')
USER_DB_FILE = os.path.join(BASE_DIR, 'known_users.json')
WARN_DB_FILE = os.path.join(BASE_DIR, 'warnings.json')
STATS_FILE = os.path.join(BASE_DIR, 'stats.json')

# --- HELPER FUNKTIONEN ---

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

def update_known_user(user):
    users = load_json(USER_DB_FILE)
    user_label = f"{user.first_name}"
    if user.last_name: user_label += f" {user.last_name}"
    if user.username: user_label += f" (@{user.username})"
    users[str(user.id)] = user_label
    save_json(USER_DB_FILE, users)

def update_stats(user_id):
    """Statistik Zähler"""
    stats = load_json(STATS_FILE)
    today = str(date.today())
    
    if "daily" not in stats: stats["daily"] = {}
    if "users" not in stats: stats["users"] = {}
    
    # Heute +1
    stats["daily"][today] = stats["daily"].get(today, 0) + 1
    # User +1
    uid = str(user_id)
    stats["users"][uid] = stats["users"].get(uid, 0) + 1
    
    save_json(STATS_FILE, stats)

def add_warning(user_id):
    warns = load_json(WARN_DB_FILE)
    uid = str(user_id)
    current = warns.get(uid, 0)
    warns[uid] = current + 1
    save_json(WARN_DB_FILE, warns)
    return warns[uid]

def reset_warnings(user_id):
    warns = load_json(WARN_DB_FILE)
    if str(user_id) in warns:
        del warns[str(user_id)]
        save_json(WARN_DB_FILE, warns)

def log_ban(user_id, user_name, chat_id, chat_title, reason):
    entry = {
        "user_id": user_id, "user_name": user_name,
        "chat_id": chat_id, "chat_title": chat_title,
        "reason": reason, "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    }
    logs = load_json(BAN_LOG_FILE)
    if isinstance(logs, dict): logs = []
    logs.insert(0, entry)
    save_json(BAN_LOG_FILE, logs)

def log_command_id(chat_id, message_id):
    entry = {"chat_id": chat_id, "message_id": message_id}
    logs = load_json(CMD_LOG_FILE)
    if isinstance(logs, dict): logs = []
    logs.append(entry)
    save_json(CMD_LOG_FILE, logs)

async def delete_later(message, delay):
    if not message: return
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except: pass

async def is_user_admin(chat, user_id):
    try:
        member = await chat.get_member(user_id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except: return False

# --- LOGIC ---

async def handle_dynamic_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    text = update.message.text
    if not text.startswith('/'): return
    
    user = update.effective_user
    chat = update.effective_chat
    config = load_json(CONFIG_FILE)
    
    update_known_user(user)
    update_stats(user.id)
    log_command_id(chat.id, update.message.message_id)

    # Timer für Befehle IMMER starten
    timer = config.get('delete_timer', 300)
    asyncio.create_task(delete_later(update.message, timer))

    # Klick-Fix: Alles nach @ abschneiden
    raw_command = text.split()[0] 
    command_clean = raw_command[1:]
    if '@' in command_clean:
        command_clean = command_clean.split('@')[0]
    
    command_trigger = command_clean.lower()
    admin_id_str = str(config.get("admin_id", ""))
    
    # 1. /id
    if command_trigger == "id":
        if update.message.reply_to_message:
            target = update.message.reply_to_message.from_user
            msg = await update.message.reply_text(f"👤 User: {target.first_name}\n🆔 ID: `{target.id}`", parse_mode='Markdown')
        else:
            msg = await update.message.reply_text(f"Deine ID: `{user.id}`\nGruppe ID: `{chat.id}`", parse_mode='Markdown')
        log_command_id(chat.id, msg.message_id)
        asyncio.create_task(delete_later(msg, 30))
        return

    # 2. /ban
    if command_trigger == "ban":
        if str(user.id) != admin_id_str: return
        if update.message.reply_to_message:
            target_msg = update.message.reply_to_message
            target_user = target_msg.from_user
            try:
                # Versuch Nachricht zu löschen
                try: await target_msg.delete()
                except: pass
                
                # Bannen + Verlauf löschen
                await chat.ban_member(target_user.id, revoke_messages=True)
                
                succ_msg = await update.message.reply_text(f"🔨 {target_user.first_name} gebannt & bereinigt!")
                log_ban(target_user.id, target_user.first_name, chat.id, chat.title, "Admin Befehl /ban")
                asyncio.create_task(delete_later(succ_msg, 10))

                if admin_id_str:
                    try: await context.bot.send_message(chat_id=admin_id_str, text=f"🚨 **MANUELLER BANN**\nAdmin: {user.first_name}\nOpfer: {target_user.first_name}", parse_mode='Markdown')
                    except: pass
            except Exception as e:
                err_msg = await update.message.reply_text(f"Fehler: {e}")
                asyncio.create_task(delete_later(err_msg, 10))
        return

    # 3. Custom Commands
    commands_dict = config.get('commands', {})
    if command_trigger in commands_dict:
        bot_reply = await update.message.reply_text(commands_dict[command_trigger])
        log_command_id(chat.id, bot_reply.message_id)
        asyncio.create_task(delete_later(bot_reply, timer))

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = load_json(CONFIG_FILE)
    if config.get("active_chat_id") != update.effective_chat.id:
        config["active_chat_id"] = update.effective_chat.id
        config["active_chat_title"] = update.effective_chat.title
        save_json(CONFIG_FILE, config)

    for member in update.message.new_chat_members:
        if member.id == context.bot.id: continue
        update_known_user(member)
        msg_text = config.get('welcome_message', 'Willkommen.')
        sent = await update.message.reply_text(f"👋 Hallo {member.first_name}!\n\n{msg_text}")
        timer = config.get('welcome_timer', 300)
        asyncio.create_task(delete_later(sent, timer))

async def monitor_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    if update.message.text.startswith('/'): return
    
    user = update.effective_user
    chat = update.effective_chat
    update_known_user(user)
    update_stats(user.id)
    
    config = load_json(CONFIG_FILE)
    if config.get("active_chat_id") != chat.id:
        config["active_chat_id"] = chat.id
        config["active_chat_title"] = chat.title
        save_json(CONFIG_FILE, config)

    text = update.message.text.lower()

    # --- 1. LINK SCHUTZ ---
    if config.get("link_protection", False):
        if "http://" in text or "https://" in text or "www." in text or ".com" in text or ".de" in text or "t.me" in text:
            # Admins & Owner dürfen Links
            is_admin = await is_user_admin(chat, user.id)
            is_bot_owner = str(user.id) == str(config.get("admin_id", ""))
            
            if not is_admin and not is_bot_owner:
                try:
                    await update.message.delete()
                    warn = await chat.send_message(f"⚠️ {user.first_name}, Links sind hier nur für Admins!")
                    asyncio.create_task(delete_later(warn, 30))
                    return 
                except Exception as e:
                    logger.error(f"Link Delete Error: {e}")

    # --- 2. WORT FILTER & STRIKES ---
    banned_words = config.get('banned_words', [])
    max_strikes = config.get('max_strikes', 1) 
    
    for word in banned_words:
        if word in text:
            try:
                await update.message.delete()
                strikes = add_warning(user.id)
                
                if strikes >= max_strikes:
                    await chat.ban_member(user.id, revoke_messages=True)
                    log_ban(user.id, user.first_name, chat.id, chat.title, f"{word} (Strike {strikes}/{max_strikes})")
                    reset_warnings(user.id)
                    
                    ban_msg = await chat.send_message(f"⛔ {user.first_name} wurde gebannt! (Grund: {word})")
                    asyncio.create_task(delete_later(ban_msg, 60))
                    
                    if config.get("admin_id"):
                        try: await context.bot.send_message(chat_id=config.get("admin_id"), text=f"🚨 **BANN (Limit)**\nUser: {user.first_name}\nWort: {word}", parse_mode='Markdown')
                        except: pass
                else:
                    warn_msg = await chat.send_message(f"⚠️ {user.first_name}, das Wort '{word}' ist verboten! ({strikes}/{max_strikes})")
                    asyncio.create_task(delete_later(warn_msg, 30))
                break
            except Exception as e:
                logger.error(f"Ban/Warn Error: {e}")

def main():
    config = load_json(CONFIG_FILE)
    token = config.get('bot_token')
    if not token: return
    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor_chat))
    app.add_handler(MessageHandler(filters.COMMAND, handle_dynamic_commands))
    app.run_polling()

if __name__ == '__main__':
    main()
