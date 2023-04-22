import zephyr
import sys
from constants import *
from zephyr_client import Zephyr
from util import strip_default_realm, create_zephyr_room, get_zephyr_localpart, timestamp_zephyr_to_matrix
from kerberos import renew_kerberos_tickets
from config import config
import matrix

z: Zephyr = Zephyr()

def handle_bot_command(message: str, sender: str) -> str:
    """
    Synchronously get the output of a command
    """
    command = message.split(' ')[0]
    if command == 'ping':
        return 'pong'
    elif command == 'echo':
        body = message.split(' ', 1)[1:][0]
        return body
    elif command == 'add':
        try:
            cls, instance, recipient = message.split(' ')[1:]
            line = ','.join([cls, instance, recipient])
            if '\\' in line or '"' in line:
                return 'Error: Backslashes/quotes are not currently supported'
            z.subscribe(cls, instance)
            return f"Successfully subscribed to -c {cls} -i {instance}"
        except ValueError as e:
            return f'Error: `add` expects exactly 3 parameters separated by spaces: {e}'
    elif command == 'send':
        try:
            recipient, message = message.split(' ', 2)[1:]
            # TODO: direct messages are just rooms.
            # using a library would take care of doing this for us
            return 'This feature is not implemented (ask rgabriel to implement it)'
        except ValueError:
            return f'What do you wish to send to {sender}?'
    elif command == 'help':
        return 'Available commands are ping, echo, add, and send (unimplemented)'
    else:
        return f'Error: Unknown command {command}'


def on_zephyr_message(message: zephyr.ZNotice):
    """
    Handles Zephyr message received (to bridge to Matrix)
    """
    print(message.__dict__)
    
    sender = strip_default_realm(message.sender)
    recipient = strip_default_realm(message.recipient)

    # Pings are not messages
    if message.opcode == 'PING':
        # TODO: bridge if actually relevant
        # (only seems to work for DMs, which would make it mostly pointless)
        print(f"{sender} is typing...")
        return
    
    # Make sure message has 2 (usually) or 1 (rare) fields
    if len(message.fields) == 1:
        # In my testing, some messages without signature were sent as one field
        signature = sender
        content = message.fields[0]
    elif len(message.fields) != 2:
        print(f"Message does not have 1 or 2 fields, skipping!", file=sys.stderr)
        print(message.__dict__, file=sys.stderr)
        return

    signature, content = message.fields
    
    # Respect blocked opcodes
    if message.opcode in config.blocked_opcodes:
        print(f"Not bridging blocked opcode: {message.opcode}")
        return
    
    # Ignore messages from Mattermost user
    if sender in config.blocked_zephyr_usernames:
        print(f"Not bridging blocked sender: {message.sender}")
        return

    # Treat empty signature as just kerb
    if signature == '':
        signature = sender

    # This is a DM! 
    if message.cls == DEFAULT_CLASS and message.instance == DEFAULT_INSTANCE:
        # If it's addressed to us, handle it as a command
        if recipient == OWN_KERB:
            print(f"Handling command from {sender}")
            z.send_message(handle_bot_command(content, sender), recipient=sender)
        else:
            print(f"Skipped DM from {sender} ({signature}) to {recipient}:\n{content}", file=sys.stderr)
        return

    # TODO: handle lack of success ↓

    room_alias = f'#{get_zephyr_localpart(message.cls, message.instance)}:{config.homeserver}'

    # Create room (if needed)
    if not matrix.get_room_id(room_alias):
        create_zephyr_room(message.cls, message.instance)
    
    # Create user (if needed)
    matrix.create_user(f'{config.zephyr_user_prefix}{sender}')
    matrix_user_id = f'@{config.zephyr_user_prefix}{sender}:{config.homeserver}'

    # Get display name (currently just the kerb, subject to change)
    display_name = sender

    # Adjust display name (if needed)
    current_matrix_name = matrix.get_global_display_name(matrix_user_id)
    if display_name and current_matrix_name != display_name:
        matrix.set_global_display_name(matrix_user_id, display_name)

    # Join user to room (if needed)
    # TODO: check if in room, then join only if not
    matrix.join_room(room_alias, matrix_user_id)

    # Send message!
    matrix.send_text_message(
        room_id=room_alias,
        message=content,
        user_id=f'@{config.zephyr_user_prefix}{sender}:{config.homeserver}',
        additional_metadata={
            'im.zephyr.authentic': message.auth,
            'im.zephyr.signature': signature,
        },
        timestamp=timestamp_zephyr_to_matrix(message.time),
    )
    
    print(f"Sent [-c {msg.cls} -i {msg.instance}] {content}")


if __name__ == '__main__':
    import os
    while True:
        # Catch zephyr exceptions at the top level
        try:
            msg: zephyr.ZNotice = zephyr.receive(True)
            if msg is not None:
                on_zephyr_message(msg)
        except OSError as e:
            renew_kerberos_tickets()
            print(f"ZEPHYR ERROR: {e}")
