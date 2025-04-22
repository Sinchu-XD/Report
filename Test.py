from telethon import TelegramClient, events
from Report import API_ID as api_id, API_HASH as api_hash, BOT_TOKEN

bot = TelegramClient('bot', api_id, api_hash).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.respond("Hello! Bot is working.")

print("Bot is running...")
bot.run_until_disconnected()
