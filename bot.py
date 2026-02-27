# ---------------------------------------------------------
# NEW BRAIN BOT - V8 (THE ULTIMATE ADMIN UPDATE)
# Created by: Kodiman_Himself
# Bugfixes applied
# ---------------------------------------------------------

import logging
import json
import asyncio
import os
import time
from datetime import datetime, date, timedelta
from telegram import Update, ChatMember, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Logging
logging.basicConfig(
    format='%(asctime)s - NEW BRAIN V8 - %(levelname)s - %(message)s',
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
KARMA_FILE = os.path.join(BASE_DIR, 'karma.json')

pending_captchas = set()

# --- HELPER FUNKTIONEN ---

def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)

def update_known_user(user):
    users = load_json(USER_DB_FILE)
    user_label = f"{user.first_name}"
    if user.last_name: user_label += f" {user.last_name}"
    if user.username: user_label += f" (@{user.username})"
    users[str(user.id)] = user_label
    save_json(USER_DB_FILE, users)

def update_stats(user_id):
    stats = load_json(STATS_FILE)
    today = str(date.today())
    if "daily" not in stats: stats["daily"] = {}
    if "users" not in stats: stats["users"] = {}
    stats["daily"][today] = stats["daily"].get(today, 0) + 1
    uid = str(user_id)
    stats["users"][uid] = stats["users"].get(uid, 0) + 1
    save_json(STATS_FILE, stats)
    return stats["users"][uid]

def add_karma(user_id):
    karma = load_json(KARMA_FILE)
    uid = str(user_id)
    karma[uid] = karma.get(uid, 0) + 1
    save_json(KARMA_FILE, karma)
    return karma[uid]

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

# --- BACKGROUND TASKS ---
async def custom_news_loop(app: Application):
    while True:
        await asyncio.sleep(60)
        config = load_json(CONFIG_FILE)
        if config.get("news_active", False) and config.get("active_chat_id"):
            last_sent = config.get("news_last_sent", 0)
            interval_hours = config.get("news_interval", 12)
            now = time.time()
            if now - last_sent > interval_hours * 3600:
                try:
                    await app.bot.send_message(
                        chat_id=config.get("active_chat_id"), 
                        text=config.get("news_message", "Hier könnten Ihre News stehen.")
                    )
                    config["news_last_sent"] = now
                    save_json(CONFIG_FILE, config)
                except Exception as e: logger.error(f"News Ticker Error: {e}")

async def post_init(application: Application):
    asyncio.create_task(custom_news_loop(application))

