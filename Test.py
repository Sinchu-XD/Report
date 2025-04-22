from telethon import TelegramClient, events
from Report import API_ID as api_id, API_HASH as api_hash, BOT_TOKEN

bot = TelegramClient('bot_ss', api_id, api_hash).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.respond("Hello! Bot is working.")

async def main():
    await bot.run_until_disconnected()
    await asyncio.get_event_loop().create_future()

if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        print("🛑 Bot stopped manually.")
