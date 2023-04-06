from config import config
import sys
import matrix
import zephyr
from constants import *
import uuid

def get_unique_transaction_id():
    """
    Get a unique transaction ID for API requests

    https://spec.matrix.org/v1.6/client-server-api/#transaction-identifiers
    """
    # a simpler counter is recommended, but we'd need somewhere to store the counter
    return str(uuid.uuid4())

def extract_mxid(mxid: str):
    """
    Given an MXID, return a tuple containing the localpart
    and homeserver
    """
    array = mxid[1:].split(':')
    assert len(array) == 2, 'MXID must have one (and only one) colon'
    return tuple(array)


def get_zephyr_user(mxid: str):
    """
    Given a Matrix user, return the corresponding Zephyr user
    """
    user_localpart, user_homeserver = extract_mxid(mxid)
    
    # Local users will use the default realm (ATHENA.MIT.EDU)
    if user_homeserver == config.homeserver:
        return f'{user_localpart}@{DEFAULT_REALM}'
    
    # Otherwise, just keep the mxid unchanged, since
    # that does not mislead or let people impersonate MIT users by
    # using accounts on other homeservers (at least from our bridge,
    # coming from our hostname)
    return mxid


def get_zephyr_location(mxid: str) -> tuple[str] | bool:
    """
    Get Zephyr class and instance for the given Matrix
    room ID, or False if not found

    Behavior is currently hardcoded to parsing the format
    #z/classname/instancename (with prefix and separator in config)
    """
    # Resolve canonical ID
    if mxid.startswith('!'):
        mxid = matrix.get_room_alias(mxid)
    # Could not find canonical ID
    if mxid is None:
        return False
    
    if mxid.startswith('#' + config.zephyr_room_prefix):
        localpart, homeserver = extract_mxid(mxid)
        if homeserver != config.homeserver:
            print(f"Unknown homeserver {homeserver}, skipping", file=sys.stderr)
            return False
        array = localpart[len(config.zephyr_room_prefix):].split(config.class_instance_separator)
        if len(array) != 2:
            print(f"Room {localpart} has extra slash, skipping", file=sys.stderr)
        return tuple(array)
    else:
        print(f"Unknown zephyr triplet for {mxid}", file=sys.stderr)
        return False


def send_zephyr_message(message, cls=DEFAULT_CLASS, instance=DEFAULT_INSTANCE, opcode=DEFAULT_OPCODE, sender=None, display_name=None):
    """
    Send a Zephyr message to the given class and instance
    """
    # Set signature to sender if not given
    if display_name is None:
        display_name = sender
    
    zephyr.init()
    notice = zephyr.ZNotice(
        cls=cls,
        instance=instance,
        sender=sender,
        opcode=opcode,
        format='Config error: see http://mit.edu/df', # URL actually leads somewhere (what BarnOwl uses)
        fields=[display_name, message],
    )
    notice.send()
