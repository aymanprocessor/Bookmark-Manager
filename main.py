import os
import sqlite3
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Initialize database
DB_NAME = "bookmarks.db"
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS bookmarks (id INTEGER PRIMARY KEY, name TEXT, url TEXT)''')
conn.commit()
conn.close()

# Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome to Bookmark Manager! Use /add, /edit, /delete, and /list commands to manage your bookmarks.")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /add <name> <url>")
        return

    name = args[0]
    url = args[1]

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO bookmarks (name, url) VALUES (?, ?)", (name, url))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Bookmark '{name}' added successfully!")

async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Usage: /edit <name> <new_name> <new_url>")
        return

    name = args[0]
    new_name = args[1]
    new_url = args[2]

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE bookmarks SET name = ?, url = ? WHERE name = ?", (new_name, new_url, name))
    if c.rowcount == 0:
        await update.message.reply_text(f"Bookmark '{name}' not found.")
    else:
        await update.message.reply_text(f"Bookmark '{name}' updated to '{new_name}: {new_url}' successfully!")
    conn.commit()
    conn.close()

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name FROM bookmarks")
    bookmarks = c.fetchall()

    if not bookmarks:
        await update.message.reply_text("No bookmarks to delete.")
        conn.close()
        return

    keyboard = [[InlineKeyboardButton(f"{bookmark[1]}", callback_data=str(bookmark[0]))] for bookmark in bookmarks]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Select a bookmark to delete:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    bookmark_id = query.data

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
    conn.commit()
    conn.close()

    await query.edit_message_text("Bookmark deleted successfully!")

async def list_bookmarks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, url FROM bookmarks")
    bookmarks = c.fetchall()
    conn.close()

    if not bookmarks:
        await update.message.reply_text("No bookmarks found.")
        return

    message = "\n".join([f"{bookmark[0]}: {bookmark[1]}" for bookmark in bookmarks])
    await update.message.reply_text(message)

# Main function
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("edit", edit))
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(CommandHandler("list", list_bookmarks))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == "__main__":
    main()
