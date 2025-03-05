import logging
import sqlite3
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Activare logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Tokenul Bot-ului Telegram (Înlocuiește cu tokenul tău real)
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Link-ul de Discord
DISCORD_LINK = "https://discord.gg/YOUR_DISCORD_LINK"

# Configurare baza de date SQLite
conn = sqlite3.connect("invites.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        inviter_id INTEGER,
        invites INTEGER DEFAULT 0,
        answered_quiz BOOLEAN DEFAULT 0,
        sent_message BOOLEAN DEFAULT 0
    )
    """
)
conn.commit()

def start(update: Update, context: CallbackContext) -> None:
    """Trimite un mesaj de bun venit și adaugă utilizatorul în baza de date."""
    user_id = update.message.chat_id
    username = update.message.from_user.username or "UtilizatorNecunoscut"
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    update.message.reply_text(
        f"🚀 Bun venit, {username}!\n\n"
        "Pentru a primi acces la **serverul nostru exclusiv de Discord**, invită **3 prieteni** și răspunde la câteva întrebări despre trading.\n"
        "După ce aceștia se alătură, vei primi automat link-ul de acces!\n\n"
        "Scrie /invites pentru a verifica progresul tău."
    )

def track_invites(update: Update, context: CallbackContext) -> None:
    """Urmărește cine a invitat pe cine și actualizează numărul de invitații."""
    for member in update.message.new_chat_members:
        inviter_id = update.message.from_user.id  # Persoana care a invitat utilizatorul nou
        new_user_id = member.id
        username = member.username or "UtilizatorNecunoscut"
        
        # Introduce utilizatorul nou și setează invitatul
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, inviter_id) VALUES (?, ?, ?)", (new_user_id, username, inviter_id))
        
        # Actualizează numărul de invitații
        cursor.execute("UPDATE users SET invites = invites + 1 WHERE user_id = ?", (inviter_id,))
        conn.commit()

def ask_quiz(update: Update, context: CallbackContext) -> None:
    """Trimite întrebările de verificare pentru utilizatorii eligibili."""
    user_id = update.message.chat_id
    cursor.execute("SELECT invites, answered_quiz FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result and result[0] >= 3 and result[1] == 0:
        update.message.reply_text(
            "📊 Înainte de a primi link-ul de Discord, răspunde la aceste întrebări simple despre trading:\n\n"
            "1️⃣ Ce este un stop-loss?\nA) Un semnal de tranzacționare\nB) Un instrument de gestionare a riscurilor\nC) O metodă de creștere a levierului\n\n"
            "2️⃣ La ce oră începe sesiunea de tranzacționare din Londra?\nA) 00:00 GMT\nB) 08:00 GMT\nC) 15:00 GMT\n\n"
            "3️⃣ Ce înseamnă 'bullish' în trading?\nA) Piața crește\nB) Piața scade\nC) Piața este neutră\n\n"
            "📩 Răspunde la aceste întrebări scriind opțiunea corectă (ex: '1B, 2B, 3A')"
        )

def verify_quiz(update: Update, context: CallbackContext) -> None:
    """Marchează utilizatorul ca verificat după ce răspunde la quiz."""
    user_id = update.message.chat_id
    cursor.execute("UPDATE users SET answered_quiz = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    update.message.reply_text("🎉 Mulțumim pentru răspunsuri! Scrie un mesaj în grup pentru a primi link-ul de Discord!")

def track_messages(update: Update, context: CallbackContext) -> None:
    """Verifică dacă utilizatorul a trimis un mesaj înainte de a primi link-ul de Discord."""
    user_id = update.message.chat_id
    cursor.execute("SELECT invites, answered_quiz, sent_message FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result and result[0] >= 3 and result[1] == 1 and result[2] == 0:
        cursor.execute("UPDATE users SET sent_message = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        update.message.reply_text(f"🎉 Felicitări! Ai primit acces la Discord: {DISCORD_LINK}")

def main():
    """Pornește bot-ul."""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("top", leaderboard))
    dp.add_handler(CommandHandler("invites", check_invites))
    dp.add_handler(CommandHandler("quiz", ask_quiz))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, verify_quiz))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, track_invites))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, track_messages))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

