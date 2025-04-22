import os
import asyncio
from telethon.sync import TelegramClient
from telethon.tl.functions.account import ReportPeerRequest
from telethon.tl.types import (
    InputReportReasonSpam,
    InputReportReasonPornography,
    InputReportReasonChildAbuse,
    InputReportReasonViolence,
    InputReportReasonFake,
    InputReportReasonCopyright,
    InputReportReasonDrugs,
    InputReportReasonOther
)

API_ID = 123456
API_HASH = "your_api_hash"
SESSION_FOLDER = "sessions"
TARGET = "https://t.me/yourchannel_or_group_or_user"
LOOP = True
DELAY = 3

REASONS_MESSAGES = {
    InputReportReasonSpam(): "Spamming constantly",
    InputReportReasonPornography(): "Posting adult content",
    InputReportReasonChildAbuse(): "Child abuse or exploitation",
    InputReportReasonViolence(): "Threatening or violent content",
    InputReportReasonFake(): "Pretending to be someone else",
    InputReportReasonCopyright(): "Posting copyrighted material",
    InputReportReasonDrugs(): "Promoting drugs",
    InputReportReasonOther(): "Miscellaneous rule violation"
}

async def report(client, entity):
    try:
        me = await client.get_me()
        reason, message = list(REASONS_MESSAGES.items())[hash(me.id) % len(REASONS_MESSAGES)]
        print(f"Reporting from @{me.username or me.id} for {reason.__class__.__name__}")
        await client(ReportPeerRequest(
            peer=entity,
            reason=reason,
            message=message
        ))
        print(f"✅ Reported successfully.")
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    while True:
        for session_file in os.listdir(SESSION_FOLDER):
            if session_file.endswith(".session"):
                session_name = os.path.join(SESSION_FOLDER, session_file).replace(".session", "")
                try:
                    client = TelegramClient(session_name, API_ID, API_HASH)
                    await client.start()
                    entity = await client.get_entity(TARGET)
                    await report(client, entity)
                    await client.disconnect()
                except Exception as e:
                    print(f"❌ [{session_file}] Failed: {e}")
                await asyncio.sleep(DELAY)
        if not LOOP:
            break

if __name__ == "__main__":
    asyncio.run(main())
  
