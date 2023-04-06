import zephyr
import sys
from constants import *

zephyr.init()

# NOTE: this is already a singleton
subs = zephyr.Subscriptions()

# TODO: don't hardcode
subs.add(('thisclassdoesnotexist', '*', '*'))
subs.add((DEFAULT_CLASS, '*', '*'))

def strip_default_realm(user: str):
    """
    If `user` ends with ATHENA.MIT.EDU, remove it
    """
    if user.endswith(DEFAULT_REALM):
        return user[:-len(DEFAULT_REALM)-1]
    else:
        return user


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
        print(f"DM from {sender} ({display_name}) to {recipient}:\n{content}")
        return

    # TODO: actually implement Matrix sending
    # TODO: specify timestamp for Matrix
    print(f"[-c {msg.cls} -i {msg.instance}] {content}")


if __name__ == '__main__':
    while True:
        msg: zephyr.ZNotice = zephyr.receive(True)
        if msg is not None:
            on_zephyr_message(msg)