# --- LOGIC ---

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data.startswith("captcha_"):
        target_id = int(data.split("_")[1])
        if query.from_user.id == target_id:
            if target_id in pending_captchas:
                pending_captchas.remove(target_id)
            try:
                await query.message.chat.restrict_member(target_id, ChatPermissions(
                    can_send_messages=True, can_send_media_messages=True, 
                    can_send_other_messages=True, can_add_web_page_previews=True
                ))
                await query.answer("Verifiziert!")
                await query.message.edit_text(f"✅ {query.from_user.first_name} ist verifiziert und darf schreiben!")
                asyncio.create_task(delete_later(query.message, 30))
            except Exception as e: 
                logger.error(f"Captcha Error: {e}")
        else:
            await query.answer("Das ist nicht dein Button!", show_alert=True)

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

    timer = config.get('delete_timer', 300)
    asyncio.create_task(delete_later(update.message, timer))

    raw_command = text.split()[0] 
    command_clean = raw_command[1:]
    if '@' in command_clean:
        command_clean = command_clean.split('@')[0]
    
    command_trigger = command_clean.lower()
    admin_id_str = str(config.get("admin_id", ""))
    
    if command_trigger == "id":
        if update.message.reply_to_message:
            target = update.message.reply_to_message.from_user
            msg = await update.message.reply_text(f"👤 User: {target.first_name}\n🆔 ID: `{target.id}`", parse_mode='Markdown')
        else:
            msg = await update.message.reply_text(f"Deine ID: `{user.id}`\nGruppe ID: `{chat.id}`", parse_mode='Markdown')
        log_command_id(chat.id, msg.message_id)
        asyncio.create_task(delete_later(msg, 30))
        return

    if command_trigger == "ban":
        if str(user.id) != admin_id_str: return
        if update.message.reply_to_message:
            target_msg = update.message.reply_to_message
            target_user = target_msg.from_user
            try:
                try: await target_msg.delete()
                except: pass
                await chat.ban_member(target_user.id, revoke_messages=True)
                succ_msg = await update.message.reply_text(f"🔨 {target_user.first_name} gebannt & bereinigt!")
                log_ban(target_user.id, target_user.first_name, chat.id, chat.title, "Admin Befehl /ban")
                asyncio.create_task(delete_later(succ_msg, 10))
            except Exception as e:
                err_msg = await update.message.reply_text(f"Fehler: {e}")
                asyncio.create_task(delete_later(err_msg, 10))
        return

    if command_trigger in ["top", "ranking"]:
        stats = load_json(STATS_FILE)
        users_stats = stats.get("users", {})
        if not users_stats: return
        sorted_users = sorted(users_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        known_users = load_json(USER_DB_FILE)
        medals = ["🥇", "🥈", "🥉", "🏅", "🏅"]
        text_lines = ["🏆 **KODIMANS TOP CHATTER** 🏆\n"]
        for i, (uid, count) in enumerate(sorted_users):
            short_name = known_users.get(uid, f"User {uid}").split(" (@")[0]
            text_lines.append(f"{medals[i]} **{short_name}** ({count} Nachrichten)")
        top_msg = await update.message.reply_text("\n".join(text_lines), parse_mode='Markdown')
        log_command_id(chat.id, top_msg.message_id)
        asyncio.create_task(delete_later(top_msg, timer))
        return

    if command_trigger in ["karma", "ehrenmann"]:
        karma_stats = load_json(KARMA_FILE)
        if not karma_stats:
            msg = await update.message.reply_text("Es wurde noch kein Karma vergeben.")
            asyncio.create_task(delete_later(msg, timer))
            return
        sorted_karma = sorted(karma_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        known_users = load_json(USER_DB_FILE)
        text_lines = ["🌟 **KODIMANS KARMA RANKING** 🌟\n"]
        for i, (uid, count) in enumerate(sorted_karma):
            short_name = known_users.get(uid, f"User {uid}").split(" (@")[0]
            text_lines.append(f"{i+1}. **{short_name}** ({count} Karma-Punkte)")
        k_msg = await update.message.reply_text("\n".join(text_lines), parse_mode='Markdown')
        log_command_id(chat.id, k_msg.message_id)
        asyncio.create_task(delete_later(k_msg, timer))
        return

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
        
        # CAPTCHA LOGIC
        if config.get("captcha_active", False):
            try:
                await update.effective_chat.restrict_member(member.id, ChatPermissions(can_send_messages=False))
                pending_captchas.add(member.id)
                keyboard = [[InlineKeyboardButton("🤖 Ich bin ein Mensch", callback_data=f"captcha_{member.id}")]]
                msg = await update.message.reply_text(f"👋 Hallo {member.first_name}!\nBitte klicke unten, um zu beweisen, dass du ein Mensch bist. Du hast 2 Minuten.", reply_markup=InlineKeyboardMarkup(keyboard))
                
                async def kick_unverified(chat_id, user_id, msg_to_del):
                    await asyncio.sleep(120)
                    if user_id in pending_captchas:
                        try:
                            await context.bot.ban_chat_member(chat_id, user_id)
                            await context.bot.unban_chat_member(chat_id, user_id)
                            await msg_to_del.delete()
                        except: pass
                asyncio.create_task(kick_unverified(update.effective_chat.id, member.id, msg))
            except Exception as e:
                logger.error(f"Failed to apply captcha restriction: {e}")
        else:
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
    config = load_json(CONFIG_FILE)
    
    # NACHTRUHE CHECK (Mit Absturz-Schutz)
    if config.get("nightmode_active", False):
        now = datetime.now().time()
        try:
            start_t = datetime.strptime(config.get("nightmode_start", "23:00"), "%H:%M").time()
            end_t = datetime.strptime(config.get("nightmode_end", "07:00"), "%H:%M").time()
            is_night = False
            if start_t <= end_t:
                is_night = start_t <= now <= end_t
            else:
                is_night = start_t <= now or now <= end_t
            
            if is_night:
                if not await is_user_admin(chat, user.id) and str(user.id) != str(config.get("admin_id", "")):
                    try:
                        await update.message.delete()
                    except: pass
                    return # Sofort abbrechen
        except Exception as e: logger.error(f"Nightmode Error: {e}")

    # LEVEL UP SYSTEM
    msg_count = update_stats(user.id)
    RANKS = {10: "Neuling 🌱", 50: "Plaudertasche 💬", 100: "Stammgast 🌟", 250: "Schreibmaschine ⌨️", 500: "Chat-Legende 👑", 1000: "Gottgleicher Tipper ⚡"}
    if msg_count in RANKS:
        try:
            lvl_msg = await chat.send_message(f"🎉 **LEVEL UP!** 🎉\nGlückwunsch {user.first_name}! Du hast gerade deine **{msg_count}. Nachricht** geschrieben.\nDein neuer Rang ist: **{RANKS[msg_count]}**", parse_mode='Markdown')
            asyncio.create_task(delete_later(lvl_msg, 60))
        except: pass

    text = update.message.text.lower()
    
    # KARMA SYSTEM (Gefixt auf bessere String-Erkennung)
    karma_triggers = ["+1", "danke", "thx", "thanks", "👍", "ehrenmann"]
    if update.message.reply_to_message and any(w in text for w in karma_triggers):
        target = update.message.reply_to_message.from_user
        if target.id != user.id and target.id != context.bot.id:
            k_count = add_karma(target.id)
            try:
                k_msg = await chat.send_message(f"🌟 {target.first_name} hat einen Karma-Punkt erhalten! (Gesamt: {k_count})")
                asyncio.create_task(delete_later(k_msg, 30))
            except: pass

    if config.get("active_chat_id") != chat.id:
        config["active_chat_id"] = chat.id
        config["active_chat_title"] = chat.title
        save_json(CONFIG_FILE, config)

    # LINK SCHUTZ
    if config.get("link_protection", False):
        if "http://" in text or "https://" in text or "www." in text or ".com" in text or ".de" in text or "t.me" in text:
            is_admin = await is_user_admin(chat, user.id)
            if not is_admin and str(user.id) != str(config.get("admin_id", "")):
                try:
                    await update.message.delete()
                    warn = await chat.send_message(f"⚠️ {user.first_name}, Links sind hier nur für Admins!")
                    asyncio.create_task(delete_later(warn, 30))
                    return 
                except Exception as e: logger.error(f"Link Delete Error: {e}")

    # WORT FILTER & TIMEOUTS / STRIKES
    banned_words = config.get('banned_words', [])
    max_strikes = config.get('max_strikes', 3) 
    
    for word in banned_words:
        if word in text:
            try:
                await update.message.delete()
                strikes = add_warning(user.id)
                
                # TIMEOUT LOGIC (Gefixt auf TimeDelta wegen Zeitzonen)
                if strikes == max_strikes - 1 and max_strikes > 1:
                    await chat.restrict_member(user.id, ChatPermissions(can_send_messages=False), until_date=timedelta(hours=24))
                    warn_msg = await chat.send_message(f"⚠️ {user.first_name}, das Wort '{word}' ist verboten! (Strike {strikes}/{max_strikes})\nDu wurdest zur Abkühlung für **24 Stunden stummgeschaltet**.", parse_mode='Markdown')
                    asyncio.create_task(delete_later(warn_msg, 60))
                
                # BAN LOGIC
                elif strikes >= max_strikes:
                    await chat.ban_member(user.id, revoke_messages=True)
                    log_ban(user.id, user.first_name, chat.id, chat.title, f"{word} (Strike {strikes}/{max_strikes})")
                    reset_warnings(user.id)
                    ban_msg = await chat.send_message(f"⛔ {user.first_name} wurde permanent gebannt! (Limit erreicht)")
                    asyncio.create_task(delete_later(ban_msg, 60))
                
                # NORMAL WARN LOGIC
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
    app = Application.builder().token(token).post_init(post_init).build()
    
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, monitor_chat))
    app.add_handler(MessageHandler(filters.COMMAND, handle_dynamic_commands))
    
    app.run_polling()

if __name__ == '__main__':
    main()
