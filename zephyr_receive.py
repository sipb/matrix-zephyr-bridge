import zephyr
import sys
from constants import *
from zephyr_client import Zephyr
from util import strip_default_realm, create_zephyr_room_if_needed, get_zephyr_localpart
from config import config
import matrix

z = Zephyr()

def on_zephyr_message(message: zephyr.ZNotice):
    """
    Handles Zephyr message received (to bridge to Matrix)
    """
    sender = strip_default_realm(message.sender)

    # Pings are not messages
    if message.opcode == 'PING':
        # TODO: bridge if actually relevant
        # (only seems to work for DMs, which would make it mostly pointless)
        print(f"{sender} is typing...")
        return
    
    # Make sure message has 2 (usually) or 1 (rare) fields
    if len(message.fields) == 1:
        # In my testing, some messages without signature were sent as one field
        display_name = sender
        content = message.fields[0]
    elif len(message.fields) != 2:
        print(f"Message does not have 1 or 2 fields, skipping!", file=sys.stderr)
        print(message.__dict__, file=sys.stderr)
        return

    display_name, content = message.fields
    
    # Treat empty signature as just kerb
    if display_name == '':
        display_name = sender

    # This is a DM! 
    if message.cls == DEFAULT_CLASS and message.instance == DEFAULT_INSTANCE:
        # TODO: handle.
        # 
        # For now, it can only be the bot's DMs, but once it uses webathena tickets,
        # this could mean anyone's DMs, to be bridged!
        #
        # Also how to subscribe to a custom instance with default class? Zulip does it...
        recipient = strip_default_realm(message.recipient)
        print(f"Skipped DM from {sender} ({display_name}) to {recipient}:\n{content}")
        return

    # TODO: handle lack of success ↓

    # Create room (if needed)
    create_zephyr_room_if_needed(message.cls, message.instance)
    
    # Create user (if needed)
    matrix.create_user(f'{config.zephyr_user_prefix}{sender}')

    room_alias = f'#{get_zephyr_localpart(message.cls, message.instance)}:{config.homeserver}'
    matrix_user_id = f'@{config.zephyr_user_prefix}{sender}:{config.homeserver}'

    # Join user to room (if needed)
    # TODO: check if in room, then join only if not
    matrix.join_room(room_alias, matrix_user_id)

    # Adjust display name (if needed)
    current_matrix_name = matrix.get_global_display_name(matrix_user_id)
    if display_name and current_matrix_name != display_name:
        matrix.set_global_display_name(matrix_user_id, display_name)

    # Send message!
    matrix.send_text_message(
        room_id=room_alias,
        message=content,
        user_id=f'@{config.zephyr_user_prefix}{sender}:{config.homeserver}'
    )
    
    print(f"Sent [-c {msg.cls} -i {msg.instance}] {content}")


if __name__ == '__main__':
    while True:
        msg: zephyr.ZNotice = zephyr.receive(True)
        if msg is not None:
            on_zephyr_message(msg)