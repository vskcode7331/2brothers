import logging
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Trimite un mesaj de bun venit și adaugă utilizatorul în baza de date."""
    user_id = update.effective_chat.id
    username = update.effective_user.username or "UtilizatorNecunoscut"
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    await update.message.reply_text(
        f"🚀 Bun venit, {username}!\n\n"
        "Pentru a primi acces la **serverul nostru exclusiv de Discord**, invită **3 prieteni** și răspunde la câteva întrebări despre trading.\n"
        "După ce aceștia se alătură, vei primi automat link-ul de acces!\n\n"
        "Scrie /invites pentru a verifica progresul tău."
    )

async def track_invites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Urmărește cine a invitat pe cine și actualizează numărul de invitații."""
    if update.message.new_chat_members:
        inviter_id = update.message.from_user.id
        for member in update.message.new_chat_members:
            new_user_id = member.id
            username = member.username or "UtilizatorNecunoscut"
            
            # Introduce utilizatorul nou și setează invitatul
            cursor.execute("INSERT OR IGNORE INTO users (user_id, username, inviter_id) VALUES (?, ?, ?)", (new_user_id, username, inviter_id))
            
            # Actualizează numărul de invitații
            cursor.execute("UPDATE users SET invites = invites + 1 WHERE user_id = ?", (inviter_id,))
            conn.commit()

async def invites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Afișează câți utilizatori au fost invitați de un user."""
    user_id = update.effective_chat.id
    cursor.execute("SELECT invites FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    invites_count = result[0] if result else 0
    await update.message.reply_text(f"📢 Ai invitat {invites_count} persoane.")

def main() -> None:
    """Pornește bot-ul."""
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("invites", invites))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_invites))
    
    application.run_polling()

if __name__ == "__main__":
