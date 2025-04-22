from telethon.sync import TelegramClient
from telethon.tl.functions.account import ReportPeer
from telethon.tl.types import InputReportReasonSpam

api_id = 123456  # Replace with your API ID
api_hash = 'your_api_hash'  # Replace with your API Hash
session_name = 'session'

with TelegramClient(session_name, api_id, api_hash) as client:
    user = client.get_input_entity("username")  # Replace with target username
    result = client(ReportPeer(
        peer=user,
        reason=InputReportReasonSpam(),
        message="User is sending spam content."
    ))
    print(result)
