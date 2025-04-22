from telethon.sync import TelegramClient
from telethon import types
from telethon.tl.functions.messages import Report

api_id = 123456  # replace with your API ID
api_hash = 'your_api_hash'  # replace with your API hash
name = 'session_name'

with TelegramClient(name, api_id, api_hash) as client:
    user = client.get_input_entity("username")  # Replace 'username' with the target username
    result = client(functions.messages.Report(
        peer=user,
        reason=types.InputReportReasonSpam(),
        message='This user is spamming.'
    ))
    print(result)
  
