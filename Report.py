from telethon import TelegramClient, events
from telethon.tl.functions.messages import Report
from telethon.tl.types import PeerChannel, PeerUser, InputReportReasonSpam, InputReportReasonPornography, InputReportReasonChildAbuse, InputReportReasonViolence, InputReportReasonFake, InputReportReasonCopyright, InputReportReasonDrugs, InputReportReasonOther
from telethon.errors import FloodWaitError
import logging
import time

logging.basicConfig(level=logging.INFO)

API_ID = 'your_api_id'
API_HASH = 'your_api_hash'
BOT_TOKEN = "YOUR_BOT_TOKEN"

OWNER_ID = 123456789
SUDO_USERS = [OWNER_ID]

LOGIN_STORAGE_FILE = 'login_storage.json'


client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

if os.path.exists(LOGIN_STORAGE_FILE):
    with open(LOGIN_STORAGE_FILE, 'r') as f:
        AUTHORIZED_USERS = json.load(f)
else:
    AUTHORIZED_USERS = {}

user_clients = {}


async def restore_sessions():
    for user_id, data in AUTHORIZED_USERS.items():
        session_str = data.get("session")
        if session_str:
            try:
                temp_client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
                await temp_client.connect()
                if await temp_client.is_user_authorized():
                    user_clients[int(user_id)] = temp_client
                    print(f"[+] Restored session for user {user_id}")
            except Exception as e:
                print(f"[!] Restore failed for {user_id}: {e}")


report_logs = {
    'channel_reports': 0,
    'user_reports': 0
}

REASONS_MESSAGES = {
    "spamming": InputReportReasonSpam(),
    "pornography": InputReportReasonPornography(),
    "child_abuse": InputReportReasonChildAbuse(),
    "violence": InputReportReasonViolence(),
    "fake": InputReportReasonFake(),
    "copyright": InputReportReasonCopyright(),
    "drugs": InputReportReasonDrugs(),
    "other": InputReportReasonOther(),
}

HELP_MESSAGE = """
Available Report Reasons:
1. /spamming - Spamming constantly
2. /pornography - Posting adult content
3. /child_abuse - Child abuse or exploitation
4. /violence - Threatening or violent content
5. /fake - Pretending to be someone else
6. /copyright - Posting copyrighted material
7. /drugs - Promoting drugs
8. /other - Miscellaneous rule violation

Usage Example:
To report a user/channel: /report_all @username spamming
"""

def is_sudo_user(user_id):
    return user_id == OWNER_ID or user_id in SUDO_USERS

async def add_sudo_user(user_id):
    if is_sudo_user(user_id):
        SUDO_USERS.append(user_id)
        await client.send_message(user_id, "You have been added as a Sudo user.")
    else:
        await client.send_message(user_id, "You do not have permission to add Sudo users.")

async def remove_sudo_user(user_id):
    if is_sudo_user(user_id) and user_id != OWNER_ID:
        SUDO_USERS.remove(user_id)
        await client.send_message(user_id, "You have been removed from Sudo users.")
    else:
        await client.send_message(user_id, "You do not have permission to remove Sudo users.")

async def authenticate_user(event):
    user_id = event.sender_id
    if user_id in AUTHORIZED_USERS:
        return True
    else:
        await event.respond("You are not logged in. Please use the /login command to authenticate.")
        return False

@client.on(events.NewMessage(pattern='/login'))
async def login(event):
    sender = await event.get_sender()
    user_id = sender.id

    if str(user_id) in AUTHORIZED_USERS:
        await event.respond("✅ You are already logged in.")
        return

    await event.respond("📱 Send your phone number (with country code):")
    try:
        response = await client.wait_for(events.NewMessage(from_users=user_id), timeout=60)
        phone_number = response.text.strip()

        temp_client = TelegramClient(StringSession(), API_ID, API_HASH)
        await temp_client.connect()
        await temp_client.send_code_request(phone_number)

        await event.respond("📩 Send the OTP you received:")
        otp_msg = await client.wait_for(events.NewMessage(from_users=user_id), timeout=60)
        otp = otp_msg.text.strip()

        try:
            await temp_client.sign_in(phone_number, otp)
        except SessionPasswordNeededError:
            await event.respond("🔐 2FA enabled. Send your Telegram password:")
            pwd_msg = await client.wait_for(events.NewMessage(from_users=user_id), timeout=60)
            password = pwd_msg.text.strip()
            await temp_client.sign_in(password=password)

        session_str = temp_client.session.save()
        AUTHORIZED_USERS[str(user_id)] = {
            "phone": phone_number,
            "session": session_str
        }
        with open(LOGIN_STORAGE_FILE, "w") as f:
            json.dump(AUTHORIZED_USERS, f)

        user_clients[user_id] = temp_client
        await event.respond("✅ Logged in successfully.")

    except Exception as e:
        await event.respond(f"❌ Login failed: {e}")
        try:
            await temp_client.disconnect()
        except:
            pass


