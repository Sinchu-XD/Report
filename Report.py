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

AUTHORIZED_USERS = {}
LOGIN_STORAGE_FILE = 'login_storage.json'


client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

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

async def login(event, phone_number):
    user_id = event.sender_id
    
    if user_id in AUTHORIZED_USERS:
        await event.respond("You are already logged in.")
        return
    
    await event.respond("Please wait while we authenticate your phone number...")
    
    try:
        # Log in with the provided phone number
        await client.send_code_request(phone_number)  # Send code to user's phone number
        await event.respond("Please enter the code you received:")

        @client.on(events.NewMessage(pattern='^\d{5,6}$'))  # Accept code from user
        async def handle_code(event):
            code = event.text.strip()
            try:
                await client.sign_in(phone_number, code)  # Complete the login
                # If 2FA is enabled, it will trigger SessionPasswordNeededError
                try:
                    await client.start()  # Start the client
                except SessionPasswordNeededError:
                    await event.respond("Please enter your 2FA password:")
                    # Ask the user to provide their 2FA password
                    @client.on(events.NewMessage(pattern='^\S+$'))  # Accept 2FA password
                    async def handle_2fa_password(event):
                        password = event.text.strip()
                        try:
                            await client.sign_in(password=password)  # Provide 2FA password
                            AUTHORIZED_USERS[user_id] = {
                                'phone_number': phone_number,
                                '2fa_password': password
                            }
                            # Save login data to the file
                            with open(LOGIN_STORAGE_FILE, 'w') as f:
                                json.dump(AUTHORIZED_USERS, f)
                            await event.respond(f"User {user_id} has been successfully logged in.")
                        except Exception as e:
                            await event.respond(f"Login failed. Error: {str(e)}")
            except Exception as e:
                await event.respond(f"Login failed. Please try again. Error: {str(e)}")
    
    except Exception as e:
        await event.respond(f"Failed to send verification code. Error: {str(e)}")


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