@client.on(events.NewMessage(pattern='/logout'))
async def logout(event):
    sender = await event.get_sender()
    user_id = sender.id

    if str(user_id) in AUTHORIZED_USERS:
        user_client = user_clients.get(user_id)
        if user_client:
            await user_client.disconnect()
            user_clients.pop(user_id, None)

        AUTHORIZED_USERS.pop(str(user_id))
        with open(LOGIN_STORAGE_FILE, "w") as f:
            json.dump(AUTHORIZED_USERS, f)

        await event.respond("✅ Logged out successfully.")
    else:
        await event.respond("❌ You are not logged in.")



async def mass_report(target, reason_key="other"):
    try:
        reason = REASONS_MESSAGES.get(reason_key, InputReportReasonOther())
        
        if isinstance(target, PeerChannel):
            result = await client(Report(target, reason))
            report_logs['channel_reports'] += 1
            logging.info(f"Reported Channel: {target.id} | Success: {result}")
        elif isinstance(target, PeerUser):
            result = await client(Report(target, reason))
            report_logs['user_reports'] += 1
            logging.info(f"Reported User: {target.id} | Success: {result}")
    except FloodWaitError as e:
        logging.error(f"FloodWaitError: You have been rate-limited. Waiting for {e.seconds} seconds.")
        await client.send_message(target, f"Flood wait triggered. Retrying after {e.seconds} seconds.")
        time.sleep(e.seconds)
        await mass_report(target, reason_key)
    except Exception as e:
        logging.error(f"Error reporting {target}: {str(e)}")

async def mass_report_all_reasons(target):
    try:
        for reason_key in REASONS_MESSAGES.keys():
            await mass_report(target, reason_key)
            logging.info(f"Mass Reported {target.id} with reason '{reason_key}'")
        await client.send_message(target, "Mass reporting completed with all available reasons.")
    except FloodWaitError as e:
        logging.error(f"FloodWaitError: You have been rate-limited. Waiting for {e.seconds} seconds.")
        await client.send_message(target, f"Flood wait triggered. Retrying after {e.seconds} seconds.")
        time.sleep(e.seconds)
        await mass_report_all_reasons(target)
    except Exception as e:
        logging.error(f"Error mass reporting {target}: {str(e)}")

async def get_report_logs(user_id):
    if is_sudo_user(user_id):
        logs = f"Channel Reports: {report_logs['channel_reports']}\nUser Reports: {report_logs['user_reports']}"
        await client.send_message(user_id, logs)
    else:
        await client.send_message(user_id, "You do not have permission to view the logs.")

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    if not is_sudo_user(user_id):
        await event.respond("You do not have permission to use this bot.")
        return
    await event.respond("Bot is active! Use /help for available commands.")

@client.on(events.NewMessage(pattern='/add_sudo'))
async def add_sudo(event):
    user_id = event.sender_id
    if is_sudo_user(user_id):
        try:
            target_id = int(event.message.text.split(' ')[1])
            await add_sudo_user(target_id)
        except:
            await event.respond("Please provide a valid user ID.")
    else:
        await event.respond("You are not authorized to add sudo users.")

@client.on(events.NewMessage(pattern='/remove_sudo'))
async def remove_sudo(event):
    user_id = event.sender_id
    if is_sudo_user(user_id):
        try:
            target_id = int(event.message.text.split(' ')[1])
            await remove_sudo_user(target_id)
        except:
            await event.respond("Please provide a valid user ID.")
    else:
        await event.respond("You are not authorized to remove sudo users.")

@client.on(events.NewMessage(pattern='/report_all'))
async def report_all(event):
    user_id = event.sender_id
    if is_sudo_user(user_id):
        try:
            target = event.message.text.split(' ')[1]
            reason_key = event.message.text.split(' ')[2] if len(event.message.text.split(' ')) > 2 else "other"
            target = await client.get_entity(target)
            await mass_report(target, reason_key)
            await event.respond(f"Mass report for {target.id} with reason '{reason_key}' has been initiated.")
        except:
            await event.respond("Please provide a valid target.")
    else:
        await event.respond("You are not authorized to use this command.")

@client.on(events.NewMessage(pattern='/mass_report_all'))
async def mass_report_all(event):
    user_id = event.sender_id
    if is_sudo_user(user_id):
        try:
            target = event.message.text.split(' ')[1]
            target = await client.get_entity(target)
            await mass_report_all_reasons(target)
            await event.respond(f"Mass report for {target.id} with all available reasons has been initiated.")
        except:
            await event.respond("Please provide a valid target.")
    else:
        await event.respond("You are not authorized to use this command.")

@client.on(events.NewMessage(pattern='/get_logs'))
async def get_logs(event):
    user_id = event.sender_id
    if is_sudo_user(user_id):
        await get_report_logs(user_id)
    else:
        await event.respond("You are not authorized to view logs.")

@client.on(events.NewMessage(pattern='/help'))
async def help(event):
    user_id = event.sender_id
    if is_sudo_user(user_id):
        await event.respond(HELP_MESSAGE)
    else:
        await event.respond("You do not have permission to view help.")

client.start()
client.run_until_disconnected()
